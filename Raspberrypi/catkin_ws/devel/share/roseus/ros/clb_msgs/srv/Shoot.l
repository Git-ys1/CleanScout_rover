;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Shoot)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Shoot (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::SHOOT")
  (make-package "CLB_MSGS::SHOOT"))
(unless (find-package "CLB_MSGS::SHOOTREQUEST")
  (make-package "CLB_MSGS::SHOOTREQUEST"))
(unless (find-package "CLB_MSGS::SHOOTRESPONSE")
  (make-package "CLB_MSGS::SHOOTRESPONSE"))

(in-package "ROS")





(defclass clb_msgs::ShootRequest
  :super ros::object
  :slots (_time ))

(defmethod clb_msgs::ShootRequest
  (:init
   (&key
    ((:time __time) 0)
    )
   (send-super :init)
   (setq _time (round __time))
   self)
  (:time
   (&optional __time)
   (if __time (setq _time __time)) _time)
  (:serialization-length
   ()
   (+
    ;; int16 _time
    2
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int16 _time
       (write-word _time s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int16 _time
     (setq _time (sys::peek buf ptr- :short)) (incf ptr- 2)
   ;;
   self)
  )

(defclass clb_msgs::ShootResponse
  :super ros::object
  :slots ())

(defmethod clb_msgs::ShootResponse
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

(defclass clb_msgs::Shoot
  :super ros::object
  :slots ())

(setf (get clb_msgs::Shoot :md5sum-) "b8e8bf26b20382c114e84bf5da39d6e4")
(setf (get clb_msgs::Shoot :datatype-) "clb_msgs/Shoot")
(setf (get clb_msgs::Shoot :request) clb_msgs::ShootRequest)
(setf (get clb_msgs::Shoot :response) clb_msgs::ShootResponse)

(defmethod clb_msgs::ShootRequest
  (:response () (instance clb_msgs::ShootResponse :init)))

(setf (get clb_msgs::ShootRequest :md5sum-) "b8e8bf26b20382c114e84bf5da39d6e4")
(setf (get clb_msgs::ShootRequest :datatype-) "clb_msgs/ShootRequest")
(setf (get clb_msgs::ShootRequest :definition-)
      "int16 time

---
")

(setf (get clb_msgs::ShootResponse :md5sum-) "b8e8bf26b20382c114e84bf5da39d6e4")
(setf (get clb_msgs::ShootResponse :datatype-) "clb_msgs/ShootResponse")
(setf (get clb_msgs::ShootResponse :definition-)
      "int16 time

---
")



(provide :clb_msgs/Shoot "b8e8bf26b20382c114e84bf5da39d6e4")


