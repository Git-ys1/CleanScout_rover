import sensor, image, time,math
from pid import PID
from pyb import Servo
from pyb import UART,Pin,Timer
CLAW_OFFSET=25
CLAW_RELEASE=-70
CLAW_CATCH=50
def obj_distance(obj_Lm):
	distance=36000/(obj_Lm*2)
	return distance
def find_max(blobs):
	max_size=0
	for blob in blobs:
		if blob[2]*blob[3] > max_size:
			max_blob=blob
			max_size = blob[2]*blob[3]
	return max_blob
ball_s=0
pan_servo=Servo(3)
tilt_servo=Servo(4)
claw_servo=Servo(1)
claw_servo.angle(CLAW_RELEASE)
pan_servo.angle(0)
tilt_servo.angle(0)
yellow_threshold=[(58, 86, 7, 53, 33, 80),(22, 50, 21, 55, 37, 66)]
pan_pid = PID(p=0.05, i=0.0 ,imax=90)
tilt_pid = PID(p=0.04, i=0.0, imax=90)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(10)
clock = time.clock()
while(True):
	clock.tick()
	img = sensor.snapshot()
	blobs = img.find_blobs(yellow_threshold)
	if blobs:
		max_blob = find_max(blobs)
		ball_s=27000/(max_blob[2]*2)
		print("ball_s:",ball_s)
		if(ball_s>=90 and ball_s<100):
			tilt_servo.angle(tilt_servo.angle()-CLAW_OFFSET/2,500)
			time.sleep(1000)
			claw_servo.angle(CLAW_CATCH)
			time.sleep(500)
			tilt_servo.angle(0,500)
			time.sleep(500)
			pan_servo.angle(0,500)
			time.sleep(500)
			claw_servo.angle(CLAW_RELEASE)
		if(ball_s>=100):
			claw_servo.angle(CLAW_RELEASE)
			pan_error =img.width()/2-max_blob.cx()
			tilt_error = img.height()/2+CLAW_OFFSET-max_blob.cy()
			img.draw_rectangle(max_blob.rect())
			img.draw_cross(max_blob.cx(), max_blob.cy())
			pan_output=pan_pid.get_pid(pan_error,1)/2
			tilt_output=tilt_pid.get_pid(tilt_error,1)
			pan_servo.angle(pan_servo.angle()+pan_output)
			tilt_servo.angle(tilt_servo.angle()-tilt_output)