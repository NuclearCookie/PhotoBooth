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
import pysftp

eventName = "Bram_Nancy"
assetLocation = '/home/photokanon/PhotoBooth/assets/';
saveLocation = f'/home/photokanon/Documents/PhotoBooth/PhotoboothPictures/{eventName}/';

img1 = Image.open(assetLocation + 'number1.png')
img2 = Image.open(assetLocation + 'number2.png')
img3 = Image.open(assetLocation + 'number3.png')
imgCalibrating = Image.open(assetLocation + 'calibrating.png')
credentials = [x.strip() for x in open("credentials.txt", "r").readlines()]

photo1 = "001.jpg"
photo2 = "002.jpg"
photo3 = "003.jpg"
photo4 = "004.jpg"

overlay_renderer = False

buttonEvent = False

# :TODO: update flash to use flash_mode instead? (professional flash timings)
# https://forums.raspberrypi.com/viewtopic.php?t=165910
# https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.flash_mode

flash = LED(26)
button = Button(17)
button_led = PWMLED(21)
button_led.pulse()
use_flash = True

camera = PiCamera()
# camera.resolution = (3280,2464)
camera.resolution = (2592,1944)
camera.framerate = 15

def addImageOverlay(image, layer):
    pad = Image.new('RGBA',(
        ((image.size[0]+31)//32)*32,
        ((image.size[1]+15)//16)*16,
        ))
    pad.paste(image, (0,0), image)

    overlay = camera.add_overlay(pad.tobytes(), size=image.size)
    overlay.layer = 0
    return overlay

# Black bars behind preview?
bb = Image.new('RGB',(
        ((1280+31)//32)*32,
        ((760+15)//16)*16,
        ))
# draw = ImageDraw.Draw(bb)
# draw.rectangle([0, 0, 32, 32], "black")
bbOverlay = camera.add_overlay(bb.tobytes(), size=bb.size)
bbOverlay.layer = 1


a = addImageOverlay(img1, 3)
b = addImageOverlay(img2, 4)
c = addImageOverlay(img3, 5)
calibrateOverlay = addImageOverlay(imgCalibrating, 6)


def setup():
    print("Welcome to the photo booth")
    if not os.path.exists(saveLocation):
        os.makedirs(saveLocation)
    camera.start_preview(resolution=(1013, 760), hflip=True, alpha=255) # keep same AR as the actual capture
    button.when_pressed = takePictures
    if len(sys.argv) > 1:
        if '--noflash' in sys.argv:
            global use_flash
            use_flash = False
        if '--instant' in sys.argv:
            takePictures()
            return 1
    return 0

def loop():
    while True:
        time.sleep(0.1)

def destroy():
    toggleFlash(False);
    camera.stop_preview()

def takePictures():
    print("Taking pictures!")
    datetime = time.strftime("%Y%m%d-%H%M%S")
    fileName = datetime +".jpg"
    camera.annotate_text = ''
    calibrateAwb()
    flashProcedure()
    one = captureImage(photo1, datetime)
    flashProcedure()
    two = captureImage(photo2, datetime)
    flashProcedure()
    three = captureImage(photo3, datetime)
    flashProcedure()
    four = captureImage(photo4, datetime)
    toggleFlash(False)
    montagePath = convertMergeImages(fileName, one, two, three, four)
    try: # not sure what will happen if some WIFI blocks the upload, so just try catch for safety.
        uploadMontage(montagePath)
    except Exception as e:
        print("Something went wrong when uploading the montage.")
        print(e)
    #printPic(fileName)
    # camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def convertMergeImages(fileName, one, two, three, four):
    print(f"Creating montage {fileName} from {one}, {two}, {three}, {four}")
    outputFile = saveLocation + fileName
    subprocess.call([
        "montage",
        "-monitor",
        one,
        two,
        three,
        four,
        "-geometry", "512x384+5+5",
        outputFile
        ])
    subprocess.call([
        "montage",
        "-monitor",
        outputFile,
        assetLocation + "banner.jpg",
        "-tile", "1x2",
        "-geometry", "+5+5",
        outputFile
    ])
    return outputFile

def uploadMontage(montagePath):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None # Not advised, but we're only uploading to this server. if there would be a Man in the Middle attack, we'd still only upload to the wrong target. No biggy.
    print("start uploading montage.")
    with pysftp.Connection(credentials[0], username=credentials[1], password=credentials[2], cnopts=cnopts) as sftp:
        with sftp.cd(f'photobooth/galleries/{eventName}'):
            sftp.put(montagePath)
    print("Done uploading montage.")
    subprocess.call([
        "perl",
        "remote_sync.pl",
        f"--base_url={credentials[3]}",
        f"--username={credentials[4]}",
        f"--password={credentials[5]}"
    ])

# def printPic(fileName):
#     addPreviewOverlay(100,200,55,"Printing")
#     conn = cups.Connection()
#     printers = conn.getPrinters()
#     default_printer = list(printers.keys())[0]
#     cups.setUser('pi')
#     conn.printFile (default_printer, saveLocation + fileName, "hl110",{'fit-to-page':'True'})

def calibrateAwb():
    calibrateOverlay.layer = 3
    toggleFlash(True)
    sleep(2)
    gains = camera.awb_gains
    print(f"Saving awb gains: {gains}")
    camera.awb_mode = 'off' # This should save the current awb gains?
    camera.awb_gains = gains
    toggleFlash(False)
    calibrateOverlay.layer = 0

def flashProcedure():
    toggleFlash(True)
    c.layer = 4
    sleep(0.5)
    toggleFlash(False)
    c.layer = 0
    sleep(0.5)
    toggleFlash(True)
    b.layer = 4
    sleep(0.5)
    toggleFlash(False)
    b.layer = 0
    sleep(0.5)
    toggleFlash(True)
    a.layer = 4
    sleep(0.5)
    a.layer = 0

def toggleFlash(state):
    if use_flash == False:
        return
    flash.value = int(state == True)

def captureImage(imageName, timestamp):
    imageName = saveLocation + timestamp + imageName;
    print(f"Capturing picture with awb: {camera.awb_gains}")
    camera.capture(imageName)
    toggleFlash(False)
    # An attempt at hijacking the black bars overlay to create a shutter effect. Doesn't look good.
    # bbOverlay.layer = 5
    # sleep(0.5)
    # bbOverlay.layer = 1
    return imageName

# def addPreviewOverlay(xcoord,ycoord,fontSize,overlayText):
#     global overlay_renderer
#     img = Image.new("RGBA" , (640,480))
#     draw = ImageDraw.Draw(img)
#     draw.text((xcoord, ycoord), overlayText, (255, 20, 147))

#     if not overlay_renderer:
#         overlay_renderer = camera.add_overlay(img.tobytes(),
#                                               layer=3,
#                                               size=img.size,
#                                               alpha=255);
#     else:
#         overlay_renderer.update(img.tobytes())


if __name__ == '__main__' :
    result = setup()
    if result is not 0:
        destroy()
    else:
        try:
            loop()
        # except KeyboardInterrupt: # When Ctrl + C is pressed, execute this
        finally:
            destroy()
