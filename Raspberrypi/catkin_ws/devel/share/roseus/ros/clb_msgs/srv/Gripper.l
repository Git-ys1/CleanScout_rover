;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Gripper)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Gripper (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::GRIPPER")
  (make-package "CLB_MSGS::GRIPPER"))
(unless (find-package "CLB_MSGS::GRIPPERREQUEST")
  (make-package "CLB_MSGS::GRIPPERREQUEST"))
(unless (find-package "CLB_MSGS::GRIPPERRESPONSE")
  (make-package "CLB_MSGS::GRIPPERRESPONSE"))

(in-package "ROS")





(defclass clb_msgs::GripperRequest
  :super ros::object
  :slots (_step _time ))

(defmethod clb_msgs::GripperRequest
  (:init
   (&key
    ((:step __step) 0)
    ((:time __time) 0)
    )
   (send-super :init)
   (setq _step (round __step))
   (setq _time (round __time))
   self)
  (:step
   (&optional __step)
   (if __step (setq _step __step)) _step)
  (:time
   (&optional __time)
   (if __time (setq _time __time)) _time)
  (:serialization-length
   ()
   (+
    ;; int16 _step
    2
    ;; int16 _time
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int16 _step
       (write-word _step s)
     ;; int16 _time
       (write-word _time s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int16 _step
     (setq _step (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;; int16 _time
     (setq _time (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(defclass clb_msgs::GripperResponse
  :super ros::object
  :slots ())

(defmethod clb_msgs::GripperResponse
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

(defclass clb_msgs::Gripper
  :super ros::object
  :slots ())

(setf (get clb_msgs::Gripper :md5sum-) "e27b20d61c16bcd76ef982854742171b")
(setf (get clb_msgs::Gripper :datatype-) "clb_msgs/Gripper")
(setf (get clb_msgs::Gripper :request) clb_msgs::GripperRequest)
(setf (get clb_msgs::Gripper :response) clb_msgs::GripperResponse)

(defmethod clb_msgs::GripperRequest
  (:response () (instance clb_msgs::GripperResponse :init)))

(setf (get clb_msgs::GripperRequest :md5sum-) "e27b20d61c16bcd76ef982854742171b")
(setf (get clb_msgs::GripperRequest :datatype-) "clb_msgs/GripperRequest")
(setf (get clb_msgs::GripperRequest :definition-)
      "int16 step
int16 time

---
")

(setf (get clb_msgs::GripperResponse :md5sum-) "e27b20d61c16bcd76ef982854742171b")
(setf (get clb_msgs::GripperResponse :datatype-) "clb_msgs/GripperResponse")
(setf (get clb_msgs::GripperResponse :definition-)
      "int16 step
int16 time

---
")



(provide :clb_msgs/Gripper "e27b20d61c16bcd76ef982854742171b")


