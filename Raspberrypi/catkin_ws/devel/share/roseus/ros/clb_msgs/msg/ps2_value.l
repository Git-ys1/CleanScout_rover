;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::ps2_value)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'ps2_value (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::PS2_VALUE")
  (make-package "CLB_MSGS::PS2_VALUE"))

(in-package "ROS")
;;//! \htmlinclude ps2_value.msg.html


(defclass clb_msgs::ps2_value
  :super ros::object
  :slots (_data ))

(defmethod clb_msgs::ps2_value
  (:init
   (&key
    ((:data __data) (make-array 10 :initial-element 0 :element-type :char))
    )
   (send-super :init)
   (setq _data __data)
   self)
  (:data
   (&optional __data)
   (if __data (setq _data __data)) _data)
  (:serialization-length
   ()
   (+
    ;; uint8[10] _data
    (* 1    10)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; uint8[10] _data
     (princ _data s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; uint8[10] _data
   (setq _data (make-array 10 :element-type :char))
   (replace _data buf :start2 ptr-) (incf ptr- 10)
   ;;
   self)
  )

(setf (get clb_msgs::ps2_value :md5sum-) "0c05a05733f13fb160c661ca1798fdba")
(setf (get clb_msgs::ps2_value :datatype-) "clb_msgs/ps2_value")
(setf (get clb_msgs::ps2_value :definition-)
      "uint8[10] data

")



(provide :clb_msgs/ps2_value "0c05a05733f13fb160c661ca1798fdba")


