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

class TrajectoryRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.id2 = null;
      this.id3 = null;
      this.id4 = null;
      this.id5 = null;
      this.id6 = null;
      this.time = null;
    }
    else {
      if (initObj.hasOwnProperty('id2')) {
        this.id2 = initObj.id2
      }
      else {
        this.id2 = 0;
      }
      if (initObj.hasOwnProperty('id3')) {
        this.id3 = initObj.id3
      }
      else {
        this.id3 = 0;
      }
      if (initObj.hasOwnProperty('id4')) {
        this.id4 = initObj.id4
      }
      else {
        this.id4 = 0;
      }
      if (initObj.hasOwnProperty('id5')) {
        this.id5 = initObj.id5
      }
      else {
        this.id5 = 0;
      }
      if (initObj.hasOwnProperty('id6')) {
        this.id6 = initObj.id6
      }
      else {
        this.id6 = 0;
      }
      if (initObj.hasOwnProperty('time')) {
        this.time = initObj.time
      }
      else {
        this.time = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type TrajectoryRequest
    // Serialize message field [id2]
    bufferOffset = _serializer.int16(obj.id2, buffer, bufferOffset);
    // Serialize message field [id3]
    bufferOffset = _serializer.int16(obj.id3, buffer, bufferOffset);
    // Serialize message field [id4]
    bufferOffset = _serializer.int16(obj.id4, buffer, bufferOffset);
    // Serialize message field [id5]
    bufferOffset = _serializer.int16(obj.id5, buffer, bufferOffset);
    // Serialize message field [id6]
    bufferOffset = _serializer.int16(obj.id6, buffer, bufferOffset);
    // Serialize message field [time]
    bufferOffset = _serializer.int16(obj.time, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type TrajectoryRequest
    let len;
    let data = new TrajectoryRequest(null);
    // Deserialize message field [id2]
    data.id2 = _deserializer.int16(buffer, bufferOffset);
    // Deserialize message field [id3]
    data.id3 = _deserializer.int16(buffer, bufferOffset);
    // Deserialize message field [id4]
    data.id4 = _deserializer.int16(buffer, bufferOffset);
    // Deserialize message field [id5]
    data.id5 = _deserializer.int16(buffer, bufferOffset);
    // Deserialize message field [id6]
    data.id6 = _deserializer.int16(buffer, bufferOffset);
    // Deserialize message field [time]
    data.time = _deserializer.int16(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 12;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/TrajectoryRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'f982c44c4992b0945e9540dc9fc648e5';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int16 id2
    int16 id3
    int16 id4
    int16 id5
    int16 id6
    int16 time
    
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new TrajectoryRequest(null);
    if (msg.id2 !== undefined) {
      resolved.id2 = msg.id2;
    }
    else {
      resolved.id2 = 0
    }

    if (msg.id3 !== undefined) {
      resolved.id3 = msg.id3;
    }
    else {
      resolved.id3 = 0
    }

    if (msg.id4 !== undefined) {
      resolved.id4 = msg.id4;
    }
    else {
      resolved.id4 = 0
    }

    if (msg.id5 !== undefined) {
      resolved.id5 = msg.id5;
    }
    else {
      resolved.id5 = 0
    }

    if (msg.id6 !== undefined) {
      resolved.id6 = msg.id6;
    }
    else {
      resolved.id6 = 0
    }

    if (msg.time !== undefined) {
      resolved.time = msg.time;
    }
    else {
      resolved.time = 0
    }

    return resolved;
    }
};

class TrajectoryResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
    }
    else {
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type TrajectoryResponse
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type TrajectoryResponse
    let len;
    let data = new TrajectoryResponse(null);
    return data;
  }

  static getMessageSize(object) {
    return 0;
  }

  static datatype() {
    // Returns string type for a service object
    return 'clb_msgs/TrajectoryResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'd41d8cd98f00b204e9800998ecf8427e';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new TrajectoryResponse(null);
    return resolved;
    }
};

module.exports = {
  Request: TrajectoryRequest,
  Response: TrajectoryResponse,
  md5sum() { return 'f982c44c4992b0945e9540dc9fc648e5'; },
  datatype() { return 'clb_msgs/Trajectory'; }
};
