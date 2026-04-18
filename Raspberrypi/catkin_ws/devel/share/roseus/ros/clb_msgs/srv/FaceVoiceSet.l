;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::FaceVoiceSet)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'FaceVoiceSet (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::FACEVOICESET")
  (make-package "CLB_MSGS::FACEVOICESET"))
(unless (find-package "CLB_MSGS::FACEVOICESETREQUEST")
  (make-package "CLB_MSGS::FACEVOICESETREQUEST"))
(unless (find-package "CLB_MSGS::FACEVOICESETRESPONSE")
  (make-package "CLB_MSGS::FACEVOICESETRESPONSE"))

(in-package "ROS")





(defclass clb_msgs::FaceVoiceSetRequest
  :super ros::object
  :slots (_voice_id ))

(defmethod clb_msgs::FaceVoiceSetRequest
  (:init
   (&key
    ((:voice_id __voice_id) 0)
    )
   (send-super :init)
   (setq _voice_id (round __voice_id))
   self)
  (:voice_id
   (&optional __voice_id)
   (if __voice_id (setq _voice_id __voice_id)) _voice_id)
  (:serialization-length
   ()
   (+
    ;; int32 _voice_id
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _voice_id
       (write-long _voice_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _voice_id
     (setq _voice_id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(defclass clb_msgs::FaceVoiceSetResponse
  :super ros::object
  :slots (_face_id _name ))

(defmethod clb_msgs::FaceVoiceSetResponse
  (:init
   (&key
    ((:face_id __face_id) nil)
    ((:name __name) "")
    )
   (send-super :init)
   (setq _face_id __face_id)
   (setq _name (string __name))
   self)
  (:face_id
   (&optional (__face_id :null))
   (if (not (eq __face_id :null)) (setq _face_id __face_id)) _face_id)
  (:name
   (&optional __name)
   (if __name (setq _name __name)) _name)
  (:serialization-length
   ()
   (+
    ;; bool _face_id
    1
    ;; string _name
    4 (length _name)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _face_id
       (if _face_id (write-byte -1 s) (write-byte 0 s))
     ;; string _name
       (write-long (length _name) s) (princ _name s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _face_id
     (setq _face_id (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass clb_msgs::FaceVoiceSet
  :super ros::object
  :slots ())

(setf (get clb_msgs::FaceVoiceSet :md5sum-) "90941b667b08b1366244be00f14ce2ac")
(setf (get clb_msgs::FaceVoiceSet :datatype-) "clb_msgs/FaceVoiceSet")
(setf (get clb_msgs::FaceVoiceSet :request) clb_msgs::FaceVoiceSetRequest)
(setf (get clb_msgs::FaceVoiceSet :response) clb_msgs::FaceVoiceSetResponse)

(defmethod clb_msgs::FaceVoiceSetRequest
  (:response () (instance clb_msgs::FaceVoiceSetResponse :init)))

(setf (get clb_msgs::FaceVoiceSetRequest :md5sum-) "90941b667b08b1366244be00f14ce2ac")
(setf (get clb_msgs::FaceVoiceSetRequest :datatype-) "clb_msgs/FaceVoiceSetRequest")
(setf (get clb_msgs::FaceVoiceSetRequest :definition-)
      "int32 voice_id
---
bool face_id
string name


")

(setf (get clb_msgs::FaceVoiceSetResponse :md5sum-) "90941b667b08b1366244be00f14ce2ac")
(setf (get clb_msgs::FaceVoiceSetResponse :datatype-) "clb_msgs/FaceVoiceSetResponse")
(setf (get clb_msgs::FaceVoiceSetResponse :definition-)
      "int32 voice_id
---
bool face_id
string name


")



(provide :clb_msgs/FaceVoiceSet "90941b667b08b1366244be00f14ce2ac")


