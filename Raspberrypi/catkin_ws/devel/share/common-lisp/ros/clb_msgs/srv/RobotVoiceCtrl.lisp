; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude RobotVoiceCtrl-request.msg.html

(cl:defclass <RobotVoiceCtrl-request> (roslisp-msg-protocol:ros-message)
  ((ctrl_id
    :reader ctrl_id
    :initarg :ctrl_id
    :type cl:integer
    :initform 0))
)

(cl:defclass RobotVoiceCtrl-request (<RobotVoiceCtrl-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <RobotVoiceCtrl-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'RobotVoiceCtrl-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<RobotVoiceCtrl-request> is deprecated: use clb_msgs-srv:RobotVoiceCtrl-request instead.")))

(cl:ensure-generic-function 'ctrl_id-val :lambda-list '(m))
(cl:defmethod ctrl_id-val ((m <RobotVoiceCtrl-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:ctrl_id-val is deprecated.  Use clb_msgs-srv:ctrl_id instead.")
  (ctrl_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <RobotVoiceCtrl-request>) ostream)
  "Serializes a message object of type '<RobotVoiceCtrl-request>"
  (cl:let* ((signed (cl:slot-value msg 'ctrl_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <RobotVoiceCtrl-request>) istream)
  "Deserializes a message object of type '<RobotVoiceCtrl-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'ctrl_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<RobotVoiceCtrl-request>)))
  "Returns string type for a service object of type '<RobotVoiceCtrl-request>"
  "clb_msgs/RobotVoiceCtrlRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'RobotVoiceCtrl-request)))
  "Returns string type for a service object of type 'RobotVoiceCtrl-request"
  "clb_msgs/RobotVoiceCtrlRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<RobotVoiceCtrl-request>)))
  "Returns md5sum for a message object of type '<RobotVoiceCtrl-request>"
  "99d7cbf41203ea07c76e17ef42eda7f5")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'RobotVoiceCtrl-request)))
  "Returns md5sum for a message object of type 'RobotVoiceCtrl-request"
  "99d7cbf41203ea07c76e17ef42eda7f5")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<RobotVoiceCtrl-request>)))
  "Returns full string definition for message of type '<RobotVoiceCtrl-request>"
  (cl:format cl:nil "int32 ctrl_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'RobotVoiceCtrl-request)))
  "Returns full string definition for message of type 'RobotVoiceCtrl-request"
  (cl:format cl:nil "int32 ctrl_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <RobotVoiceCtrl-request>))
  (cl:+ 0
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <RobotVoiceCtrl-request>))
  "Converts a ROS message object to a list"
  (cl:list 'RobotVoiceCtrl-request
    (cl:cons ':ctrl_id (ctrl_id msg))
))
;//! \htmlinclude RobotVoiceCtrl-response.msg.html

(cl:defclass <RobotVoiceCtrl-response> (roslisp-msg-protocol:ros-message)
  ((face_id
    :reader face_id
    :initarg :face_id
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass RobotVoiceCtrl-response (<RobotVoiceCtrl-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <RobotVoiceCtrl-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'RobotVoiceCtrl-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<RobotVoiceCtrl-response> is deprecated: use clb_msgs-srv:RobotVoiceCtrl-response instead.")))

(cl:ensure-generic-function 'face_id-val :lambda-list '(m))
(cl:defmethod face_id-val ((m <RobotVoiceCtrl-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:face_id-val is deprecated.  Use clb_msgs-srv:face_id instead.")
  (face_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <RobotVoiceCtrl-response>) ostream)
  "Serializes a message object of type '<RobotVoiceCtrl-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'face_id) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <RobotVoiceCtrl-response>) istream)
  "Deserializes a message object of type '<RobotVoiceCtrl-response>"
    (cl:setf (cl:slot-value msg 'face_id) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<RobotVoiceCtrl-response>)))
  "Returns string type for a service object of type '<RobotVoiceCtrl-response>"
  "clb_msgs/RobotVoiceCtrlResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'RobotVoiceCtrl-response)))
  "Returns string type for a service object of type 'RobotVoiceCtrl-response"
  "clb_msgs/RobotVoiceCtrlResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<RobotVoiceCtrl-response>)))
  "Returns md5sum for a message object of type '<RobotVoiceCtrl-response>"
  "99d7cbf41203ea07c76e17ef42eda7f5")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'RobotVoiceCtrl-response)))
  "Returns md5sum for a message object of type 'RobotVoiceCtrl-response"
  "99d7cbf41203ea07c76e17ef42eda7f5")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<RobotVoiceCtrl-response>)))
  "Returns full string definition for message of type '<RobotVoiceCtrl-response>"
  (cl:format cl:nil "bool face_id~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'RobotVoiceCtrl-response)))
  "Returns full string definition for message of type 'RobotVoiceCtrl-response"
  (cl:format cl:nil "bool face_id~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <RobotVoiceCtrl-response>))
  (cl:+ 0
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <RobotVoiceCtrl-response>))
  "Converts a ROS message object to a list"
  (cl:list 'RobotVoiceCtrl-response
    (cl:cons ':face_id (face_id msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'RobotVoiceCtrl)))
  'RobotVoiceCtrl-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'RobotVoiceCtrl)))
  'RobotVoiceCtrl-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'RobotVoiceCtrl)))
  "Returns string type for a service object of type '<RobotVoiceCtrl>"
  "clb_msgs/RobotVoiceCtrl")