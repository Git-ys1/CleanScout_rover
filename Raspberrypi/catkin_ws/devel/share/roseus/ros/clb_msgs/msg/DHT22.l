;; Auto-generated. Do not edit!


(when (boundp 'clb_msgs::DHT22)
  (if (not (find-package "CLB_MSGS"))
    (make-package "CLB_MSGS"))
  (shadow 'DHT22 (find-package "CLB_MSGS")))
(unless (find-package "CLB_MSGS::DHT22")
  (make-package "CLB_MSGS::DHT22"))

(in-package "ROS")
;;//! \htmlinclude DHT22.msg.html


(defclass clb_msgs::DHT22
  :super ros::object
  :slots (_Temperature _Humidity ))

(defmethod clb_msgs::DHT22
  (:init
   (&key
    ((:Temperature __Temperature) 0.0)
    ((:Humidity __Humidity) 0.0)
    )
   (send-super :init)
   (setq _Temperature (float __Temperature))
   (setq _Humidity (float __Humidity))
   self)
  (:Temperature
   (&optional __Temperature)
   (if __Temperature (setq _Temperature __Temperature)) _Temperature)
  (:Humidity
   (&optional __Humidity)
   (if __Humidity (setq _Humidity __Humidity)) _Humidity)
  (:serialization-length
   ()
   (+
    ;; float32 _Temperature
    4
    ;; float32 _Humidity
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32 _Temperature
       (sys::poke _Temperature (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _Humidity
       (sys::poke _Humidity (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32 _Temperature
     (setq _Temperature (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _Humidity
     (setq _Humidity (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get clb_msgs::DHT22 :md5sum-) "5444ed9cc78ceaace5058c55fe815905")
(setf (get clb_msgs::DHT22 :datatype-) "clb_msgs/DHT22")
(setf (get clb_msgs::DHT22 :definition-)
      "float32 Temperature
float32 Humidity

")



(provide :clb_msgs/DHT22 "5444ed9cc78ceaace5058c55fe815905")


