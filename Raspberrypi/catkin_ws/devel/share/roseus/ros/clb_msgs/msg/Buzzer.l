;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::Buzzer)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'Buzzer (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::BUZZER")
  (make-package "CLB_MSGS::BUZZER"))

(in-package "ROS")
;;//! \htmlinclude Buzzer.msg.html


(defclass clb_msgs::Buzzer
  :super ros::object
  :slots (_BUZZER1 ))

(defmethod clb_msgs::Buzzer
  (:init
   (&key
    ((:BUZZER1 __BUZZER1) 0)
    )
   (send-super :init)
   (setq _BUZZER1 (round __BUZZER1))
   self)
  (:BUZZER1
   (&optional __BUZZER1)
   (if __BUZZER1 (setq _BUZZER1 __BUZZER1)) _BUZZER1)
  (:serialization-length
   ()
   (+
    ;; int32 _BUZZER1
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _BUZZER1
       (write-long _BUZZER1 s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _BUZZER1
     (setq _BUZZER1 (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get clb_msgs::Buzzer :md5sum-) "961d0bf227fa8152deae5f5d68ec086e")
(setf (get clb_msgs::Buzzer :datatype-) "clb_msgs/Buzzer")
(setf (get clb_msgs::Buzzer :definition-)
      "int32 BUZZER1

")



(provide :clb_msgs/Buzzer "961d0bf227fa8152deae5f5d68ec086e")


