/**********************************************************************
项目名称/Project          : 太乐1号 / Tyler-1
程序名称/Program name     : Check_4_Bluetooth
团队/Team                : 太极创客团队 / Taichi-Maker (www.taichi-maker.com)
作者/Author              : CYNO 朔 
日期/Date（YYYYMMDD）     : 20190719
程序目的/Purpose          : 
此程序旨在演示如何通过HC-06模块使用蓝牙通讯向Arduino数字IO引脚
收发串口数据，以及如何设置HC-06蓝牙模块。
-----------------------------------------------------------------------
修订历史/Revision History  
日期/Date    作者/Author      参考号/Ref    修订说明/Revision Description
-----------------------------------------------------------------------
电路连接：
  Arduino AFMOTOR SERVO2引脚（Arduino引脚9）连接 HC06-TX
  Arduino A0引脚 连接 HCSR04的 trig 引脚
  Arduino A1引脚 连接 HCSR04的 echo 引脚
***********************************************************************/

 
#include <SoftwareSerial.h>

// 建立SoftwareSerial对象，HC-06的TX接Arduino引脚9（AFMOTOR SERVO-2引脚）
SoftwareSerial BTserial(9, 2); 
 
void setup() {
  Serial.begin(9600);
  BTserial.begin(9600);   // HC-06 默认波特率 9600
 
  Serial.print("Tyler-1 HC-06 TEST");                     
 
}
 
void loop(){
 
    // 通过串口监视器显示HC-06发送的数据
    if( BTserial.available()>0 ){            //如果软件串口有HC-06发来的数据
      char BTserialData =  BTserial.read();  //将软件串口中的数据赋值给变量BTserialData
      Serial.print( BTserialData );          //通过硬件串口监视器显示HC-06发来的数据
    }
 
    // 将用户通过串口监视器输入的数据发送给HC-06
    if (Serial.available()>0) {            //如果硬件串口缓存中有等待传输的数据
      char serialData =  Serial.read();    //将硬件串口中的数据赋值给变量serialData
      BTserial.print( serialData );         //将硬件串口中的数据发送给HC-06
    }
}

/*
---- AT指令 ---- 
 
指令               答复                        说明
AT                 OK                          通讯测试
AT+VERSION         OKlinvorV1.8                固件版本
AT+NAMEmyBTmodule  OKsetname                   设置设备名 “myBTmodule”
AT+PIN6789         OKsetPIN                    设置设备 PIN 6789
AT+BAUD1           OK1200                      设置波特率 1200
AT+BAUD2           OK2400                      设置波特率 2400
AT+BAUD3           OK4800                      设置波特率 4800
AT+BAUD4           OK9600                      设置波特率 9600
AT+BAUD5           OK19200                     设置波特率 19200
AT+BAUD6           OK38400                     设置波特率 38400
AT+BAUD7           OK57600                     设置波特率 57600
AT+BAUD8           OK115200                    设置波特率 115200
AT+BAUD9           OK230400                    设置波特率 230400
AT+BAUDA           OK460800                    设置波特率 460800
AT+BAUDB           OK921600                    设置波特率 921600
AT+BAUDC           OK1382400                   设置波特率 1382400
*/
