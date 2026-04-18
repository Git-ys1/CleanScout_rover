/**********************************************************************
项目名称/Project          : 太乐1号 / Tyler-1
程序名称/Program name     : Check_3_Dist_Sensor
团队/Team                : 太极创客团队 / Taichi-Maker (www.taichi-maker.com)
作者/Author              : CYNO 朔 
日期/Date（YYYYMMDD）     : 20190716
程序目的/Purpose          : 
本程序旨在测试太乐1号的距离传感器是否可以正常工作。
本程序使用Taichi-HCSR04库读取HC-SR04超声波测距传感器模块读数。
程序运行后，传感器将感应到的距离信息并通过Arduino IDE的串口监视器显示。 

This code is to test if the HCSR04 sensor works properly.
After uploading this code to Arduino, The distance measurement 
results will be displayed in Arduino IDE's Serial Monitor. 
-----------------------------------------------------------------------
修订历史/Revision History  
日期/Date    作者/Author      参考号/Ref    修订说明/Revision Description
-----------------------------------------------------------------------
电路连接：
  HC-SR04   -------   Arduino
    VCC     -------    +5VDC
    Trig    -------     A0
    Echo    -------     A1
    GND     -------     GND
***********************************************************************/

#include <Tyler_1.h>

// 建立太乐1号对象。其中对象参数分别是：
// (车轮电机1运转方向, 车轮电机2运转方向, 车轮电机3运转方向, 车轮电机4运转方向,
// 车轮电机运转速度，测距传感器TRIG引脚， 测距传感器ECHO引脚，头部舵机信号引脚 )
Tyler_1 tyler_1(1, 1, 1, 1, 200, A0, A1, 10);     

void setup() {
  Serial.begin (9600);
}

void loop(){
  int distCM = tyler_1.getDistance();  //读取传感器测量举例
  Serial.print(distCM);         //通过串口监视器输出测量距离值
  Serial.println("cm");         //单位是厘米

  delay(1000);
}
