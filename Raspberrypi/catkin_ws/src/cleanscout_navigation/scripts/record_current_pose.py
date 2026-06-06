#!/usr/bin/env python3

import math
import os

import rospy
import yaml
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf.transformations import euler_from_quaternion


def ensure_parent(path):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


class CurrentPoseRecorder:
    def __init__(self):
        self.pose_topic = rospy.get_param("~pose_topic", "/amcl_pose")
        self.routes_file = rospy.get_param("~routes_file")
        self.route_name = rospy.get_param("~route_name", "lab_test_2point")
        self.point_name = rospy.get_param("~point_name")
        self.pause_sec = float(rospy.get_param("~pause_sec", 0.0))
        self.tolerance_xy = float(rospy.get_param("~tolerance_xy", 0.20))
        self.tolerance_yaw = float(rospy.get_param("~tolerance_yaw", 0.30))

        self.latest_pose = None
        rospy.Subscriber(self.pose_topic, PoseWithCovarianceStamped, self.pose_callback, queue_size=1)

    def pose_callback(self, msg):
        self.latest_pose = msg

    def wait_for_pose(self):
        timeout_sec = 5.0
        deadline = rospy.Time.now().to_sec() + timeout_sec
        rate = rospy.Rate(10)
        while not rospy.is_shutdown() and self.latest_pose is None:
            if rospy.Time.now().to_sec() > deadline:
                raise RuntimeError(f"Timed out waiting for {self.pose_topic}")
            rate.sleep()

    def save(self):
        self.wait_for_pose()
        msg = self.latest_pose
        pose = msg.pose.pose
        quat = pose.orientation
        yaw = euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])[2]

        ensure_parent(self.routes_file)
        data = {"routes": {}}
        if os.path.isfile(self.routes_file):
            with open(self.routes_file, "r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
                if isinstance(loaded, dict):
                    data = loaded
                    data.setdefault("routes", {})

        route = data["routes"].setdefault(self.route_name, {
            "description": f"Recorded route {self.route_name}",
            "map": "",
            "points": [],
        })
        route.setdefault("points", [])

        point = {
            "name": self.point_name,
            "x": round(pose.position.x, 3),
            "y": round(pose.position.y, 3),
            "yaw": round(yaw, 3),
            "tolerance_xy": round(self.tolerance_xy, 3),
            "tolerance_yaw": round(self.tolerance_yaw, 3),
            "pause_sec": round(self.pause_sec, 3),
        }

        existing_points = route["points"]
        replaced = False
        for index, item in enumerate(existing_points):
            if item.get("name") == self.point_name:
                existing_points[index] = point
                replaced = True
                break
        if not replaced:
            existing_points.append(point)

        with open(self.routes_file, "w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)

        rospy.loginfo(
            "Saved route point %s to %s (%s: x=%.3f y=%.3f yaw=%.3f deg)",
            self.point_name,
            self.routes_file,
            self.route_name,
            point["x"],
            point["y"],
            math.degrees(point["yaw"]),
        )


def main():
    rospy.init_node("record_current_pose")
    recorder = CurrentPoseRecorder()
    recorder.save()


if __name__ == "__main__":
    main()
