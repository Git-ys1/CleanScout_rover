;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::RobotVoiceCtrl)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'RobotVoiceCtrl (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::ROBOTVOICECTRL")
  (make-package "CLB_MSGS::ROBOTVOICECTRL"))
(unless (find-package "CLB_MSGS::ROBOTVOICECTRLREQUEST")
  (make-package "CLB_MSGS::ROBOTVOICECTRLREQUEST"))
(unless (find-package "CLB_MSGS::ROBOTVOICECTRLRESPONSE")
  (make-package "CLB_MSGS::ROBOTVOICECTRLRESPONSE"))

(in-package "ROS")





(defclass clb_msgs::RobotVoiceCtrlRequest
  :super ros::object
  :slots (_ctrl_id ))

(defmethod clb_msgs::RobotVoiceCtrlRequest
  (:init
   (&key
    ((:ctrl_id __ctrl_id) 0)
    )
   (send-super :init)
   (setq _ctrl_id (round __ctrl_id))
   self)
  (:ctrl_id
   (&optional __ctrl_id)
   (if __ctrl_id (setq _ctrl_id __ctrl_id)) _ctrl_id)
  (:serialization-length
   ()
   (+
    ;; int32 _ctrl_id
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _ctrl_id
       (write-long _ctrl_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _ctrl_id
     (setq _ctrl_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(defclass clb_msgs::RobotVoiceCtrlResponse
  :super ros::object
  :slots (_face_id ))

(defmethod clb_msgs::RobotVoiceCtrlResponse
  (:init
   (&key
    ((:face_id __face_id) nil)
    )
   (send-super :init)
   (setq _face_id __face_id)
   self)
  (:face_id
   (&optional (__face_id :null))
   (if (not (eq __face_id :null)) (setq _face_id __face_id)) _face_id)
  (:serialization-length
   ()
   (+
    ;; bool _face_id
    1
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _face_id
       (if _face_id (write-byte -1 s) (write-byte 0 s))
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _face_id
     (setq _face_id (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;;
   self)
  )

(defclass clb_msgs::RobotVoiceCtrl
  :super ros::object
  :slots ())

(setf (get clb_msgs::RobotVoiceCtrl :md5sum-) "99d7cbf41203ea07c76e17ef42eda7f5")
(setf (get clb_msgs::RobotVoiceCtrl :datatype-) "clb_msgs/RobotVoiceCtrl")
(setf (get clb_msgs::RobotVoiceCtrl :request) clb_msgs::RobotVoiceCtrlRequest)
(setf (get clb_msgs::RobotVoiceCtrl :response) clb_msgs::RobotVoiceCtrlResponse)

(defmethod clb_msgs::RobotVoiceCtrlRequest
  (:response () (instance clb_msgs::RobotVoiceCtrlResponse :init)))

(setf (get clb_msgs::RobotVoiceCtrlRequest :md5sum-) "99d7cbf41203ea07c76e17ef42eda7f5")
(setf (get clb_msgs::RobotVoiceCtrlRequest :datatype-) "clb_msgs/RobotVoiceCtrlRequest")
(setf (get clb_msgs::RobotVoiceCtrlRequest :definition-)
      "int32 ctrl_id
---
bool face_id


")

(setf (get clb_msgs::RobotVoiceCtrlResponse :md5sum-) "99d7cbf41203ea07c76e17ef42eda7f5")
(setf (get clb_msgs::RobotVoiceCtrlResponse :datatype-) "clb_msgs/RobotVoiceCtrlResponse")
(setf (get clb_msgs::RobotVoiceCtrlResponse :definition-)
      "int32 ctrl_id
---
bool face_id


")



(provide :clb_msgs/RobotVoiceCtrl "99d7cbf41203ea07c76e17ef42eda7f5")


