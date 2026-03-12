/**********************************************************************
项目名称/Project          : 太乐1号 / Tyler-1
程序名称/Program name     : Tyler-1-Servo-Sweep
团队/Team                : 太极创客团队 / Taichi-Maker (www.taichi-maker.com)
作者/Author              : CYNO 朔 
日期/Date（YYYYMMDD）     : 20190716
程序目的/Purpose          : 
本程序用于测试太乐1号的舵机是否可以正常工作。当本程序上传太乐1号以后，舵机将会左右摆动。
-----------------------------------------------------------------------
修订历史/Revision History  
日期/Date    作者/Author      参考号/Ref    修订说明/Revision Description
-----------------------------------------------------------------------
电路连接：
    舵机    -------   Arduino
    +5V    -------    +5VDC
    GND    -------     GND
    信号    -------     10    
***********************************************************************/

#include <Tyler_1.h>

// 建立太乐1号对象。其中对象参数分别是：
// (车轮电机1运转方向, 车轮电机2运转方向, 车轮电机3运转方向, 车轮电机4运转方向,
// 车轮电机运转速度，测距传感器TRIG引脚， 测距传感器ECHO引脚，头部舵机信号引脚 )
Tyler_1 tyler_1(1, 1, 1, 1, 200, A0, A1, 10);   

void setup() {
  Serial.begin(9600);
  tyler_1.headServoIni();  //头部舵机初始化  
}

void loop() {

  for(int i = 0; i <= 180; i++){
    tyler_1.setHeadPos(i);
    Serial.println(tyler_1.getHeadPos());
    delay(15);
  }
  
  for(int i = 180; i >=0; i--){
    tyler_1.setHeadPos(i);
    Serial.println(tyler_1.getHeadPos());
    delay(15);
  }  

}
