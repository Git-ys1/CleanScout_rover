; Auto-generated. Do not edit!


(cl:in-package clb_msgs-srv)


;//! \htmlinclude FaceVoiceSet-request.msg.html

(cl:defclass <FaceVoiceSet-request> (roslisp-msg-protocol:ros-message)
  ((voice_id
    :reader voice_id
    :initarg :voice_id
    :type cl:integer
    :initform 0))
)

(cl:defclass FaceVoiceSet-request (<FaceVoiceSet-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <FaceVoiceSet-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'FaceVoiceSet-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<FaceVoiceSet-request> is deprecated: use clb_msgs-srv:FaceVoiceSet-request instead.")))

(cl:ensure-generic-function 'voice_id-val :lambda-list '(m))
(cl:defmethod voice_id-val ((m <FaceVoiceSet-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:voice_id-val is deprecated.  Use clb_msgs-srv:voice_id instead.")
  (voice_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <FaceVoiceSet-request>) ostream)
  "Serializes a message object of type '<FaceVoiceSet-request>"
  (cl:let* ((signed (cl:slot-value msg 'voice_id)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <FaceVoiceSet-request>) istream)
  "Deserializes a message object of type '<FaceVoiceSet-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'voice_id) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<FaceVoiceSet-request>)))
  "Returns string type for a service object of type '<FaceVoiceSet-request>"
  "clb_msgs/FaceVoiceSetRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'FaceVoiceSet-request)))
  "Returns string type for a service object of type 'FaceVoiceSet-request"
  "clb_msgs/FaceVoiceSetRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<FaceVoiceSet-request>)))
  "Returns md5sum for a message object of type '<FaceVoiceSet-request>"
  "90941b667b08b1366244be00f14ce2ac")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'FaceVoiceSet-request)))
  "Returns md5sum for a message object of type 'FaceVoiceSet-request"
  "90941b667b08b1366244be00f14ce2ac")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<FaceVoiceSet-request>)))
  "Returns full string definition for message of type '<FaceVoiceSet-request>"
  (cl:format cl:nil "int32 voice_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'FaceVoiceSet-request)))
  "Returns full string definition for message of type 'FaceVoiceSet-request"
  (cl:format cl:nil "int32 voice_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <FaceVoiceSet-request>))
  (cl:+ 0
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <FaceVoiceSet-request>))
  "Converts a ROS message object to a list"
  (cl:list 'FaceVoiceSet-request
    (cl:cons ':voice_id (voice_id msg))
))
;//! \htmlinclude FaceVoiceSet-response.msg.html

(cl:defclass <FaceVoiceSet-response> (roslisp-msg-protocol:ros-message)
  ((face_id
    :reader face_id
    :initarg :face_id
    :type cl:boolean
    :initform cl:nil)
   (name
    :reader name
    :initarg :name
    :type cl:string
    :initform ""))
)

(cl:defclass FaceVoiceSet-response (<FaceVoiceSet-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <FaceVoiceSet-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'FaceVoiceSet-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-srv:<FaceVoiceSet-response> is deprecated: use clb_msgs-srv:FaceVoiceSet-response instead.")))

(cl:ensure-generic-function 'face_id-val :lambda-list '(m))
(cl:defmethod face_id-val ((m <FaceVoiceSet-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:face_id-val is deprecated.  Use clb_msgs-srv:face_id instead.")
  (face_id m))

(cl:ensure-generic-function 'name-val :lambda-list '(m))
(cl:defmethod name-val ((m <FaceVoiceSet-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-srv:name-val is deprecated.  Use clb_msgs-srv:name instead.")
  (name m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <FaceVoiceSet-response>) ostream)
  "Serializes a message object of type '<FaceVoiceSet-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'face_id) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'name))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'name))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <FaceVoiceSet-response>) istream)
  "Deserializes a message object of type '<FaceVoiceSet-response>"
    (cl:setf (cl:slot-value msg 'face_id) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'name) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'name) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<FaceVoiceSet-response>)))
  "Returns string type for a service object of type '<FaceVoiceSet-response>"
  "clb_msgs/FaceVoiceSetResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'FaceVoiceSet-response)))
  "Returns string type for a service object of type 'FaceVoiceSet-response"
  "clb_msgs/FaceVoiceSetResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<FaceVoiceSet-response>)))
  "Returns md5sum for a message object of type '<FaceVoiceSet-response>"
  "90941b667b08b1366244be00f14ce2ac")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'FaceVoiceSet-response)))
  "Returns md5sum for a message object of type 'FaceVoiceSet-response"
  "90941b667b08b1366244be00f14ce2ac")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<FaceVoiceSet-response>)))
  "Returns full string definition for message of type '<FaceVoiceSet-response>"
  (cl:format cl:nil "bool face_id~%string name~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'FaceVoiceSet-response)))
  "Returns full string definition for message of type 'FaceVoiceSet-response"
  (cl:format cl:nil "bool face_id~%string name~%~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <FaceVoiceSet-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'name))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <FaceVoiceSet-response>))
  "Converts a ROS message object to a list"
  (cl:list 'FaceVoiceSet-response
    (cl:cons ':face_id (face_id msg))
    (cl:cons ':name (name msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'FaceVoiceSet)))
  'FaceVoiceSet-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'FaceVoiceSet)))
  'FaceVoiceSet-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'FaceVoiceSet)))
  "Returns string type for a service object of type '<FaceVoiceSet>"
  "clb_msgs/FaceVoiceSet")