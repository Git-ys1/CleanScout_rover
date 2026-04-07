; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude Gripper-request.msg.html

(cl:defclass <Gripper-request> (roslisp-msg-protocol:ros-message)
  ((step
    :reader step
    :initarg :step
    :type cl:fixnum
    :initform 0)
   (time
    :reader time
    :initarg :time
    :type cl:fixnum
    :initform 0))
)

(cl:defclass Gripper-request (<Gripper-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Gripper-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Gripper-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Gripper-request> is deprecated: use clb_msgs-srv:Gripper-request instead.")))

(cl:ensure-generic-function 'step-val :lambda-list '(m))
(cl:defmethod step-val ((m <Gripper-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:step-val is deprecated.  Use clb_msgs-srv:step instead.")
  (step m))

(cl:ensure-generic-function 'time-val :lambda-list '(m))
(cl:defmethod time-val ((m <Gripper-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:time-val is deprecated.  Use clb_msgs-srv:time instead.")
  (time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Gripper-request>) ostream)
  "Serializes a message object of type '<Gripper-request>"
  (cl:let* ((signed (cl:slot-value msg 'step)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'time)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Gripper-request>) istream)
  "Deserializes a message object of type '<Gripper-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'step) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'time) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Gripper-request>)))
  "Returns string type for a service object of type '<Gripper-request>"
  "clb_msgs/GripperRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Gripper-request)))
  "Returns string type for a service object of type 'Gripper-request"
  "clb_msgs/GripperRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Gripper-request>)))
  "Returns md5sum for a message object of type '<Gripper-request>"
  "e27b20d61c16bcd76ef982854742171b")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Gripper-request)))
  "Returns md5sum for a message object of type 'Gripper-request"
  "e27b20d61c16bcd76ef982854742171b")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Gripper-request>)))
  "Returns full string definition for message of type '<Gripper-request>"
  (cl:format cl:nil "int16 step~%int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Gripper-request)))
  "Returns full string definition for message of type 'Gripper-request"
  (cl:format cl:nil "int16 step~%int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Gripper-request>))
  (cl:+ 0
     2
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Gripper-request>))
  "Converts a ROS message object to a list"
  (cl:list 'Gripper-request
    (cl:cons ':step (step msg))
    (cl:cons ':time (time msg))
))
;//! \htmlinclude Gripper-response.msg.html

(cl:defclass <Gripper-response> (roslisp-msg-protocol:ros-message)
  ()
)

(cl:defclass Gripper-response (<Gripper-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Gripper-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Gripper-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Gripper-response> is deprecated: use clb_msgs-srv:Gripper-response instead.")))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Gripper-response>) ostream)
  "Serializes a message object of type '<Gripper-response>"
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Gripper-response>) istream)
  "Deserializes a message object of type '<Gripper-response>"
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Gripper-response>)))
  "Returns string type for a service object of type '<Gripper-response>"
  "clb_msgs/GripperResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Gripper-response)))
  "Returns string type for a service object of type 'Gripper-response"
  "clb_msgs/GripperResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Gripper-response>)))
  "Returns md5sum for a message object of type '<Gripper-response>"
  "e27b20d61c16bcd76ef982854742171b")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Gripper-response)))
  "Returns md5sum for a message object of type 'Gripper-response"
  "e27b20d61c16bcd76ef982854742171b")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Gripper-response>)))
  "Returns full string definition for message of type '<Gripper-response>"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Gripper-response)))
  "Returns full string definition for message of type 'Gripper-response"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Gripper-response>))
  (cl:+ 0
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Gripper-response>))
  "Converts a ROS message object to a list"
  (cl:list 'Gripper-response
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'Gripper)))
  'Gripper-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'Gripper)))
  'Gripper-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Gripper)))
  "Returns string type for a service object of type '<Gripper>"
  "clb_msgs/Gripper")