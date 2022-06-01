from picamera import PiCamera
import RPi.GPIO as GPIO
import time
from time import sleep
from gpiozero import LED
from PIL import Image, ImageDraw, ImageFont
import datetime as dt
import itertools
import cups
import subprocess
import os
from shutil import copyfile
import sys
import time

assetLocation = '/home/photokanon/PhotoBooth/assets/';
saveLocation = '/home/photokanon/Documents/PhotoBooth/PhotoboothPictures/';

img1 = Image.open(assetLocation + 'number1.png')
img2 = Image.open(assetLocation + 'number2.png')
img3 = Image.open(assetLocation + 'number3.png')


photo1 = "001.jpg"
photo2 = "002.jpg"
photo3 = "003.jpg"
photo4 = "004.jpg"

overlay_renderer = False

buttonEvent = False

        
flash = LED(26)
camera = PiCamera()
# camera.resolution = (3280,2464)
camera.resolution = (2592,1944)
camera.framerate = 15
number_pin_button = 17

pad = Image.new('RGB',(
    ((img1.size[0]+31)//32)*32,
    ((img1.size[1]+15)//16)*16,
    ))
pad.paste(img1, (0,0))

a = camera.add_overlay(pad.tobytes(), size=img1.size)
a.alpha = 0
a.layer = 3

pad = Image.new('RGB',(
    ((img2.size[0]+31)//32)*32,
    ((img2.size[1]+15)//16)*16,
    ))
pad.paste(img2, (0,0))

b = camera.add_overlay(pad.tobytes(), size=img2.size)
b.alpha = 0
b.layer = 4

pad = Image.new('RGB',(
    ((img3.size[0]+31)//32)*32,
    ((img3.size[1]+15)//16)*16,
    ))
pad.paste(img3, (0,0))

c = camera.add_overlay(pad.tobytes(), size=img3.size)
c.alpha = 0
c.layer = 5

class BlinkingLed:
    def __init__(self):
        self.counter = 0
        self.number_pin = 21
        self.ascending = True
        
    def initialize(self):
        GPIO.setup(self.number_pin, GPIO.OUT)
        self.led = GPIO.PWM(self.number_pin, 100)
        self.led.start(0)
    
    def update(self):
        '''
            limit * multiplier = 100, otherwise this does not work
        '''
        limit = 25;
        multiplier = 4;
        if self.ascending:
            self.counter += 1
        else:
            self.counter -= 1
        if self.counter <= 0:
            self.ascending = True
        elif self.counter >= limit:
            self.ascending = False
        
        self.led.ChangeDutyCycle(min(max(self.counter*multiplier, 0.0), 100.0))
        
blinking_led = BlinkingLed()

def play():
    print("Welcome to the photo booth")
    if not os.path.exists(saveLocation):
        os.makedirs(saveLocation)
    camera.start_preview(resolution=(1280, 720))
    camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    camera.annotate_text_size = 80
    blinking_led.initialize()
    if len(sys.argv) > 1 and sys.argv[1] == "--instant":
        takePictures()
        return


    while True:
        try:
            time.sleep(0.1)
            blinking_led.update();
            if waitForButtonPress(number_pin_button):
                takePictures()
                
        except KeyboardInterrupt:
            GPIO.cleanup()
            camera.stop_preview()
            break
        
def waitForButtonPress(number_pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(number_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    input_state = GPIO.input(number_pin)
    return input_state == False

def takePictures():
    fileName = time.strftime("%Y%m%d-%H%M%S")+".jpg"
    camera.annotate_text = ''
    flashProcedure()
    captureImage(photo1)
    flashProcedure()
    captureImage(photo2)
    flashProcedure()
    captureImage(photo3)
    flashProcedure()
    captureImage(photo4)
    flash.off()
    convertMergeImages(fileName)
    #printPic(fileName)
    camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def convertMergeImages(fileName):
    subprocess.call([
        "montage", 
        saveLocation + photo1, 
        saveLocation + photo2, 
        saveLocation + photo3, 
        saveLocation + photo4, 
        "-geometry", "512x384+5+5", 
        saveLocation + fileName
        ])
    subprocess.call([
        "montage",
        saveLocation + fileName, 
        assetLocation + "banner.jpg",
        "-tile", "1x2",
        "-geometry", "+5+5",
        saveLocation + fileName
    ])

def printPic(fileName):
    addPreviewOverlay(100,200,55,"Printing")
    conn = cups.Connection()
    printers = conn.getPrinters()
    default_printer = list(printers.keys())[0]
    cups.setUser('pi')
    conn.printFile (default_printer, saveLocation + fileName, "hl110",{'fit-to-page':'True'})

def flashProcedure():
    flash.on()
    c.alpha = 128
    sleep(0.5)
    flash.off()
    c.alpha = 0
    sleep(0.5)
    flash.on()
    b.alpha = 128
    sleep(0.5)
    flash.off()
    b.alpha = 0
    sleep(0.5)
    flash.on()
    a.alpha = 128
    sleep(0.5)
    a.alpha = 0

def captureImage(imageName):
    camera.capture(saveLocation + imageName)
    flash.off()

def addPreviewOverlay(xcoord,ycoord,fontSize,overlayText):
    global overlay_renderer
    img = Image.new("RGB" , (640,480))
    draw = ImageDraw.Draw(img)
    draw.text((xcoord, ycoord), overlayText, (255, 20, 147))
    
    if not overlay_renderer:
        overlay_renderer = camera.add_overlay(img.tobytes(),
                                              layer=3,
                                              size=img.size,
                                              alpha=128);
    else:
        overlay_renderer.update(img.tobytes())

play()

