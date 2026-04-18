import sensor, image, lcd,time 
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA2)
sensor.skip_frames(time = 2000)
lcd.init()
lcd.set_direction(0)
clock = time.clock()
while(True):
	clock.tick()
	img=sensor.snapshot()
	img.draw_string(0, 0, "FPS:%.2f"%(clock.fps()))
	lcd.display(img) 
	print(clock.fps())
