;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Pose)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Pose (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::POSE")
  (make-package "CLB_MSGS::POSE"))
(unless (find-package "CLB_MSGS::POSEREQUEST")
  (make-package "CLB_MSGS::POSEREQUEST"))
(unless (find-package "CLB_MSGS::POSERESPONSE")
  (make-package "CLB_MSGS::POSERESPONSE"))

(in-package "ROS")





(defclass clb_msgs::PoseRequest
  :super ros::object
  :slots (_x _y _z _rtoary _time ))

(defmethod clb_msgs::PoseRequest
  (:init
   (&key
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:z __z) 0.0)
    ((:rtoary __rtoary) 0.0)
    ((:time __time) 0)
    )
   (send-super :init)
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _z (float __z))
   (setq _rtoary (float __rtoary))
   (setq _time (round __time))
   self)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:z
   (&optional __z)
   (if __z (setq _z __z)) _z)
  (:rtoary
   (&optional __rtoary)
   (if __rtoary (setq _rtoary __rtoary)) _rtoary)
  (:time
   (&optional __time)
   (if __time (setq _time __time)) _time)
  (:serialization-length
   ()
   (+
    ;; float32 _x
    4
    ;; float32 _y
    4
    ;; float32 _z
    4
    ;; float32 _rtoary
    4
    ;; int16 _time
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32 _x
       (sys::poke _x (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _y
       (sys::poke _y (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _z
       (sys::poke _z (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _rtoary
       (sys::poke _rtoary (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; int16 _time
       (write-word _time s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32 _x
     (setq _x (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _y
     (setq _y (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _z
     (setq _z (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _rtoary
     (setq _rtoary (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; int16 _time
     (setq _time (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(defclass clb_msgs::PoseResponse
  :super ros::object
  :slots ())

(defmethod clb_msgs::PoseResponse
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

(defclass clb_msgs::Pose
  :super ros::object
  :slots ())

(setf (get clb_msgs::Pose :md5sum-) "c4258fd17a5d5267d5a22ad00faa1382")
(setf (get clb_msgs::Pose :datatype-) "clb_msgs/Pose")
(setf (get clb_msgs::Pose :request) clb_msgs::PoseRequest)
(setf (get clb_msgs::Pose :response) clb_msgs::PoseResponse)

(defmethod clb_msgs::PoseRequest
  (:response () (instance clb_msgs::PoseResponse :init)))

(setf (get clb_msgs::PoseRequest :md5sum-) "c4258fd17a5d5267d5a22ad00faa1382")
(setf (get clb_msgs::PoseRequest :datatype-) "clb_msgs/PoseRequest")
(setf (get clb_msgs::PoseRequest :definition-)
      "float32 x
float32 y
float32 z
float32 rtoary
int16 time

---
")

(setf (get clb_msgs::PoseResponse :md5sum-) "c4258fd17a5d5267d5a22ad00faa1382")
(setf (get clb_msgs::PoseResponse :datatype-) "clb_msgs/PoseResponse")
(setf (get clb_msgs::PoseResponse :definition-)
      "float32 x
float32 y
float32 z
float32 rtoary
int16 time

---
")



(provide :clb_msgs/Pose "c4258fd17a5d5267d5a22ad00faa1382")


