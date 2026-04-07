;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Trajectory)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Trajectory (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::TRAJECTORY")
  (make-package "CLB_MSGS::TRAJECTORY"))
(unless (find-package "CLB_MSGS::TRAJECTORYREQUEST")
  (make-package "CLB_MSGS::TRAJECTORYREQUEST"))
(unless (find-package "CLB_MSGS::TRAJECTORYRESPONSE")
  (make-package "CLB_MSGS::TRAJECTORYRESPONSE"))

(in-package "ROS")





(defclass clb_msgs::TrajectoryRequest
  :super ros::object
  :slots (_id2 _id3 _id4 _id5 _id6 _time ))

(defmethod clb_msgs::TrajectoryRequest
  (:init
   (&key
    ((:id2 __id2) 0)
    ((:id3 __id3) 0)
    ((:id4 __id4) 0)
    ((:id5 __id5) 0)
    ((:id6 __id6) 0)
    ((:time __time) 0)
    )
   (send-super :init)
   (setq _id2 (round __id2))
   (setq _id3 (round __id3))
   (setq _id4 (round __id4))
   (setq _id5 (round __id5))
   (setq _id6 (round __id6))
   (setq _time (round __time))
   self)
  (:id2
   (&optional __id2)
   (if __id2 (setq _id2 __id2)) _id2)
  (:id3
   (&optional __id3)
   (if __id3 (setq _id3 __id3)) _id3)
  (:id4
   (&optional __id4)
   (if __id4 (setq _id4 __id4)) _id4)
  (:id5
   (&optional __id5)
   (if __id5 (setq _id5 __id5)) _id5)
  (:id6
   (&optional __id6)
   (if __id6 (setq _id6 __id6)) _id6)
  (:time
   (&optional __time)
   (if __time (setq _time __time)) _time)
  (:serialization-length
   ()
   (+
    ;; int16 _id2
    2
    ;; int16 _id3
    2
    ;; int16 _id4
    2
    ;; int16 _id5
    2
    ;; int16 _id6
    2
    ;; int16 _time
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int16 _id2
       (write-word _id2 s)
     ;; int16 _id3
       (write-word _id3 s)
     ;; int16 _id4
       (write-word _id4 s)
     ;; int16 _id5
       (write-word _id5 s)
     ;; int16 _id6
       (write-word _id6 s)
     ;; int16 _time
       (write-word _time s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int16 _id2
     (setq _id2 (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _id3
     (setq _id3 (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _id4
     (setq _id4 (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _id5
     (setq _id5 (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _id6
     (setq _id6 (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _time
     (setq _time (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(defclass clb_msgs::TrajectoryResponse
  :super ros::object
  :slots ())

(defmethod clb_msgs::TrajectoryResponse
  (:init
   (&key
    )
   (send-super :init)
   self)
  (:serialization-length
   ()
   (+
    0
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;;
   self)
  )

(defclass clb_msgs::Trajectory
  :super ros::object
  :slots ())

(setf (get clb_msgs::Trajectory :md5sum-) "f982c44c4992b0945e9540dc9fc648e5")
(setf (get clb_msgs::Trajectory :datatype-) "clb_msgs/Trajectory")
(setf (get clb_msgs::Trajectory :request) clb_msgs::TrajectoryRequest)
(setf (get clb_msgs::Trajectory :response) clb_msgs::TrajectoryResponse)

(defmethod clb_msgs::TrajectoryRequest
  (:response () (instance clb_msgs::TrajectoryResponse :init)))

(setf (get clb_msgs::TrajectoryRequest :md5sum-) "f982c44c4992b0945e9540dc9fc648e5")
(setf (get clb_msgs::TrajectoryRequest :datatype-) "clb_msgs/TrajectoryRequest")
(setf (get clb_msgs::TrajectoryRequest :definition-)
      "int16 id2
int16 id3
int16 id4
int16 id5
int16 id6
int16 time


---
")

(setf (get clb_msgs::TrajectoryResponse :md5sum-) "f982c44c4992b0945e9540dc9fc648e5")
(setf (get clb_msgs::TrajectoryResponse :datatype-) "clb_msgs/TrajectoryResponse")
(setf (get clb_msgs::TrajectoryResponse :definition-)
      "int16 id2
int16 id3
int16 id4
int16 id5
int16 id6
int16 time


---
")



(provide :clb_msgs/Trajectory "f982c44c4992b0945e9540dc9fc648e5")


