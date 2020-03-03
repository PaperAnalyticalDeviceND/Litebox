import time
import os
from PIL import Image
from YIP3 import unGodlyHack

base_prefix = "/home/pi/Documents/Yeast_Data/"
#base_prefix = "./Yeast_Data/"

def openDir(directory):
  directory = os.path.dirname(directory)
  if not os.path.exists(directory):
    os.makedirs(directory)

def saveYeastWhiteImage(image, yeastImage, data = None):
  cTime = time.gmtime()
  cTime = time.strftime("%Y_%m_%d_%H:%M:%S", cTime)
  prefix = base_prefix
  prefix += cTime+"/"
  openDir(prefix)
  img = Image.fromarray(image)
  img = img.rotate(90)
  img.save(prefix+"white.tiff")
  if data is not None:
    dataFile = open(prefix+"data.txt", 'w')
    dataFile.write(data)
  yeastImage = Image.fromarray(yeastImage)
  yeastImage = yeastImage.rotate(90)
  saveYeastImage(yeastImage, prefix = prefix)
  finalImage = unGodlyHack(prefix)
  finalImage = Image.fromarray(finalImage)
  saveYeastImage(finalImage, name = 'green_processed.tiff', prefix = prefix)

def saveYeastImage(yeastImage, name='green.tiff', prefix=None):
  if prefix is None:
    cTime = time.gmtime()
    cTime = time.strftime("%Y_%m_%d_%H:%M:%S", cTime)
    prefix = base_prefix
    openDir(prefix)
    prefix += cTime+"_"
  yeastImage.save(prefix+name)
