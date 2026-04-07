; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude Shoot-request.msg.html

(cl:defclass <Shoot-request> (roslisp-msg-protocol:ros-message)
  ((time
    :reader time
    :initarg :time
    :type cl:fixnum
    :initform 0))
)

(cl:defclass Shoot-request (<Shoot-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Shoot-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Shoot-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Shoot-request> is deprecated: use clb_msgs-srv:Shoot-request instead.")))

(cl:ensure-generic-function 'time-val :lambda-list '(m))
(cl:defmethod time-val ((m <Shoot-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:time-val is deprecated.  Use clb_msgs-srv:time instead.")
  (time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Shoot-request>) ostream)
  "Serializes a message object of type '<Shoot-request>"
  (cl:let* ((signed (cl:slot-value msg 'time)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Shoot-request>) istream)
  "Deserializes a message object of type '<Shoot-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'time) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Shoot-request>)))
  "Returns string type for a service object of type '<Shoot-request>"
  "clb_msgs/ShootRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Shoot-request)))
  "Returns string type for a service object of type 'Shoot-request"
  "clb_msgs/ShootRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Shoot-request>)))
  "Returns md5sum for a message object of type '<Shoot-request>"
  "b8e8bf26b20382c114e84bf5da39d6e4")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Shoot-request)))
  "Returns md5sum for a message object of type 'Shoot-request"
  "b8e8bf26b20382c114e84bf5da39d6e4")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Shoot-request>)))
  "Returns full string definition for message of type '<Shoot-request>"
  (cl:format cl:nil "int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Shoot-request)))
  "Returns full string definition for message of type 'Shoot-request"
  (cl:format cl:nil "int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Shoot-request>))
  (cl:+ 0
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Shoot-request>))
  "Converts a ROS message object to a list"
  (cl:list 'Shoot-request
    (cl:cons ':time (time msg))
))
;//! \htmlinclude Shoot-response.msg.html

(cl:defclass <Shoot-response> (roslisp-msg-protocol:ros-message)
  ()
)

(cl:defclass Shoot-response (<Shoot-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Shoot-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Shoot-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Shoot-response> is deprecated: use clb_msgs-srv:Shoot-response instead.")))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Shoot-response>) ostream)
  "Serializes a message object of type '<Shoot-response>"
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Shoot-response>) istream)
  "Deserializes a message object of type '<Shoot-response>"
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Shoot-response>)))
  "Returns string type for a service object of type '<Shoot-response>"
  "clb_msgs/ShootResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Shoot-response)))
  "Returns string type for a service object of type 'Shoot-response"
  "clb_msgs/ShootResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Shoot-response>)))
  "Returns md5sum for a message object of type '<Shoot-response>"
  "b8e8bf26b20382c114e84bf5da39d6e4")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Shoot-response)))
  "Returns md5sum for a message object of type 'Shoot-response"
  "b8e8bf26b20382c114e84bf5da39d6e4")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Shoot-response>)))
  "Returns full string definition for message of type '<Shoot-response>"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Shoot-response)))
  "Returns full string definition for message of type 'Shoot-response"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Shoot-response>))
  (cl:+ 0
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Shoot-response>))
  "Converts a ROS message object to a list"
  (cl:list 'Shoot-response
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'Shoot)))
  'Shoot-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'Shoot)))
  'Shoot-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Shoot)))
  "Returns string type for a service object of type '<Shoot>"
  "clb_msgs/Shoot")