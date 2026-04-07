// Auto-generated. Do not edit!

// (in-package clb_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------

class Bluetooth {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.connect_stats = null;
      this.angle_x = null;
      this.angle_y = null;
    }
    else {
      if (initObj.hasOwnProperty('connect_stats')) {
        this.connect_stats = initObj.connect_stats
      }
      else {
        this.connect_stats = 0;
      }
      if (initObj.hasOwnProperty('angle_x')) {
        this.angle_x = initObj.angle_x
      }
      else {
        this.angle_x = 0;
      }
      if (initObj.hasOwnProperty('angle_y')) {
        this.angle_y = initObj.angle_y
      }
      else {
        this.angle_y = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Bluetooth
    // Serialize message field [connect_stats]
    bufferOffset = _serializer.int32(obj.connect_stats, buffer, bufferOffset);
    // Serialize message field [angle_x]
    bufferOffset = _serializer.int32(obj.angle_x, buffer, bufferOffset);
    // Serialize message field [angle_y]
    bufferOffset = _serializer.int32(obj.angle_y, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Bluetooth
    let len;
    let data = new Bluetooth(null);
    // Deserialize message field [connect_stats]
    data.connect_stats = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [angle_x]
    data.angle_x = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [angle_y]
    data.angle_y = _deserializer.int32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 12;
  }

  static datatype() {
    // Returns string type for a message object
    return 'clb_msgs/Bluetooth';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'd231f5dc5332675e1ab8a685bdfd06a0';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int32 connect_stats
    int32 angle_x
    int32 angle_y
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Bluetooth(null);
    if (msg.connect_stats !== undefined) {
      resolved.connect_stats = msg.connect_stats;
    }
    else {
      resolved.connect_stats = 0
    }

    if (msg.angle_x !== undefined) {
      resolved.angle_x = msg.angle_x;
    }
    else {
      resolved.angle_x = 0
    }

    if (msg.angle_y !== undefined) {
      resolved.angle_y = msg.angle_y;
    }
    else {
      resolved.angle_y = 0
    }

    return resolved;
    }
};

module.exports = Bluetooth;
