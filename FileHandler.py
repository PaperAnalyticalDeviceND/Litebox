import time
import os
from PIL import Image
import json
import ImageUploading, TFLightbox

targetDir = "/home/pi/Documents/PAD_Data/"
#targetDir = "./PAD/"

def getSavedSamples():
  openDir(targetDir)
  return os.listdir(targetDir)

def getSavedSampleInstances(sample):
  directory = targetDir+sample+"/"
  if os.path.exists(directory):
    return os.listdir(directory)
  else:
    return None

def getMetaData(instance, sample):
  directory = targetDir+sample+"/"+instance+"/data.json"
  if os.path.exists(directory):
    return ImageUploading.getMetadata(directory)
  else:
    return None

def readImage(instance, sample, system):
  directory = targetDir+sample+"/"+instance+"/processed.jpg"
  if os.path.exists(directory):
    return TFLightbox.readImage(directory, system)
  else:
    return None

def openDir(directory):
  directory = os.path.dirname(directory)
  if not os.path.exists(directory):
    os.makedirs(directory)

def saveMetaData(data, prefix=targetDir, instance=None, sample=None):
  if instance is not None:
    prefix += sample+'/'+instance+'/'
  with open(prefix+"data.json", "w") as output:
      json.dump([data], output)

def savePADImage(rawImage, PADImage, data, QR='Unknown'):
  cTime = time.gmtime()
  cTime = time.strftime("%Y_%m_%d_%H:%M:%S", cTime)
  prefix = targetDir+QR+'/'+cTime+"/"
  openDir(prefix)
  img = Image.fromarray(rawImage)
  img.save(prefix+"raw.jpg")
  img = Image.fromarray(PADImage)
  img.save(prefix+"processed.jpg")
  saveMetaData(data[0], prefix)
  return prefix

def saveYeastWhiteImage(image, yeastImage):
  cTime = time.gmtime()
  cTime = time.strftime("%Y_%m_%d_%H:%M:%S", cTime)
  prefix = targetDir+cTime+"/"
  openDir(prefix)
  img = Image.fromarray(image)
  img = img.rotate(90)
  img.save(prefix+"white.jpg")
  saveYeastImage(yeastImage, prefix)

def saveYeastImage(yeastImage, prefix=None):
  if prefix is None:
    cTime = time.gmtime()
    cTime = time.strftime("%Y_%m_%d_%H:%M:%S", cTime)
    prefix = targetDir+cTime+"/"
  openDir(prefix)
  img = Image.fromarray(yeastImage)
  img = img.rotate(90)
  img.save(prefix+"processed.jpg")