import sensor,image,time,math
from pid import PID
from pyb import Servo,UART,Pin,Timer
ball_s=0
global count
count=0
CLAW_OFFSET=25
CLAW_RELEASE=-70
CLAW_CATCH=50
pan_servo=Servo(3)
tilt_servo=Servo(4)
claw_servo=Servo(1)
claw_servo.angle(CLAW_RELEASE)
pan_servo.angle(0)
tilt_servo.angle(0)
pan_servo.calibration(500, 2500, 1500)
tilt_servo.calibration(500, 2500, 1500)
def find_max(blobs):
	max_size=0
	for blob in blobs:
		if blob[2]*blob[3] > max_size:
			max_blob=blob
			max_size = blob[2]*blob[3]
	return max_blob
yellow_threshold= [(43, 85, -31, 55, 27, 84)]
red_threshold = [(38, 65, 54, 109, 34, 107)]
blue_threshold = [(10, 46, -26, 63, -82, -7)]
pan_pid = PID(p=0.05, i=0.0 ,imax=90)
tilt_pid = PID(p=0.05, i=0.0, imax=90)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.HQVGA)
sensor.skip_frames(20)
sensor.set_auto_whitebal(False)
clock = time.clock()
count=0
h_error=30
pan_servo.angle(90,2000)
time.sleep(2000)
tilt_servo.angle(30,2000)
while(True):
	clock.tick()
	img = sensor.snapshot()
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
		ball_s=13500/(max_blob[2]*2)
		pan_error=0
		tilt_output=0
		print("ball_s: ", ball_s)
		if(ball_s>=90 and ball_s<=110):
			print("color_num: ",color_num)
			tilt_error = (img.height()/2+CLAW_OFFSET)-max_blob.cy()
			tilt_output=tilt_pid.get_pid(tilt_error,1)
			tilt_servo.angle(tilt_servo.angle()-tilt_output)
			if tilt_output<=0.5:
				count=count+1
				if count >=5:
					count=0
					tilt_servo.angle(tilt_servo.angle(),500)
					time.sleep(1000)
					claw_servo.angle(CLAW_CATCH)
					time.sleep(1000)
					tilt_servo.angle(-10,1000)
					time.sleep(1000)
					if (color_num==1):
						pan_servo.angle(45,1000)
					elif (color_num==2):
						pan_servo.angle(0,1000)
					else :
						pan_servo.angle(-45,1000)
					time.sleep(1000)
					tilt_servo.angle(35,1000)
					time.sleep(1000)
					claw_servo.angle(CLAW_RELEASE)
					time.sleep(1000)
					tilt_servo.angle(0,1000)
					time.sleep(1000)
					tilt_servo.angle(0,1000)
					time.sleep(1000)
					pan_servo.angle(90,1000)
					time.sleep(1000)
		if(ball_s>110):
			claw_servo.angle(CLAW_RELEASE)
			pan_error = img.width()/2-max_blob.cx()
			tilt_error =(img.height()/2+h_error)- max_blob.cy()
			print("pan_error: ", pan_error)
			pan_output=pan_pid.get_pid(pan_error,1)/2
			tilt_output=tilt_pid.get_pid(tilt_error,1)
			pan_angle=pan_servo.angle()+pan_output
			tilt_angle=tilt_servo.angle()-tilt_output
			if tilt_angle>80:
			  tilt_angle=80
			if tilt_angle<-80:
			  tilt_angle=-80
			pan_servo.angle(pan_angle)
			tilt_servo.angle(tilt_angle)
	else:
		pan_servo.angle(90,500)
		tilt_servo.angle(30,500)
		claw_servo.angle(CLAW_RELEASE)
