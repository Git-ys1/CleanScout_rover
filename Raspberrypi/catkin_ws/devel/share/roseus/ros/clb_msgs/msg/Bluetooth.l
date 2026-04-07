;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Bluetooth)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Bluetooth (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::BLUETOOTH")
  (make-package "CLB_MSGS::BLUETOOTH"))

(in-package "ROS")
;;//! \htmlinclude Bluetooth.msg.html


(defclass clb_msgs::Bluetooth
  :super ros::object
  :slots (_connect_stats _angle_x _angle_y ))

(defmethod clb_msgs::Bluetooth
  (:init
   (&key
    ((:connect_stats __connect_stats) 0)
    ((:angle_x __angle_x) 0)
    ((:angle_y __angle_y) 0)
    )
   (send-super :init)
   (setq _connect_stats (round __connect_stats))
   (setq _angle_x (round __angle_x))
   (setq _angle_y (round __angle_y))
   self)
  (:connect_stats
   (&optional __connect_stats)
   (if __connect_stats (setq _connect_stats __connect_stats)) _connect_stats)
  (:angle_x
   (&optional __angle_x)
   (if __angle_x (setq _angle_x __angle_x)) _angle_x)
  (:angle_y
   (&optional __angle_y)
   (if __angle_y (setq _angle_y __angle_y)) _angle_y)
  (:serialization-length
   ()
   (+
    ;; int32 _connect_stats
    4
    ;; int32 _angle_x
    4
    ;; int32 _angle_y
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _connect_stats
       (write-long _connect_stats s)
     ;; int32 _angle_x
       (write-long _angle_x s)
     ;; int32 _angle_y
       (write-long _angle_y s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _connect_stats
     (setq _connect_stats (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32 _angle_x
     (setq _angle_x (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; int32 _angle_y
     (setq _angle_y (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get clb_msgs::Bluetooth :md5sum-) "d231f5dc5332675e1ab8a685bdfd06a0")
(setf (get clb_msgs::Bluetooth :datatype-) "clb_msgs/Bluetooth")
(setf (get clb_msgs::Bluetooth :definition-)
      "int32 connect_stats
int32 angle_x
int32 angle_y

")



(provide :clb_msgs/Bluetooth "d231f5dc5332675e1ab8a685bdfd06a0")


