// Auto-generated. Do not edit!

// (in-package clb_msgs.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class RobotVoiceCtrlRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.ctrl_id = null;
    }
    else {
      if (initObj.hasOwnProperty('ctrl_id')) {
        this.ctrl_id = initObj.ctrl_id
      }
      else {
        this.ctrl_id = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type RobotVoiceCtrlRequest
    // Serialize message field [ctrl_id]
    bufferOffset = _serializer.int32(obj.ctrl_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type RobotVoiceCtrlRequest
    let len;
    let data = new RobotVoiceCtrlRequest(null);
    // Deserialize message field [ctrl_id]
    data.ctrl_id = _deserializer.int32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 4;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/RobotVoiceCtrlRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '11f6f9365c6a32e4d7e2a5c7cc4c8895';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int32 ctrl_id
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new RobotVoiceCtrlRequest(null);
    if (msg.ctrl_id !== undefined) {
      resolved.ctrl_id = msg.ctrl_id;
    }
    else {
      resolved.ctrl_id = 0
    }

    return resolved;
    }
};

class RobotVoiceCtrlResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.face_id = null;
    }
    else {
      if (initObj.hasOwnProperty('face_id')) {
        this.face_id = initObj.face_id
      }
      else {
        this.face_id = false;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type RobotVoiceCtrlResponse
    // Serialize message field [face_id]
    bufferOffset = _serializer.bool(obj.face_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type RobotVoiceCtrlResponse
    let len;
    let data = new RobotVoiceCtrlResponse(null);
    // Deserialize message field [face_id]
    data.face_id = _deserializer.bool(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 1;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/RobotVoiceCtrlResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '337f2aabe2cbd4bf896f44421c3c0179';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool face_id
    
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new RobotVoiceCtrlResponse(null);
    if (msg.face_id !== undefined) {
      resolved.face_id = msg.face_id;
    }
    else {
      resolved.face_id = false
    }

    return resolved;
    }
};

module.exports = {
  Request: RobotVoiceCtrlRequest,
  Response: RobotVoiceCtrlResponse,
  md5sum() { return '99d7cbf41203ea07c76e17ef42eda7f5'; },
  datatype() { return 'clb_msgs/RobotVoiceCtrl'; }
};
