; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude Trajectory-request.msg.html

(cl:defclass <Trajectory-request> (roslisp-msg-protocol:ros-message)
  ((id2
    :reader id2
    :initarg :id2
    :type cl:fixnum
    :initform 0)
   (id3
    :reader id3
    :initarg :id3
    :type cl:fixnum
    :initform 0)
   (id4
    :reader id4
    :initarg :id4
    :type cl:fixnum
    :initform 0)
   (id5
    :reader id5
    :initarg :id5
    :type cl:fixnum
    :initform 0)
   (id6
    :reader id6
    :initarg :id6
    :type cl:fixnum
    :initform 0)
   (time
    :reader time
    :initarg :time
    :type cl:fixnum
    :initform 0))
)

(cl:defclass Trajectory-request (<Trajectory-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Trajectory-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Trajectory-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Trajectory-request> is deprecated: use clb_msgs-srv:Trajectory-request instead.")))

(cl:ensure-generic-function 'id2-val :lambda-list '(m))
(cl:defmethod id2-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:id2-val is deprecated.  Use clb_msgs-srv:id2 instead.")
  (id2 m))

(cl:ensure-generic-function 'id3-val :lambda-list '(m))
(cl:defmethod id3-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:id3-val is deprecated.  Use clb_msgs-srv:id3 instead.")
  (id3 m))

(cl:ensure-generic-function 'id4-val :lambda-list '(m))
(cl:defmethod id4-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:id4-val is deprecated.  Use clb_msgs-srv:id4 instead.")
  (id4 m))

(cl:ensure-generic-function 'id5-val :lambda-list '(m))
(cl:defmethod id5-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:id5-val is deprecated.  Use clb_msgs-srv:id5 instead.")
  (id5 m))

(cl:ensure-generic-function 'id6-val :lambda-list '(m))
(cl:defmethod id6-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:id6-val is deprecated.  Use clb_msgs-srv:id6 instead.")
  (id6 m))

(cl:ensure-generic-function 'time-val :lambda-list '(m))
(cl:defmethod time-val ((m <Trajectory-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:time-val is deprecated.  Use clb_msgs-srv:time instead.")
  (time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Trajectory-request>) ostream)
  "Serializes a message object of type '<Trajectory-request>"
  (cl:let* ((signed (cl:slot-value msg 'id2)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'id3)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'id4)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'id5)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'id6)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'time)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Trajectory-request>) istream)
  "Deserializes a message object of type '<Trajectory-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id2) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id3) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id4) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id5) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'id6) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'time) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Trajectory-request>)))
  "Returns string type for a service object of type '<Trajectory-request>"
  "clb_msgs/TrajectoryRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Trajectory-request)))
  "Returns string type for a service object of type 'Trajectory-request"
  "clb_msgs/TrajectoryRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Trajectory-request>)))
  "Returns md5sum for a message object of type '<Trajectory-request>"
  "f982c44c4992b0945e9540dc9fc648e5")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Trajectory-request)))
  "Returns md5sum for a message object of type 'Trajectory-request"
  "f982c44c4992b0945e9540dc9fc648e5")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Trajectory-request>)))
  "Returns full string definition for message of type '<Trajectory-request>"
  (cl:format cl:nil "int16 id2~%int16 id3~%int16 id4~%int16 id5~%int16 id6~%int16 time~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Trajectory-request)))
  "Returns full string definition for message of type 'Trajectory-request"
  (cl:format cl:nil "int16 id2~%int16 id3~%int16 id4~%int16 id5~%int16 id6~%int16 time~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Trajectory-request>))
  (cl:+ 0
     2
     2
     2
     2
     2
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Trajectory-request>))
  "Converts a ROS message object to a list"
  (cl:list 'Trajectory-request
    (cl:cons ':id2 (id2 msg))
    (cl:cons ':id3 (id3 msg))
    (cl:cons ':id4 (id4 msg))
    (cl:cons ':id5 (id5 msg))
    (cl:cons ':id6 (id6 msg))
    (cl:cons ':time (time msg))
))
;//! \htmlinclude Trajectory-response.msg.html

(cl:defclass <Trajectory-response> (roslisp-msg-protocol:ros-message)
  ()
)

(cl:defclass Trajectory-response (<Trajectory-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Trajectory-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Trajectory-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<Trajectory-response> is deprecated: use clb_msgs-srv:Trajectory-response instead.")))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Trajectory-response>) ostream)
  "Serializes a message object of type '<Trajectory-response>"
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Trajectory-response>) istream)
  "Deserializes a message object of type '<Trajectory-response>"
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Trajectory-response>)))
  "Returns string type for a service object of type '<Trajectory-response>"
  "clb_msgs/TrajectoryResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Trajectory-response)))
  "Returns string type for a service object of type 'Trajectory-response"
  "clb_msgs/TrajectoryResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Trajectory-response>)))
  "Returns md5sum for a message object of type '<Trajectory-response>"
  "f982c44c4992b0945e9540dc9fc648e5")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Trajectory-response)))
  "Returns md5sum for a message object of type 'Trajectory-response"
  "f982c44c4992b0945e9540dc9fc648e5")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Trajectory-response>)))
  "Returns full string definition for message of type '<Trajectory-response>"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Trajectory-response)))
  "Returns full string definition for message of type 'Trajectory-response"
  (cl:format cl:nil "~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Trajectory-response>))
  (cl:+ 0
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Trajectory-response>))
  "Converts a ROS message object to a list"
  (cl:list 'Trajectory-response
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'Trajectory)))
  'Trajectory-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'Trajectory)))
  'Trajectory-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Trajectory)))
  "Returns string type for a service object of type '<Trajectory>"
  "clb_msgs/Trajectory")