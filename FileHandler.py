import time
import os
from PIL import Image
import json
import ImageUploading , TFLightbox

targetDir = "/home/pi/Documents/PAD_Data/"
#targetDir = "./PAD/"

def uploadImgDir():
  ImageUploading.uploadFormatedDir()

def getBriefData(defaults='PAD'):
  tests = ImageUploading.getBriefData('tests')
  samples = ImageUploading.getBriefData('samples')
  categories = ImageUploading.getBriefData('categories')
  if defaults == 'PAD':
    return {'tests':tests, 'samples':samples, 'categories':categories}
  elif defaults == 'Herbs':
    herbs = ['Alum (Granules)', 'Anise Seed', 'Annatto Seed (Gluten-free)', 'Bay Leaf (Whole Organic)', 'Beet Powder (Organic)', 'Burdock Root', 'Caraway Seed', 'Cardamom (Ground)', 'Catnip', 'Cayenne (35,00 HU w/Silicon Dioxide)', 'Celery Seed (Whole)', 'China Green Tea (Organic)', 'Chives', 'Cilantro (Organic)', 'Cinnamon (Ground)', 'Cloves', 'Cocao', 'Collagen Peptides', 'Coriander (Ground)', 'Cornsilk', 'Cream of Tartar', 'Cumin (Ground)', 'Dandelion Root', 'Dill Seed (Organic)', 'Eucalyptus', 'Fennel Seed (Whole)', 'Garlic Powder (Organic)', 'Ginger Root (Ground)', 'Hibiscus Petals (0rganic)', 'Horseradish Root (Powder)', 'Hyssop (Organic)', 'Jamain Allspice', 'Kale', 'Lavendar', 'Lemon Peel (Organic)', 'Majoram Leaf', 'Matcha Green Tea', 'Moringa', 'Nutmeg (Ground)', 'Oregano', 'Paprika (Ground)', 'Parsley', 'Pau D\'Arco', 'Peppermint', 'Poppy Seed', 'Psyllium Husk', 'Red Clover', 'Rooibos Tea (Organic Fair Trade)', 'Rosemary', 'Sage (Crushed)', 'Sencha Tea (Organic)', 'Senna Leaf', 'Slippery Elm (Organic/ Powdered Inner Bark)', 'Spearmint', 'Spirulina', 'Spirulina (Capsules)', 'Stevia Leaf (Organic)', 'Stinging Nettle', 'Sweet Basil Leaf ', 'Tarragon', 'Thyme', 'Tumeric Root', 'Valerian', 'Weat Grass', 'Wheat Grass (Organic)', 'White Peony Tea (Organic)', 'White Pepper (Organic Ground)', 'Yarrow Flowers (Organic)', 'Yeast (Nutritional)', 'Yellow Mustard']
    return {'tests':tests, 'samples':herbs, 'categories':categories}
  elif defaults == 'PADTemp':
    samplesTemp = ['Amoxicillin', 'Amoxicillin clavulonic acid', 'Ampicillin', 'Azithromycin', 'Benzyl Penicillin', 'Ceftriaxone', 'Chloroquine', 'Ciprofloxacin', 'Corn Starch', 'DI water', 'Doxycycline', 'Enalapril', 'Isoniazid', 'Losartan', 'Metformin', 'Paracetamol', 'Penicillin Procaine',  'Quinine', 'Tap water', 'Unknown']
    return {'tests':tests, 'samples':samplesTemp, 'categories':categories}

def getData(defaults='PAD'):
  tests = ImageUploading.getData('tests')
  samples = ImageUploading.getData('samples')
  categories = ImageUploading.getData('categories')
  return {'tests':tests, 'samples':samples, 'categories':categories}

def getSavedSamples():
  openDir(targetDir)
  return os.listdir(targetDir)

def getSavedSampleInstances(sample):
  directory = targetDir+sample+"/"
  if os.path.exists(directory):
    return os.listdir(directory)
  else:
    return None

def getSavedImage(instance, sample):
  return targetDir+sample+"/"+instance+"/processed.jpg"

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

def uploadImage(instance, sample2):
  directory = targetDir+sample2+"/"+instance+"/"
  if os.path.exists(directory):
    data = ImageUploading.getMetadata(directory+"data.json")
    file1 = directory+"processed.jpg"
    file2 = directory+"raw.jpg"
    sample = data['sample_name']
    test = data['test_name']
    category = data['category_name']
    idnum = sample2
    data['uploaded'] = ImageUploading.postData(file1, file2, sample, test, category, idnum)
    saveMetaData(data, instance=instance, sample=sample2)


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