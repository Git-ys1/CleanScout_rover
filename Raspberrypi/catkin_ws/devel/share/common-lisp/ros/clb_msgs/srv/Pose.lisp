; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude Pose-request.msg.html

(cl:defclass <Pose-request> (roslisp-msg-protocol:ros-message)
  ((x
    :reader x
    :initarg :x
    :type cl:float
    :initform 0.0)
   (y
    :reader y
    :initarg :y
    :type cl:float
    :initform 0.0)
   (z
    :reader z
    :initarg :z
    :type cl:float
    :initform 0.0)
   (rtoary
    :reader rtoary
    :initarg :rtoary
    :type cl:float
    :initform 0.0)
   (time
    :reader time
    :initarg :time
    :type cl:fixnum
    :initform 0))
)

(cl:defclass Pose-request (<Pose-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Pose-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Pose-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Pose-request> is deprecated: use clb_msgs-srv:Pose-request instead.")))

(cl:ensure-generic-function 'x-val :lambda-list '(m))
(cl:defmethod x-val ((m <Pose-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:x-val is deprecated.  Use clb_msgs-srv:x instead.")
  (x m))

(cl:ensure-generic-function 'y-val :lambda-list '(m))
(cl:defmethod y-val ((m <Pose-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:y-val is deprecated.  Use clb_msgs-srv:y instead.")
  (y m))

(cl:ensure-generic-function 'z-val :lambda-list '(m))
(cl:defmethod z-val ((m <Pose-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:z-val is deprecated.  Use clb_msgs-srv:z instead.")
  (z m))

(cl:ensure-generic-function 'rtoary-val :lambda-list '(m))
(cl:defmethod rtoary-val ((m <Pose-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:rtoary-val is deprecated.  Use clb_msgs-srv:rtoary instead.")
  (rtoary m))

(cl:ensure-generic-function 'time-val :lambda-list '(m))
(cl:defmethod time-val ((m <Pose-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:time-val is deprecated.  Use clb_msgs-srv:time instead.")
  (time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Pose-request>) ostream)
  "Serializes a message object of type '<Pose-request>"
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'x))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'y))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'z))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'rtoary))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let* ((signed (cl:slot-value msg 'time)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Pose-request>) istream)
  "Deserializes a message object of type '<Pose-request>"
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'x) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'y) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'z) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'rtoary) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'time) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Pose-request>)))
  "Returns string type for a service object of type '<Pose-request>"
  "clb_msgs/PoseRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Pose-request)))
  "Returns string type for a service object of type 'Pose-request"
  "clb_msgs/PoseRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Pose-request>)))
  "Returns md5sum for a message object of type '<Pose-request>"
  "c4258fd17a5d5267d5a22ad00faa1382")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Pose-request)))
  "Returns md5sum for a message object of type 'Pose-request"
  "c4258fd17a5d5267d5a22ad00faa1382")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Pose-request>)))
  "Returns full string definition for message of type '<Pose-request>"
  (cl:format cl:nil "float32 x~%float32 y~%float32 z~%float32 rtoary~%int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Pose-request)))
  "Returns full string definition for message of type 'Pose-request"
  (cl:format cl:nil "float32 x~%float32 y~%float32 z~%float32 rtoary~%int16 time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Pose-request>))
  (cl:+ 0
     4
     4
     4
     4
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Pose-request>))
  "Converts a ROS message object to a list"
  (cl:list 'Pose-request
    (cl:cons ':x (x msg))
    (cl:cons ':y (y msg))
    (cl:cons ':z (z msg))
    (cl:cons ':rtoary (rtoary msg))
    (cl:cons ':time (time msg))
))
;//! \htmlinclude Pose-response.msg.html

(cl:defclass <Pose-response> (roslisp-msg-protocol:ros-message)
  ()
)

(cl:defclass Pose-response (<Pose-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Pose-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Pose-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Pose-response> is deprecated: use clb_msgs-srv:Pose-response instead.")))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Pose-response>) ostream)
  "Serializes a message object of type '<Pose-response>"
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Pose-response>) istream)
  "Deserializes a message object of type '<Pose-response>"
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Pose-response>)))
  "Returns string type for a service object of type '<Pose-response>"
  "clb_msgs/PoseResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Pose-response)))
  "Returns string type for a service object of type 'Pose-response"
  "clb_msgs/PoseResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Pose-response>)))
  "Returns md5sum for a message object of type '<Pose-response>"
  "c4258fd17a5d5267d5a22ad00faa1382")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Pose-response)))
  "Returns md5sum for a message object of type 'Pose-response"
  "c4258fd17a5d5267d5a22ad00faa1382")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Pose-response>)))
  "Returns full string definition for message of type '<Pose-response>"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Pose-response)))
  "Returns full string definition for message of type 'Pose-response"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Pose-response>))
  (cl:+ 0
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Pose-response>))
  "Converts a ROS message object to a list"
  (cl:list 'Pose-response
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'Pose)))
  'Pose-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'Pose)))
  'Pose-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Pose)))
  "Returns string type for a service object of type '<Pose>"
  "clb_msgs/Pose")