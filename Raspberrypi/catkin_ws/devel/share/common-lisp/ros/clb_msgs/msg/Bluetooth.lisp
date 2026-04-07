; Auto-generated. Do not edit!


(cl:in-package clb_msgs-msg)


;//! \htmlinclude Bluetooth.msg.html

(cl:defclass <Bluetooth> (roslisp-msg-protocol:ros-message)
  ((connect_stats
    :reader connect_stats
    :initarg :connect_stats
    :type cl:integer
    :initform 0)
   (angle_x
    :reader angle_x
    :initarg :angle_x
    :type cl:integer
    :initform 0)
   (angle_y
    :reader angle_y
    :initarg :angle_y
    :type cl:integer
    :initform 0))
)

(cl:defclass Bluetooth (<Bluetooth>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Bluetooth>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Bluetooth)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-msg:<Bluetooth> is deprecated: use clb_msgs-msg:Bluetooth instead.")))

(cl:ensure-generic-function 'connect_stats-val :lambda-list '(m))
(cl:defmethod connect_stats-val ((m <Bluetooth>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-msg:connect_stats-val is deprecated.  Use clb_msgs-msg:connect_stats instead.")
  (connect_stats m))

(cl:ensure-generic-function 'angle_x-val :lambda-list '(m))
(cl:defmethod angle_x-val ((m <Bluetooth>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-msg:angle_x-val is deprecated.  Use clb_msgs-msg:angle_x instead.")
  (angle_x m))

(cl:ensure-generic-function 'angle_y-val :lambda-list '(m))
(cl:defmethod angle_y-val ((m <Bluetooth>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-msg:angle_y-val is deprecated.  Use clb_msgs-msg:angle_y instead.")
  (angle_y m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Bluetooth>) ostream)
  "Serializes a message object of type '<Bluetooth>"
  (cl:let* ((signed (cl:slot-value msg 'connect_stats)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'angle_x)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'angle_y)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Bluetooth>) istream)
  "Deserializes a message object of type '<Bluetooth>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'connect_stats) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'angle_x) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'angle_y) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Bluetooth>)))
  "Returns string type for a message object of type '<Bluetooth>"
  "clb_msgs/Bluetooth")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Bluetooth)))
  "Returns string type for a message object of type 'Bluetooth"
  "clb_msgs/Bluetooth")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Bluetooth>)))
  "Returns md5sum for a message object of type '<Bluetooth>"
  "d231f5dc5332675e1ab8a685bdfd06a0")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Bluetooth)))
  "Returns md5sum for a message object of type 'Bluetooth"
  "d231f5dc5332675e1ab8a685bdfd06a0")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Bluetooth>)))
  "Returns full string definition for message of type '<Bluetooth>"
  (cl:format cl:nil "int32 connect_stats~%int32 angle_x~%int32 angle_y~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Bluetooth)))
  "Returns full string definition for message of type 'Bluetooth"
  (cl:format cl:nil "int32 connect_stats~%int32 angle_x~%int32 angle_y~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Bluetooth>))
  (cl:+ 0
     4
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Bluetooth>))
  "Converts a ROS message object to a list"
  (cl:list 'Bluetooth
    (cl:cons ':connect_stats (connect_stats msg))
    (cl:cons ':angle_x (angle_x msg))
    (cl:cons ':angle_y (angle_y msg))
))
