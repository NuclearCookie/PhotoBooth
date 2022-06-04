from picamera import PiCamera
import time
from time import sleep
from gpiozero import LED, Button, PWMLED
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
button = Button(17)
button_led = PWMLED(21)
button_led.pulse()
use_flash = True

camera = PiCamera()
# camera.resolution = (3280,2464)
camera.resolution = (2592,1944)
camera.framerate = 15

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

def setup():
    print("Welcome to the photo booth")
    if not os.path.exists(saveLocation):
        os.makedirs(saveLocation)
    camera.start_preview(resolution=(1280, 720))
    camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    camera.annotate_text_size = 80
    button.when_pressed = takePictures
    if len(sys.argv) > 1: 
        if sys.argv[1] == "--instant":
            takePictures()
            return
        elif sys.argv[1] == "--noflash":
            global use_flash
            use_flash = False

def loop():
    while True:
        time.sleep(0.1)

def destroy():
    toggleFlash(False);
    camera.stop_preview()

def takePictures():
    print("Taking pictures!")
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
    toggleFlash(False)
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
    toggleFlash(True)
    c.alpha = 128
    sleep(0.5)
    toggleFlash(False)
    c.alpha = 0
    sleep(0.5)
    toggleFlash(True)
    b.alpha = 128
    sleep(0.5)
    toggleFlash(False)
    b.alpha = 0
    sleep(0.5)
    toggleFlash(True)
    a.alpha = 128
    sleep(0.5)
    a.alpha = 0

def toggleFlash(state):
    if use_flash == False:
        return
    flash.value = int(state == True)

def captureImage(imageName):
    camera.capture(saveLocation + imageName)
    toggleFlash(False)

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


if __name__ == '__main__' :
    setup()
    try:
        loop()
    # except KeyboardInterrupt: # When Ctrl + C is pressed, execute this
    finally:
        destroy()
