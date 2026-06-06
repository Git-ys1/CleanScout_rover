#!/usr/bin/env python3

import threading
import time

import actionlib
import rospy
import yaml
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped, Quaternion
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_srvs.srv import Trigger, TriggerResponse
from tf.transformations import quaternion_from_euler


STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_CANCELLING = "cancelling"


class RouteExecutor:
    def __init__(self):
        self.routes_file = rospy.get_param("~routes_file")
        self.map_frame = rospy.get_param("~map_frame", "map")
        self.pose_topic = rospy.get_param("~pose_topic", "/amcl_pose")
        self.move_base_action = rospy.get_param("~move_base_action", "move_base")
        self.default_route_name = rospy.get_param("~default_route_name", "lab_test_2point")
        self.retry_once = bool(rospy.get_param("~retry_once", True))

        self.client = actionlib.SimpleActionClient(self.move_base_action, MoveBaseAction)
        self.latest_amcl_pose = None
        self.state_lock = threading.Lock()
        self.status = STATUS_IDLE
        self.active_route = ""
        self.current_index = -1
        self.current_point_name = ""
        self.last_result = "never_started"
        self.worker_thread = None
        self.cancel_requested = False

        rospy.Subscriber(self.pose_topic, PoseWithCovarianceStamped, self.pose_callback, queue_size=1)

        rospy.Service("start_route", Trigger, self.handle_start_route)
        rospy.Service("cancel_route", Trigger, self.handle_cancel_route)
        rospy.Service("get_route_status", Trigger, self.handle_get_route_status)

    def pose_callback(self, msg):
        self.latest_amcl_pose = msg

    def handle_start_route(self, _req):
        with self.state_lock:
            if self.status == STATUS_RUNNING:
                return TriggerResponse(success=False, message="route already running")
            self.cancel_requested = False
            self.status = STATUS_RUNNING
            self.active_route = self.default_route_name
            self.current_index = -1
            self.current_point_name = ""
            self.last_result = "starting"

        self.worker_thread = threading.Thread(target=self.run_route, args=(self.default_route_name,), daemon=True)
        self.worker_thread.start()
        return TriggerResponse(success=True, message=f"started route {self.default_route_name}")

    def handle_cancel_route(self, _req):
        with self.state_lock:
            if self.status != STATUS_RUNNING:
                return TriggerResponse(success=False, message="no running route")
            self.cancel_requested = True
            self.status = STATUS_CANCELLING
        self.client.cancel_all_goals()
        return TriggerResponse(success=True, message="cancel requested")

    def handle_get_route_status(self, _req):
        with self.state_lock:
            message = (
                f"status={self.status}; route={self.active_route or '-'}; "
                f"index={self.current_index}; point={self.current_point_name or '-'}; result={self.last_result}"
            )
            return TriggerResponse(success=True, message=message)

    def load_routes(self):
        with open(self.routes_file, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        routes = data.get("routes", {})
        if not isinstance(routes, dict):
            raise RuntimeError("routes.yaml missing top-level routes map")
        return routes

    def require_navigation_ready(self):
        if not self.client.wait_for_server(rospy.Duration(10.0)):
            raise RuntimeError("move_base action server is not available")
        if self.latest_amcl_pose is None:
            raise RuntimeError(f"{self.pose_topic} is not available")

    def build_goal(self, point):
        goal = MoveBaseGoal()
        goal.target_pose = PoseStamped()
        goal.target_pose.header.frame_id = self.map_frame
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = float(point["x"])
        goal.target_pose.pose.position.y = float(point["y"])
        q = quaternion_from_euler(0.0, 0.0, float(point["yaw"]))
        goal.target_pose.pose.orientation = Quaternion(*q)
        return goal

    def run_route(self, route_name):
        try:
            routes = self.load_routes()
            route = routes.get(route_name)
            if not route:
                raise RuntimeError(f"route not found: {route_name}")
            points = route.get("points", [])
            if not points:
                raise RuntimeError(f"route has no points: {route_name}")

            self.require_navigation_ready()

            for index, point in enumerate(points):
                with self.state_lock:
                    if self.cancel_requested:
                        self.last_result = "cancelled"
                        self.status = STATUS_IDLE
                        return
                    self.current_index = index
                    self.current_point_name = point.get("name", f"point_{index}")

                attempt_count = 2 if self.retry_once else 1
                success = False
                for attempt in range(attempt_count):
                    goal = self.build_goal(point)
                    self.client.send_goal(goal)
                    finished = self.client.wait_for_result()
                    state = self.client.get_state() if finished else GoalStatus.LOST

                    if self.cancel_requested:
                        self.client.cancel_all_goals()
                        with self.state_lock:
                            self.last_result = "cancelled"
                            self.status = STATUS_IDLE
                        return

                    if state == GoalStatus.SUCCEEDED:
                        success = True
                        with self.state_lock:
                            self.last_result = f"reached:{self.current_point_name}"
                        break

                    rospy.logwarn(
                        "route_executor failed point %s (attempt %d/%d), move_base state=%s",
                        self.current_point_name,
                        attempt + 1,
                        attempt_count,
                        state,
                    )
                    try:
                        rospy.wait_for_service("/move_base/clear_costmaps", timeout=2.0)
                    except (rospy.ROSException, rospy.ROSInterruptException):
                        pass

                if not success:
                    raise RuntimeError(f"route aborted at point {self.current_point_name}")

                pause_sec = float(point.get("pause_sec", 0.0) or 0.0)
                if pause_sec > 0.0:
                    time.sleep(pause_sec)

            with self.state_lock:
                self.status = STATUS_IDLE
                self.last_result = "finished"
                self.current_index = len(points) - 1
        except Exception as exc:
            rospy.logerr("route_executor error: %s", exc)
            with self.state_lock:
                self.status = STATUS_IDLE
                self.last_result = f"error:{exc}"


def main():
    rospy.init_node("route_executor")
    RouteExecutor()
    rospy.spin()


if __name__ == "__main__":
    main()
