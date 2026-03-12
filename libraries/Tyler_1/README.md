太乐1号库/Tyler-1 Library
========
为了便于您开发使用太乐1号，我们为太乐1号编制了Arduino第三方库。该第三方库除了有专门用于控制Arduino的库文件还有一系列示例程序供您在调试和开发太乐1号时使用。

假如您想获取太乐一号的搭建和开发讲解指导，请前往太极创客官网的太乐一号项目页面。这里您可以免费获取太乐一号视频教学和图文讲解资源。

[http://www.taichi-maker.com/homepage/arduino-tutorial-index/arduino-hardware/#taile1](http://www.taichi-maker.com/homepage/arduino-tutorial-index/arduino-hardware/#taile1)

# 请留意:
太乐1号库依赖Adafruit开发的AFMotor库，因此您需要预先将AFMotor库安装到Arduino IDE后方可使用太乐1号库。您可以在太乐1号项目仓库的res目录中找到AFMotor库源码。

--------

# 1. 安装库至Arduino IDE

当您把库文件下载到电脑中后，接下来就可以将库文件安装到Arduino IDE中以便调试和开发使用。

假如您不知道如何将库文件安装到Arduino IDE，不用担心。太极创客团队专门制作了图文及视频教程指导您如何完成此项任务。您可以通过以下链接或通过太极创客首页搜索栏搜索关键字“添加库”即可找到教程链接。

[http://www.taichi-maker.com/homepage/reference-index/arduino-library-index/install-arduino-library/](http://www.taichi-maker.com/homepage/reference-index/arduino-library-index/install-arduino-library/)

--------

# 2. 示例程序（examples目录中示例程序）简介


| 程序名称              | 程序功能                                                                                                                                                                                                                     |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Check_1_Servo_90      | 在太乐1号组装过程中，需要将舵机调整为90度位置。此程序用于将舵机调整为90度位置。                                                                                                                                              |
| Check_2_Servo_Sweep   | 本程序用于测试太乐1号的舵机是否可以正常工作。当本程序上传太乐1号以后，舵机将会左右摆动。                                                                                                                                     |
| Check_3_Dist_Sensor   | 本程序旨在测试太乐1号的距离传感器是否可以正常工作。本程序使用Taichi-HCSR04库读取HC-SR04超声波测距传感器模块读数。程序运行后，传感器将感应到的距离信息并通过Arduino IDE的串口监视器显示。                                     |
| Check_4_Bluetooth     | 此程序旨在演示如何通过HC-06模块使用蓝牙通讯向Arduino数字IO引脚收发串口数据，以及如何设置HC-06蓝牙模块。                                                                                                                      |
| Check_5_Wheel_Motors  | 本程序利用Tyler-1库文件测试太乐1号智能小车的车轮电机工作情况。用户可调节Tyler_1 tyler_1 的参数来调节电机旋转方向。此程序调节的目的是让太乐1号在本程序控制下可以向前运行。 即：M1，M2电机顺时针旋转     M3，M4电机逆时针旋转 |
| Check_6_Turn_Left_90  | 本程序用于找到太乐1号向左转动90度角度所需要的TURN_LEFT_90参数数值                                                                                                                                                           |
| Check_7_Turn_Right_90 | 本程序用于找到太乐1号向右转动90度角度所需要的TURN_RIGHT_90参数数值                                                                                                                                                          |
| Tyler_1               | 太乐1号主控制程序                                                                                                                                                                                                           |

--------

# 3. 主要库函数简介

#### 太乐1号运行控制

**void forward()**  - 太乐1号前进

**void backward()**  -   太乐1号后退

**void turnL()**  -   太乐1号左转

**void turnR()**  -   太乐1号右转

**void forwardL()**  -   太乐1号左前

**void forwardR()**  -   太乐1号右前

**void backwardL()**  -   太乐1号左后

**void backwardR()**  -   太乐1号右后

**void stop()**  -   太乐1号停车

#### 太乐1号测距传感器控制

**int getDistance()**  -   此函数返回值为太乐1号测距传感器(HCSR04)所读取的距离测量结果

#### 太乐1号头部舵机控制

**void headServoIni()**  -   头部舵机初始化。**注意**：此函数需要在setup函数中调用，否则头部舵机无法正常运行。

**void setHeadPos(int pos)**  -   设定头部舵机为指定角度，角度值由函数参数控制

**int getHeadPos()**  -   此函数返回值为太乐1号头部舵机角度值