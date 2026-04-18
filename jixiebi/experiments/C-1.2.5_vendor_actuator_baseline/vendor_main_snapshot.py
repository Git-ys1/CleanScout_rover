# Untitled - By: Admin - Sun Mar 17 2024

import sensor, image, time,pyb,omv,math,utime,tf,gc,lcd
from pyb import UART,Pin,Timer,Servo
from machine import SPI
from ubluetooth import CARSTATE,UBLUETOOTH
from pid import PID
#notes：
#配合视频小车app，实现小车寻迹，跟随，避障三种功能
#寻迹，小车沿着黑线前进，可以自己标定一下线的阈值
#跟随，小车人脸检测跟随
#避障，暂未添加，可看寻迹避障跟随原始例程
#前面三种模式下，按下小车前后左右键可以控制小车
#开灯，关灯按钮暂时用来作为云台控制功能，即按下这两个按钮时，上下左右键可以控制云台，也可以切换到云台自动跟随
#以上仅为参考功能设计，可以在ubluetooth.py库自行定义其他功能
global ultradis,carstate,cardir,left_speed,right_speed,img,THRESHOLD,flag_lost
ultradis=0.0
ble=UBLUETOOTH(uart_port=1,baudrate=9600)
objects = list()
last_objects=objects
flag_lost=0 #目标丢失计数
#LCD初始化
lcd.init(type=2,width=240,height=320)
lcd.clear()
lcd.set_direction(2)

pan_servo=Servo(3)      #左右控制PD14
tilt_servo=Servo(4)     #上下控制PD15
#pan_servo.calibration(500, 2500, 1500)
#tilt_servo.calibration(500, 2500, 1500)
pan_servo.angle(0)
tilt_servo.angle(-30)
Servo(1).angle(50)
#舵机PID
pan_pid = PID(p=0.2, i=0.0 ,imax=90)#在线调试使用这个PID
tilt_pid = PID(p=0.2, i=0.0, imax=90)#在线调试使用这个PID
#小车追踪PID
dis_pid = PID(p=0.15, i=0.01)
len_pid = PID(p=0.45, i=0.01)

#加载yoloface人脸检测模型,人脸检测容易内存不足，暂时屏蔽
net = None
labels = None
confidence=0.7
try:
    # load the model, alloc the model file on the heap if we have at least 64K free after loading
    labels,net = tf.load_builtin_model('yoloface')
    #net = tf.load("yoloface.tflite",load_to_fb=True)
except Exception as e:
    raise Exception('Failed to load "yoloface", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')
print(net)

#功能： 寻找最大的目标，计算方式为像素面积排序
#输入： 链表objects，坐标X,坐标y,像素宽,像素高,mode=0是色块，1是人脸坐标
#输出： 最大目标元组,
def find_max_object(objects,mode=0):
    max_size=0
    if mode==0:#色块元组
        max_object=None
    if mode==1:#人脸框坐标格式和色块不同，单独定义
        max_object=(0,0,0,0,0.0)
    for object in objects:
        if object[2]*object[3] > max_size:
            max_object=object
            max_size = object[2]*object[3]
    return max_object

#功能： 人脸跟随，yolo算法
#输入： 图像
#输出： 无
def face_detect(img):
    max_object=(0,0,0,0,0.0)
    object_s=0
    objects=None
    rid=img.width()/img.height() #模型计算输入是按宽高相等的，因此输出坐标要做转换
    objects=net.detect_yolo(img, confidence=0.75, anchors=[21,28,34,49,61,77],nms=0.2)#YOLOface50,Kanchors=[9,14,12,17,22,21]
    #if (len(objects) == 0): continue # no detections for this class?
    if objects:
        for d in objects :
            rect=(int(d.x()/rid), d.y(), int(d.w()/rid), d.h())
            img.draw_rectangle(rect,color=(255,255,0))
            #img.draw_string(int(d.x()/rid), d.y()-15, "face %.3f"%(d.output()))
        m_object=find_max_object(objects=objects,mode=1)
        max_object=(int(m_object[0]/rid),m_object[1], int(m_object[2]/rid), m_object[3],m_object[4])
        if max_object[4]>0.75: object_s=15000/(max_object[2]*2) #计算距离
    return object_s,max_object

#功能： 目标追踪
#输入： 图像，目标类型，控制模式
#输出： 无
def object_traking(img,mode=1):
    global flag_lost
    object_s=0
    max_object=None
    object_s,max_object=face_detect(img)
    if(object_s>0):
        flag_lost=0 #丢失清空
        cx =int(max_object[0]+max_object[2]/2)
        cy =int(max_object[1]+max_object[3]/2)
        print("object_s: ", object_s)
        pan_error =img.width()/2-cx
        tilt_error =img.height()/2-cy #计算目标位置偏差
        print("pan_error: ", pan_error)
        print("tilt_error: ", tilt_error)
        pan_output=pan_pid.get_pid(pan_error,1)/2 #计算PID跟随
        tilt_output=tilt_pid.get_pid(tilt_error,1)/2
        tilt_servo.angle(tilt_servo.angle()-tilt_output) #云台上下追踪
        pan_servo.angle(pan_servo.angle()+pan_output) #云台左右
    else: #目标丢失计数
        flag_lost=flag_lost+1
        if flag_lost>5:#连续5帧没有目标
            pan_servo.angle(0) #舵机回中
            tilt_servo.angle(-30) #上仰方便看到人脸


def car_state_deal(img):
    carstate,cardir,left_speed,right_speed,s_flag=ble.bluetooth_deal()
    if (carstate==CARSTATE.enFLITING or carstate==CARSTATE.enMANUAL): #控制舵机
        if(cardir==CARSTATE.enRUN):  #舵机向上
            tilt_servo.angle(tilt_servo.angle()-2)
        elif(cardir==CARSTATE.enBACK): #舵机向下
            tilt_servo.angle(tilt_servo.angle()+2)
        elif(cardir==CARSTATE.enLEFT): #舵机向左
            pan_servo.angle(pan_servo.angle()+2)
        elif(cardir==CARSTATE.enRIGHT):#舵机向右
            pan_servo.angle(pan_servo.angle()-2)
    elif (carstate==CARSTATE.enSTRAKING):
        object_traking(img,mode=1)#舵机追踪
    elif(carstate==CARSTATE.enTRACING):#寻迹
        object_traking(img,mode=1)#舵机追踪
    elif(carstate==CARSTATE.enTRAKING):
        object_traking(img,mode=1)#舵机追踪
    elif(carstate==CARSTATE.enAVOIDING): #避障模式暂无功能
        pan_servo.angle(0)
        tilt_servo.angle(0)

sensor.reset()
#sensor.set_contrast(1)
#sensor.set_brightness(1)
sensor.set_framesize(sensor.QVGA)
#sensor.set_quality(90)
sensor.set_pixformat(sensor.RGB565)
#sensor.set_hmirror(True) #水平镜像，方便调试
#sensor.set_vflip(True) #不同的摄像头需要设置一下旋转镜像才能正常跟踪
sensor.skip_frames(50)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()


while(True):
  clock.tick()
  img = sensor.snapshot()
  car_state_deal(img=img)
  lcd.display(img)
  print(clock.fps(), "fps", end="\n\n")
  gc.collect()
