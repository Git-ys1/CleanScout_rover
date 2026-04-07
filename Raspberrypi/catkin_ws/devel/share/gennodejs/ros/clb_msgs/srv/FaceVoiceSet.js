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

class FaceVoiceSetRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.voice_id = null;
    }
    else {
      if (initObj.hasOwnProperty('voice_id')) {
        this.voice_id = initObj.voice_id
      }
      else {
        this.voice_id = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type FaceVoiceSetRequest
    // Serialize message field [voice_id]
    bufferOffset = _serializer.int32(obj.voice_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type FaceVoiceSetRequest
    let len;
    let data = new FaceVoiceSetRequest(null);
    // Deserialize message field [voice_id]
    data.voice_id = _deserializer.int32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 4;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/FaceVoiceSetRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '98325de2d7d0e1dc65e6817d659bf621';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int32 voice_id
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new FaceVoiceSetRequest(null);
    if (msg.voice_id !== undefined) {
      resolved.voice_id = msg.voice_id;
    }
    else {
      resolved.voice_id = 0
    }

    return resolved;
    }
};

class FaceVoiceSetResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.face_id = null;
      this.name = null;
    }
    else {
      if (initObj.hasOwnProperty('face_id')) {
        this.face_id = initObj.face_id
      }
      else {
        this.face_id = false;
      }
      if (initObj.hasOwnProperty('name')) {
        this.name = initObj.name
      }
      else {
        this.name = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type FaceVoiceSetResponse
    // Serialize message field [face_id]
    bufferOffset = _serializer.bool(obj.face_id, buffer, bufferOffset);
    // Serialize message field [name]
    bufferOffset = _serializer.string(obj.name, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type FaceVoiceSetResponse
    let len;
    let data = new FaceVoiceSetResponse(null);
    // Deserialize message field [face_id]
    data.face_id = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [name]
    data.name = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.name);
    return length + 5;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/FaceVoiceSetResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '0287046282234b95fe7e07ac1a8feb81';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool face_id
    string name
    
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new FaceVoiceSetResponse(null);
    if (msg.face_id !== undefined) {
      resolved.face_id = msg.face_id;
    }
    else {
      resolved.face_id = false
    }

    if (msg.name !== undefined) {
      resolved.name = msg.name;
    }
    else {
      resolved.name = ''
    }

    return resolved;
    }
};

module.exports = {
  Request: FaceVoiceSetRequest,
  Response: FaceVoiceSetResponse,
  md5sum() { return '90941b667b08b1366244be00f14ce2ac'; },
  datatype() { return 'clb_msgs/FaceVoiceSet'; }
};
