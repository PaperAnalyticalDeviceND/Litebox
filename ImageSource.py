import threading
import Queue
import cv2
import subprocess

testImageSource = '/Users/Diyogon/Documents/ND/Lightbox/temp2.png'
white = '255 255 255 255'
green = '0 255 0 0'
black = '0 0 0 0'

class imageSource():
  def __init__(self, os=None, testing=False, yeast=False):
    self.running = False
    self.picQueue = Queue.Queue()
    self.capture_thread = None
    self.os = os
    self.testing = testing
    self.yeast = yeast

  def setSize(self, height, width):
    self.height = height
    self.width = width

  def controlLED(self, color):
    if self.os == 'Linux':
      command = "sudo python /home/pi/Documents/LED_control.py "
      subprocess.call(command+color, shell=True)

  def startCapture(self, g=False):
    self.capture_thread = threading.Thread(target=self.grab, args = (0, 1296, 976, 2, g))
    self.capture_thread.start()
    self.running = True
    if g:
      self.controlLED(green)
    else:
      self.controlLED(white)

  def stopCapture(self):
    self.running = False
    self.controlLED(black)

  def testGrab(self, cam, width, height, fps):
    while self.running:
      frame = {}
      frame["img"] = cv2.imread(testImageSource, 1)
      if self.picQueue.qsize() < 10:
        self.picQueue.put(frame)

  def macGrab(self, cam, width, height, fps):
    capture = cv2.VideoCapture(cam)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)

    while(self.running):
      frame = {}
      capture.grab()
      retval, img = capture.retrieve(0)
      frame["img"] = img
      if self.picQueue.qsize() < 10:
        self.picQueue.put(frame)

  def piGrab(self, cam, width, height, fps, g):
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    try:
      camera = PiCamera()
    except Exception as e:
      print(e)
    camera.resolution = (width, height)
    camera.framerate = fps
    if g:
      print("Adjusting camera for fluorescence")
      camera.exposure_mode = 'fireworks'
      camera.awb_mode = 'sunlight'
      camera.iso = 400
      camera.shutter_speed = 500000
      camera.meter_mode = 'average'
    rawCapture = PiRGBArray(camera, size=(width, height))
    for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        frame = {}
        image = f.array
        frame["img"] = image
        if self.picQueue.qsize() < 10:
          self.picQueue.put(frame)
        rawCapture.truncate(0)
        if not self.running:
          break
    camera.close()

  def grab(self, cam, width, height, fps, g=False):
    if self.testing:
      print("Running testmode")
      self.testGrab(cam, width, height, fps)
    elif self.os == 'Darwin':
      print("Running darwin")
      self.macGrab(cam, width, height, fps)
    elif self.os == 'Linux':
      print("Running linux")
      self.piGrab(cam, width, height, fps, g)
    else:
      print("Unknown os")

  def ready(self):
    return (self.running and not self.picQueue.empty())

  def rescaleToWindow(self, img):
    img_height, img_width, img_colors = img.shape
    scale_height = float(self.height)/float(img_height)
    scale_width = float(self.width)/float(img_width)
    img = cv2.resize(img, None, fx=scale_width, fy=scale_height, interpolation = cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

  def getImage(self):
    frame = self.picQueue.get()
    img = frame['img']
    return self.rescaleToWindow(img)