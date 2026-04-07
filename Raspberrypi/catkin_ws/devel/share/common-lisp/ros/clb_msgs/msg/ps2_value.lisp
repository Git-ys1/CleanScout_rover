; Auto-generated. Do not edit!


(cl:in-package clb_msgs-msg)


;//! \htmlinclude ps2_value.msg.html

(cl:defclass <ps2_value> (roslisp-msg-protocol:ros-message)
  ((data
    :reader data
    :initarg :data
    :type (cl:vector cl:fixnum)
   :initform (cl:make-array 10 :element-type 'cl:fixnum :initial-element 0)))
)

(cl:defclass ps2_value (<ps2_value>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ps2_value>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ps2_value)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name clb_msgs-msg:<ps2_value> is deprecated: use clb_msgs-msg:ps2_value instead.")))

(cl:ensure-generic-function 'data-val :lambda-list '(m))
(cl:defmethod data-val ((m <ps2_value>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader clb_msgs-msg:data-val is deprecated.  Use clb_msgs-msg:data instead.")
  (data m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ps2_value>) ostream)
  "Serializes a message object of type '<ps2_value>"
  (cl:map cl:nil #'(cl:lambda (ele) (cl:write-byte (cl:ldb (cl:byte 8 0) ele) ostream))
   (cl:slot-value msg 'data))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ps2_value>) istream)
  "Deserializes a message object of type '<ps2_value>"
  (cl:setf (cl:slot-value msg 'data) (cl:make-array 10))
  (cl:let ((vals (cl:slot-value msg 'data)))
    (cl:dotimes (i 10)
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:aref vals i)) (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ps2_value>)))
  "Returns string type for a message object of type '<ps2_value>"
  "clb_msgs/ps2_value")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ps2_value)))
  "Returns string type for a message object of type 'ps2_value"
  "clb_msgs/ps2_value")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ps2_value>)))
  "Returns md5sum for a message object of type '<ps2_value>"
  "0c05a05733f13fb160c661ca1798fdba")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ps2_value)))
  "Returns md5sum for a message object of type 'ps2_value"
  "0c05a05733f13fb160c661ca1798fdba")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ps2_value>)))
  "Returns full string definition for message of type '<ps2_value>"
  (cl:format cl:nil "uint8[10] data~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ps2_value)))
  "Returns full string definition for message of type 'ps2_value"
  (cl:format cl:nil "uint8[10] data~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ps2_value>))
  (cl:+ 0
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'data) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 1)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ps2_value>))
  "Converts a ROS message object to a list"
  (cl:list 'ps2_value
    (cl:cons ':data (data msg))
))
