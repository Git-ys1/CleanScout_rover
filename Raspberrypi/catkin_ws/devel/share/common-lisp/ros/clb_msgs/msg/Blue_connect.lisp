; Auto-generated. Do not edit!


(cl:in-package clb_msgs-msg)


;//! \htmlinclude Blue_connect.msg.html

(cl:defclass <Blue_connect> (roslisp-msg-protocol:ros-message)
  ((connect_stats
    :reader connect_stats
    :initarg :connect_stats
    :type cl:integer
    :initform 0))
)

(cl:defclass Blue_connect (<Blue_connect>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Blue_connect>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Blue_connect)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-msg:<Blue_connect> is deprecated: use clb_msgs-msg:Blue_connect instead.")))

(cl:ensure-generic-function 'connect_stats-val :lambda-list '(m))
(cl:defmethod connect_stats-val ((m <Blue_connect>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-msg:connect_stats-val is deprecated.  Use clb_msgs-msg:connect_stats instead.")
  (connect_stats m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Blue_connect>) ostream)
  "Serializes a message object of type '<Blue_connect>"
  (cl:let* ((signed (cl:slot-value msg 'connect_stats)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Blue_connect>) istream)
  "Deserializes a message object of type '<Blue_connect>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'connect_stats) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Blue_connect>)))
  "Returns string type for a message object of type '<Blue_connect>"
  "clb_msgs/Blue_connect")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Blue_connect)))
  "Returns string type for a message object of type 'Blue_connect"
  "clb_msgs/Blue_connect")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Blue_connect>)))
  "Returns md5sum for a message object of type '<Blue_connect>"
  "689b4c4cbf04148501838010cd8ac299")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Blue_connect)))
  "Returns md5sum for a message object of type 'Blue_connect"
  "689b4c4cbf04148501838010cd8ac299")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Blue_connect>)))
  "Returns full string definition for message of type '<Blue_connect>"
  (cl:format cl:nil "int32 connect_stats~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Blue_connect)))
  "Returns full string definition for message of type 'Blue_connect"
  (cl:format cl:nil "int32 connect_stats~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Blue_connect>))
  (cl:+ 0
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Blue_connect>))
  "Converts a ROS message object to a list"
  (cl:list 'Blue_connect
    (cl:cons ':connect_stats (connect_stats msg))
))
