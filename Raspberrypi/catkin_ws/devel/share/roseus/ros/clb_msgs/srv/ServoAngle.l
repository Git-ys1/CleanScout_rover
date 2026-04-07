;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::ServoAngle)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'ServoAngle (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::SERVOANGLE")
  (make-package "CLB_MSGS::SERVOANGLE"))
(unless (find-package "CLB_MSGS::SERVOANGLEREQUEST")
  (make-package "CLB_MSGS::SERVOANGLEREQUEST"))
(unless (find-package "CLB_MSGS::SERVOANGLERESPONSE")
  (make-package "CLB_MSGS::SERVOANGLERESPONSE"))

(in-package "ROS")





(defclass clb_msgs::ServoAngleRequest
  :super ros::object
  :slots (_Servo1 _Servo2 ))

(defmethod clb_msgs::ServoAngleRequest
  (:init
   (&key
    ((:Servo1 __Servo1) 0)
    ((:Servo2 __Servo2) 0)
    )
   (send-super :init)
   (setq _Servo1 (round __Servo1))
   (setq _Servo2 (round __Servo2))
   self)
  (:Servo1
   (&optional __Servo1)
   (if __Servo1 (setq _Servo1 __Servo1)) _Servo1)
  (:Servo2
   (&optional __Servo2)
   (if __Servo2 (setq _Servo2 __Servo2)) _Servo2)
  (:serialization-length
   ()
   (+
    ;; int32 _Servo1
    4
    ;; int32 _Servo2
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _Servo1
       (write-long _Servo1 s)
     ;; int32 _Servo2
       (write-long _Servo2 s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _Servo1
     (setq _Servo1 (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32 _Servo2
     (setq _Servo2 (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(defclass clb_msgs::ServoAngleResponse
  :super ros::object
  :slots ())

(defmethod clb_msgs::ServoAngleResponse
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

(defclass clb_msgs::ServoAngle
  :super ros::object
  :slots ())

(setf (get clb_msgs::ServoAngle :md5sum-) "b1d39e7bb90536edb373b61068d04284")
(setf (get clb_msgs::ServoAngle :datatype-) "clb_msgs/ServoAngle")
(setf (get clb_msgs::ServoAngle :request) clb_msgs::ServoAngleRequest)
(setf (get clb_msgs::ServoAngle :response) clb_msgs::ServoAngleResponse)

(defmethod clb_msgs::ServoAngleRequest
  (:response () (instance clb_msgs::ServoAngleResponse :init)))

(setf (get clb_msgs::ServoAngleRequest :md5sum-) "b1d39e7bb90536edb373b61068d04284")
(setf (get clb_msgs::ServoAngleRequest :datatype-) "clb_msgs/ServoAngleRequest")
(setf (get clb_msgs::ServoAngleRequest :definition-)
      "int32 Servo1
int32 Servo2

---
")

(setf (get clb_msgs::ServoAngleResponse :md5sum-) "b1d39e7bb90536edb373b61068d04284")
(setf (get clb_msgs::ServoAngleResponse :datatype-) "clb_msgs/ServoAngleResponse")
(setf (get clb_msgs::ServoAngleResponse :definition-)
      "int32 Servo1
int32 Servo2

---
")



(provide :clb_msgs/ServoAngle "b1d39e7bb90536edb373b61068d04284")


