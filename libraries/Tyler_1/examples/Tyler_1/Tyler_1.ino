/**********************************************************************
项目名称/Project          : 太乐1号 / Tyler-1
程序名称/Program name     : Tyler_1
团队/Team                 : 太极创客团队 / Taichi-Maker (www.taichi-maker.com)
作者/Author               : CYNO 朔 
日期/Date（YYYYMMDD）     : 20190920
程序目的/Purpose          : 
本程序为太乐一号库主控制程序。太乐一号库中有一系列示例程序（程序名以Check开头）。
这些示例程序的作用是调试和测试太乐一号使用。在使用本程序前，请确保您已经完成了太乐
一号的搭建和调试工作。

如需获得更多的太乐一号资料，请参与太极创客网站太乐一号页：
http://www.taichi-maker.com/homepage/arduino-tutorial-index/arduino-hardware/#taile1

-----------------------------------------------------------------------
修订历史/Revision History  
日期/Date    作者/Author      参考号/Ref    修订说明/Revision Description
20190727       CYNO朔            0.01       结合新的库文件修改自动控制模式
20190821       CYNO朔            0.02       根据新应用调整控制字符以及控制流程
20190831       CYNO朔            0.03       添加更多注释信息，让程序增加可读性
20190831       CYNO朔            0.10       优化代码控制流程，简化串口输出，去掉
                                            控制debug信息的宏定义操作
20190920       CYNO朔            0.11       去除turn_back功能 
                                            整理程序格式并添加更丰富程序注释   
20190920       CYNO朔            0.12       仅软件串口                                                                        
-----------------------------------------------------------------------
电路连接：
  Arduino AFMOTOR SERVO-2引脚（Arduino引脚9） 连接 HC06-TX
  Arduino AFMOTOR SERVO-1引脚（Arduino引脚10）连接 舵机信号线
  Arduino A0引脚 连接 HCSR04的 trig 引脚
  Arduino A1引脚 连接 HCSR04的 echo 引脚
  Arduino 10引脚 连接 头部舵机 控制信号线
其它说明（以下注释内容见本程序尾部）：
 - 蓝牙应用控制用字符说明

***********************************************************************/
#include <Tyler_1.h>
#include <SoftwareSerial.h>

#define OK_DIST 35        // 避障距离参数（cm）
#define MAN 0             // 手动模式
#define AUTO 1            // 自动模式
#define GEST 2            // 体感模式

#define TURN_LEFT_90   900        // 左转90度延迟参数
#define TURN_RIGHT_90   1000      // 右转90度延迟参数

// 建立太乐1号对象。其中对象参数分别是：
// (车轮电机1运转方向, 车轮电机2运转方向, 车轮电机3运转方向, 车轮电机4运转方向,
// 车轮电机运转速度，测距传感器TRIG引脚， 测距传感器ECHO引脚，头部舵机信号引脚 )
Tyler_1 tyler_1(1, 1, 1, 1, 200, A0, A1, 10); 
                                                                                               
// 建立SoftwareSerial对象，HC-06的TX接Arduino引脚9（AFMOTOR SERVO-2引脚）
SoftwareSerial softSerial(9, 2);    

char cmdChar = '5';             // 存放串口控制指令字符
byte systemMode = MAN;          // 用于控制系统运行模式
                           
void setup() {

  softSerial.begin(9600);     // 启动软件串口（用于接收手机控制指令信息）
  delay(100);   
  
  tyler_1.headServoIni();    //头部舵机初始化
  tyler_1.setHeadPos(90);    // 系统启动时将头部设置为90位置
    
}

void loop() {

  if(softSerial.available()){           // 如果软件串口收到信息
    cmdChar = softSerial.read();        // 将信息传递给cmdChar变量
  }   

  runMode();                           // 执行运行模式并实施相应控制
}

