import sensor,image,time,math
from pid import PID
from pyb import Servo,UART,Pin,Timer

############################机械臂驱动部分############################

#控制左右接D14
#控制上下接D15
#控制抓取接B10
#调试时先接一个舵机，将其调试好再接另外一个，不同的摄像头通过控制翻转和镜像进行调试
#不同的目标和不同的摄像头对应的颜色阈值不同，需要使用阈值标定工具进行重新标定才能正常识别

#0度----0.5/20*100=2.5;(要看实际的舵机是否支持0度，一般运动不到0度，需要把这个值调大一点)
#45度----1.0/20*100=5;
#90度----1.5/20*100=7.5;
#135度----2.0/20*100=10;
#180度----2.5/20*100=12.5;
# 生成50HZ方波，使用TIM2，channels 3
#控制舵机需要输出2.5%-12.5%的PWM
tim = Timer(2, freq=50) # Frequency in 50Hz(20ms)
claw=tim.channel(3, Timer.PWM, pin=Pin("B10"), pulse_width_percent=7.5)   #初始角度90度
#定义机械爪舵机运动角度
#输入：舵机运动到目标角度
#输出：无
def claw_angle(servo_angle):
    if servo_angle<=0:
        servo_angle=0
    if servo_angle>=180:
        servo_angle=180
    percent=(servo_angle+45)/18
    claw.pulse_width_percent(percent)

#功能：目标距离计算
#输入：目标宽度或直径，单位：像素值
#输出：距离 mm
#note:不同的镜头焦距和摄像头芯片对应的距离参数不同，具体可配合超声波测距模块进行距离参数标定
def obj_distance(obj_Lm):
    distance= 8000/obj_Lm   #OV2640 DVP高清，M12接口摄像头
    return int(distance)
#功能：寻找最大的色块，计算方式为像素面积排序
#输入： 色块链表blobs，中心坐标X(blob[0]),中心坐标y(blob[1]),（像素宽）blob[2],（像素高）blob[3],
#输出： 最大色块max_blob
def find_max(blobs):
    max_size=0
    for blob in blobs:
        if blob[2]*blob[3] > max_size:
            max_blob=blob
            max_size = blob[2]*blob[3]
    return max_blob


ball_s=0
global count
count=0
pan_servo=Servo(3)    #左右控制
tilt_servo=Servo(4)  #上下控制
#//OV2640
#color_thresholds=[(53, 99, -13, 46, 29, 57),   #黄色
#                  (38, 76, 22, 59, 0, 28),      #红色
#                  (33, 80, -31, 18, -56, -21)]      #蓝色

yellow_threshold= [(53, 99, -13, 46, 29, 57)]#黄色
red_threshold = [(38, 76, 22, 59, 0, 28)] #红色
blue_threshold = [(33, 80, -31, 18, -56, -21)] #蓝色

pan_pid = PID(p=0.09, i=0.0 ,imax=90)#在线调试使用这个PID
tilt_pid = PID(p=0.09, i=0.0, imax=90)#在线调试使用这个PID

sensor.reset()
sensor.set_pixformat(sensor.RGB565)         #设置图像格式RGB565
sensor.set_framesize(sensor.QVGA)           #设置分辨率320x240
#sensor.set_hmirror(True)                    #控制镜像
#sensor.set_vflip(True)                      #控制水平翻转
sensor.skip_frames(20)
sensor.set_auto_whitebal(False)
clock = time.clock()
claw_angle(60)
count=0
h_error=-30
tilt_servo.angle(30)
pan_servo.angle(90)

while(True):
    clock.tick()
    img = sensor.snapshot()
    max_size0=0
    max_size1=0
    max_size2=0
    color_num=0
    blobs0 = img.find_blobs(red_threshold,pixels_threshold=500)
    if blobs0:
        max_blob = find_max(blobs0)
        color_num=1
    else :
        blobs1 = img.find_blobs(yellow_threshold,pixels_threshold=500)
        if blobs1:
            max_blob = find_max(blobs1)
            color_num=2
        else :
            blobs2 = img.find_blobs(blue_threshold,pixels_threshold=500)
            if blobs2:
                max_blob = find_max(blobs2)
                color_num=3
    if color_num>0:
        img.draw_rectangle(max_blob.rect())
        img.draw_cross(max_blob.cx(), max_blob.cy())
        ball_s=obj_distance((max_blob[2]+max_blob[3])/2) #计算距离
        pan_error=0
        tilt_output=0
        print("ball_s: ", ball_s)

        ############################抓取############################
        if(ball_s>=60 and ball_s<=110):
            tilt_error = (img.height()/2+h_error)-max_blob.cy()
            tilt_output=tilt_pid.get_pid(tilt_error,1)
            #捡球时关闭左右追踪
            print("color_num: ",color_num)
            #pan_servo.angle(pan_servo.angle()+pan_output)
            tilt_servo.angle(tilt_servo.angle()-tilt_output)
            if tilt_output<=0.5:
                count=count+1
                if count >=5:
                    count=0
                    claw_angle(150)        #夹取
                    time.sleep(1000)
                    tilt_servo.angle(0)   #上升
                    time.sleep(1000)
                    if (color_num==1):
                        pan_servo.angle(45)    #运动到目标位置
                    elif (color_num==2):
                        pan_servo.angle(0)    #运动到目标位置
                    else :
                        pan_servo.angle(-45)    #运动到目标位置
                    time.sleep(1000)
                    tilt_servo.angle(35)   #下降
                    time.sleep(1000)
                    claw_angle(60)         #放下
                    time.sleep(1000)
                    tilt_servo.angle(0)  #回到初始位置
                    time.sleep(1000)
                    pan_servo.angle(90)     #回到初始位置
                    time.sleep(1000)
        if(ball_s>110):
            ############################云台追踪############################
            claw_angle(60)
            pan_error = img.width()/2-max_blob.cx()
            tilt_error =(img.height()/2+h_error)- max_blob.cy()
            print("pan_error: ", pan_error)
            pan_output=pan_pid.get_pid(pan_error,1)/2
            tilt_output=tilt_pid.get_pid(tilt_error,1)
            #不做左右追踪
            pan_angle=pan_servo.angle()+pan_output
            tilt_angle=tilt_servo.angle()-tilt_output
            #对上下追踪做限幅
            if tilt_angle>60:
              tilt_angle=60
            if tilt_angle<-60:
              tilt_angle=-60
           # pan_servo.angle(pan_angle)
            tilt_servo.angle(tilt_angle)
    else:
        #没有目标
        pan_servo.angle(90)
        tilt_servo.angle(30)
        claw_angle(60)

