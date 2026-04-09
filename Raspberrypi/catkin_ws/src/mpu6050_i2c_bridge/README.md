# mpu6050_i2c_bridge

`mpu6050_i2c_bridge` is the Raspberry Pi side raw MPU6050 driver layer for `C-2.3.1`.

## Purpose

- read MPU6050 directly from Raspberry Pi I2C bus 1
- freeze MPU6050 address at `0x68`
- publish raw measurements on the existing `raw_imu` topic using `clb_msgs/Imu`
- feed the existing `imu_calib -> imu_filter_madgwick -> robot_localization` chain without rewriting it

## Frozen hardware assumptions

- bus: `/dev/i2c-1`
- address: `0x68`
- AD0 tied to `GND`
- `XDA`, `XCL`, and `INT` not connected in this phase

## Published topic

- `raw_imu` (`clb_msgs/Imu`)

## Bringup

```bash
source /home/clbrobot/Work/CleanScout_rover/Raspberrypi/catkin_ws/devel/setup.bash
roslaunch mpu6050_i2c_bridge mpu6050_raw.launch
```

## Notes

- This node intentionally publishes only accelerometer and gyro data.
- Magnetic field is set to zero because MPU6050 has no magnetometer.
- The active implementation uses `python3-smbus` on `/dev/i2c-1`.