// 执行运行模式并实施相应控制
void runMode(){
  switch(cmdChar){
    case 'A':                       // 用户输入控制指令字符为自动运行字符'A'
      systemMode = AUTO;            // 将当前运行模式控制变量设置为AUTO
      break;
      
    case 'M':                       // 用户输入控制指令字符为自动运行字符'M'          
      systemMode = MAN;             // 将当前运行模式控制变量设置为手动  
      tyler_1.stop();               // 切换为手动模式后自动停车
      cmdChar =  '5';               // 并且将控制指令字符设置为'5'（停车字符）
      break;      

    case 'G':                       // 用户输入控制指令字符为自动运行字符'G'          
      systemMode = GEST;             // 将当前运行模式控制变量设置为体感模式
      tyler_1.stop();               // 切换为体感模式后自动停车
      cmdChar =  '5';               // 并且将控制指令字符设置为'5'（停车字符）
      break;        
  }
  
  if (systemMode == MAN || systemMode == GEST ){  // 如果当前运行模式为手动或体感
    manMode();                      // 则使用手动控制函数控制太乐1号（体感和手动模式的控制字符相同）
  } else if(systemMode == AUTO){    // 如果当前运行模式为自动
    autoMode();                     // 则使用自动控制函数控制太乐1号
  }     
}

// 太乐1号手动控制函数
void manMode(){

  switch(cmdChar){ 

    case '8': // 前进
      tyler_1.forward();
      break;             

    case '2': // 后退
      tyler_1.backward();
      break;   

    case '4': //左转
      tyler_1.turnL();
      break;        

    case '6': //右转
      tyler_1.turnR();
      break;    
      
    case '5': //停止
      tyler_1.stop();
      break;       

    case '7': //左前
      tyler_1.forwardL();
      break;         

    case '9': //右前
      tyler_1.forwardR();
      break;      

    case '1': //右后
      tyler_1.backwardR();
      break; 

    case '3': //左后
      tyler_1.backwardL();
      break;                 
  }

}

// 太乐1号自动控制函数
void autoMode(){ 
    
  int frontDist = tyler_1.getDistance(); // 检查前方距离
  delay(50);              // 提高系统稳定性等待
  
  if(frontDist >= OK_DIST){          // 如果检测前方距离读数大于等于允许距离参数
    tyler_1.forward();               // 太乐1号向前
  } else {                           // 如果检测前方距离小于允许距离参数
    tyler_1.stop();                  // 太乐1号停止   
    autoTurn();                      // 检测左右侧距离并做出自动转向 
  }
}

// 检查左右方向距离并返回专项方向
void autoTurn(){
  
  // 检查右侧距离     
  for (int pos = 90; pos >= 0; pos -= 1) {
    tyler_1.setHeadPos(pos);               
    delay(3);                     
  }  
  int rightDist =  tyler_1.getDistance();
  delay(300);              // 提高系统稳定性等待

  // 检查左侧距离     
  for (int pos = 0; pos <= 180; pos += 1) {
    tyler_1.setHeadPos(pos);                
    delay(3);                     
  }
  int leftDist =  tyler_1.getDistance();  
  delay(300);              // 提高系统稳定性等待  

  //将头部调整到正前方
  for (int pos = 180; pos >= 90; pos -= 1) {
    tyler_1.setHeadPos(pos);               
    delay(3);                     
  }
  delay(300);              // 提高系统稳定性等待
  
  //检查左右距离并做出转向决定
  if ( rightDist >= leftDist){               // 如果右边距离大于左边距离              
    turnR90();                                      // 右转90度
    return;
  } else {                                         // 如果左边距离大于右边距离              
    turnL90();                                     // 左转90度
    return;
  }
}

// 左转90度
void turnL90(){
  tyler_1.turnL();
  delay(TURN_LEFT_90);
}

// 右转90度
void turnR90(){
  tyler_1.turnR();
  delay(TURN_RIGHT_90);  
}

/*
控制指令字符

模式控制
A --- AUTO 自动避障模式
M --- MAN  人工控制模式
G --- GEST 体感控制模式

运行控制
8  ---  前进
2  ---  后退
4  ---  左转
6  ---  右转
5  ---  停车
7  ---  左前
9  ---  右前
1  ---  左后
3  ---  右后
A  ---  自动模式
M  ---  手动模式
G  ---  体感模式
*/
