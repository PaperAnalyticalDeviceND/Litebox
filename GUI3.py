from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QAction, QMenuBar, QActionGroup, QMenu
from PyQt5.QtCore import QTimer, QRectF, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QImage, QFont
'''
from PyQt5.QtWidgets import , QPushButton, QApplication, QLabel, QFrame, QComboBox, QLabel, QMainWindow, QAction, QActionGroup, QMenuBar
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QRectF, QPoint, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QImage, QIcon'''
import sys
import ImageSource, ImageProcessing, FileHandler
import platform
import numpy as np

border_size = 20.0
default_test = '12LanePADKenya2015'
default_category = 'General'
default_sample = 'Amoxicillin'

def CenterWindow(widget, screenX, screenY, percent):
  width = percent*screenX
  topX = (screenX-width)/2
  height = percent*screenY
  topY = (screenY-height)/2
  widget.setGeometry(60, 30, width, height)

class ImageWidget(QWidget):
  def __init__(self, parent=None):
    super(ImageWidget, self).__init__(parent)
    if parent:
      self.setMinimumSize(parent.size())
    self.image = None
    self.color = QColor(0,200,0)

  def setImage(self, image):
    self.image = image
    self.setMinimumSize(image.size())
    self.update()

  def setColor(self, color):
    self.color = color
    self.update()

  def paintEvent(self, event):
    qp = QPainter()
    qp.begin(self)
    if self.image:
      qp.setBrush(self.color)
      qp.drawRect(0,0,self.image.width(), self.image.height())
      tX = self.image.width()-(3*border_size)
      tY = self.image.height()-(3*border_size)
      centerImage = self.image.scaled(QSize(tX, tY))
      qp.drawImage(QPoint(border_size,border_size), centerImage)
    qp.end()

class ScanWidget(QMainWindow):
  def __init__(self):
    super(QMainWindow, self).__init__()
    self.initVars()
    self.initUI()
    self.setUpImage()
    print("Hi mom!")

  def initVars(self):
    self.testing = False
    self.yeast = False
    self.os = platform.system()
    self.oldFiducials = []
    self.binFrames = 0
    self.foundYeast = False
    self.manualFoundYeast = False
    self.prefix = ""
    self.test = default_test
    self.drug = default_sample
    self.category = default_category

  def getData(self):
    data = {}
    if self.drugMenu.checkedAction() is None:
      data['sample_name'] = default_sample
    else:
      data['sample_name'] = self.drugMenu.checkedAction().text()
    if self.testMenu.checkedAction() is None:
      data['test_name'] = default_test
    else:
      data['test_name'] = self.testMenu.checkedAction().text()
    if self.categoryMenu.checkedAction() is None:
      data['category_name'] = default_category
    else:
      data['category_name'] = self.categoryMenu.checkedAction().text()
    data['uploaded'] = False
    return [data]

  def saveImage(self):
    print("Saving image")
    if not self.yeast:
      data = self.getData()
      self.prefix = FileHandler.savePADImage(self.rawImage, self.finalImage, data, self.qr)
    if self.yeast and self.foundYeast:
      FileHandler.saveYeastImage(self.finalImage)
    elif self.yeast and self.manualFoundYeast:
      FileHandler.saveYeastWhiteImage(self.whiteImage, self.finalImage)
    self.restartCapture()

  def runNN(self, parentMenu, instance, sample):
    drug, percent = FileHandler.readImage(instance, sample, self.os)
    data = FileHandler.getMetaData(instance, sample)
    data['sample_pred'] = drug
    FileHandler.saveMetaData(data, instance=instance, sample=sample)
    parentMenu.clear()
    self.buildMetaData(parentMenu, instance, sample)

  def setButtonVisibility(self, visibility):
    self.saveButton.setVisible(visibility)
    self.resetButton.setVisible(visibility)

  def initUI(self):
    CenterWindow(self, 800, 480, 1.2)
    self.setWindowTitle('PadScan')
    self.IWidget =  ImageWidget(self)
    self.saveButton = QPushButton("Save image", self)
    self.setupButton(self.saveButton, self.saveImage, 10, 20)
    self.resetButton = QPushButton("Discard image", self)
    self.setupButton(self.resetButton, self.restartCapture, 760, 20)
    self.label = QLabel("Image saved!", self)
    self.label.setFont(QFont("Arial", 20))
    self.label.move(375, 20)
    self.label.setStyleSheet("QLabel { color: white; }")
    self.label.adjustSize()
    self.label.setVisible(False)
    if self.yeast:
      self.takeButton = QPushButton("Take image", self)
      self.setupButton(self.takeButton, self.manualYeastImage, 400, 520)
      self.takeButton.setVisible(True)
    self.setUpMenu()
    self.show()

  def setDefaults(self, action):
    parentMenu = action.parentWidget()
    title = parentMenu.title()
    if title == 'Select Test':
      self.test = action.text()
    if title == 'Select Drug':
      self.drug = action.text()
    if title == 'Select Category':
      self.category = action.text()
    print(self.test, self.drug, self.category)

  def unholyHack(self, action):
    parentMenu = action.parentWidget()
    grandParentMenu = parentMenu.parent()
    if action.text() == 'No prediction':
      instance = parentMenu.title()
      sample = grandParentMenu.title()
      data = FileHandler.getMetaData(instance, sample)
      data['sample_pred'] = 'Processing...'
      FileHandler.saveMetaData(data, instance=instance, sample=sample)
      parentMenu.clear()
      self.buildMetaData(parentMenu, instance, sample)
      self.runNN(parentMenu, instance, sample)

    #print(action.text(), parentMenu.title(), grandParentMenu.title())

  def setUpMenu(self):
    mainmenu = self.menuBar()
    menu = mainmenu.addMenu('Set Defaults')
    self.testMenu = self.buildTestMenu(menu)
    self.drugMenu = self.buildDrugMenu(menu)
    self.categoryMenu = self.buildCategoryMenu(menu)
    reviewMenu = mainmenu.addMenu('Review Samples')
    self.setUpSubMenus(reviewMenu)

  def setUpSubMenus(self, menu):
    samples = FileHandler.getSavedSamples()
    for sample in samples:
      sampleInstances = FileHandler.getSavedSampleInstances(sample)
      if sampleInstances is not None:
        sampleMenu = QMenu(sample, menu)
        for instance in sampleInstances:
          instanceMenu = QMenu(instance, sampleMenu)
          self.buildMetaData(instanceMenu, instance, sample)
          sampleMenu.addMenu(instanceMenu)
        menu.addMenu(sampleMenu)

  def buildMetaData(self, menu, instance, sample):
    metadata = FileHandler.getMetaData(instance, sample)
    if metadata is not None:
      actionGroup = self.setUpMetaDataActions(menu, metadata)
      actionGroup.triggered.connect(self.unholyHack)

  def setUpMetaDataActions(self, menu, metadata):
    actionGroup = QActionGroup(menu)
    testName = 'Test not recorded'
    drugName = 'Drug not recorded'
    catName = 'Category not recorded'
    predName = 'No prediction'
    uploadName = 'Upload not recorded'
    if 'test_name' in metadata.keys():
      testName = 'Test = '+metadata['test_name']
    if 'sample_name' in metadata.keys():
      drugName = 'Drug = '+metadata['sample_name']
    if 'category_name' in metadata.keys():
      catName = 'Category = '+metadata['category_name']
    if 'sample_pred' in metadata.keys():
      predName = metadata['sample_pred']
    if 'uploaded' in metadata.keys():
      if metadata['uploaded'] is True:
        uploadName = 'Uploaded'
      else:
        uploadName = 'Not Uploaded'
    act = actionGroup.addAction(QAction(testName, menu))
    menu.addAction(act)
    act = actionGroup.addAction(QAction(drugName, menu))
    menu.addAction(act)
    act = actionGroup.addAction(QAction(catName, menu))
    menu.addAction(act)
    act = actionGroup.addAction(QAction(predName, menu))
    menu.addAction(act)
    act = actionGroup.addAction(QAction(uploadName, menu))
    menu.addAction(act)
    return actionGroup

  def buildTestMenu(self, menu):
    setTest = menu.addMenu('Select Test')
    tests = ['Acidic Cobalt Thiocyanate', 'Aspirin Test', 'Basic Cobalt Thiocyanate', 'Beta-lactam (Cu)', 'Biuret', 'Carbonate', 'Dimethylcinnamonaldehyde (DMCA)', 'Eosine Red', 'Eriochrome Black T K2CO3', 'Eriochrome Black T NaOH', 'Ethambutol (Cu)', 'Hemin', 'Iron (III) Chloride-Carbonate Test', 'Magic SNP', 'Naphthaquinone Sulfonate (NQS)', 'Ninhydrin', 'Nirophenols-HONO', 'Phenols-HONO and PNA', 'Pyridyl Pyridinium Chloride (PPC)', 'Rimani Test', 'Sodium Nitroprusside (SNP)', 'Timer', 'Triiodide Povidone', 'Turmeric', '12 Lane PAD Kenya 2014', 'SaltPAD', 'amPAD_Early', 'amPAD_Late', 'Sandipan1', '12LanePADKenya2015', 'dropbox', 'Lane G (SNP) for Clav standards', 'HPLC Comparison', '2017 Laos Antibiotic PAD', 'idPAD']
    #tests = ImageUploading.getData("tests")
    actionGroup = QActionGroup(setTest, exclusive=True)
    for test in tests:
      act = actionGroup.addAction(QAction(test, setTest, checkable=True))
      setTest.addAction(act)
      if(test == default_test):
        act.toggle()
    actionGroup.triggered.connect(self.setDefaults)
    return actionGroup

  def buildDrugMenu(self, menu):
    setTest = menu.addMenu('Select Drug')
    tests = ['Amoxicillin', 'Amoxicillin clavulonic acid', 'Ampicillin', 'Azithromycin', 'Benzyl Penicillin', 'Ceftriaxone', 'Chloroquine', 'Ciprofloxacin', 'Corn Starch', 'DI water', 'Doxycycline', 'Enalapril', 'Isoniazid', 'Losartan', 'Metformin', 'Paracetamol', 'Penicillin Procaine',  'Quinine', 'Tap water',   'Unknown']
    #tests = ImageUploading.getData("tests")
    actionGroup = QActionGroup(setTest, exclusive=True)
    for test in tests:
      act = actionGroup.addAction(QAction(test, setTest, checkable=True))
      setTest.addAction(act)
      if(test == default_test):
        act.toggle()
    actionGroup.triggered.connect(self.setDefaults)
    return actionGroup

  def buildCategoryMenu(self, menu):
    setCat = menu.addMenu('Select Category')
    #cats = ImageUploading.getData("categories")
    cats = ['Chris Test', 'General', '2016 PAD VALIDATION', '2017 Laos preparation', '2015-2016 USAID DIV project']
    actionGroup = QActionGroup(setCat, exclusive=True)
    for cat in cats:
      act = actionGroup.addAction(QAction(cat, setCat, checkable=True))
      setCat.addAction(act)
      if(cat == default_category):
        act.toggle()
    actionGroup.triggered.connect(self.setDefaults)
    return actionGroup

  def setupButton(self, button, program, x, y):
    button.setFont(QFont("Arial", 20))
    button.clicked.connect(program)
    button.move(x, y)
    button.adjustSize()
    button.setVisible(False)

  def setUpImage(self):
    self.imageSource = ImageSource.imageSource(self.os, self.testing, self.yeast)
    self.imageSource.setSize(self.frameSize().height(), self.frameSize().width())
    self.imageSource.startCapture()
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.updateFrame)
    self.timer.start(1)

  def mousePressEvent(self, QMouseEvent):
    userPoint = [QMouseEvent.pos().x(), QMouseEvent.pos().y(), 13, -1]
    posFiducials = self.oldFiducials[:]
    posFiducials.append(userPoint)
    self.oldFiducials = ImageProcessing.sortFiducials(posFiducials, self.oldFiducials)

  def manualYeastImage(self):
    self.imageSource.stopCapture()
    if not self.manualFoundYeast:
      self.whiteImage = self.imageSource.getImage()
      ImageProcessing.getQR(self.whiteImage)
      print("Restarting for yeast")
      self.restartCapture(green=True, reset=False)
      self.binFrames = 10
      self.manualFoundYeast = True
    else:
      self.finalImage = self.imageSource.getImage()
      self.saveImage()

  def correctYeastImage(self, img):
    self.imageSource.stopCapture()
    print("Correcting yeast")
    fiducials = np.asarray(self.oldFiducials)
    img, valid = ImageProcessing.rectifyImage(img, fiducials[:,:2])
    corrected, valid = ImageProcessing.correctComb(img, finX = self.frameSize().width(), finY = self.frameSize().height(), wax=self.wax)
    self.finalImage = corrected
    self.setImage(corrected)
    self.setButtonVisibility(True)

  def analyzeImage(self, img):
    self.imageSource.stopCapture()
    fiducials = np.asarray(self.oldFiducials)
    self.rawImage = img
    rectified, valid = ImageProcessing.rectifyImage(img, fiducials[:,:2])
    if valid:
      print("Got good fiducials")
      wax = ImageProcessing.findWax(rectified)
      corrected, resized, valid = ImageProcessing.correctComb(rectified, finX = self.frameSize().width(), finY = self.frameSize().height())
    else:
      self.oldFiducials = []
      self.restartCapture()
    if valid and not self.yeast:
      print("Getting qr")
      self.qr = ImageProcessing.getQR(rectified)
      print(self.qr)
      self.setImage(resized)
      self.finalImage = corrected
      self.setButtonVisibility(True)
    if valid and self.yeast:
      print("Restarting for yeast")
      self.restartCapture(green=True, reset=False)
      self.binFrames = 20
      self.wax = wax
      self.foundYeast = True

  def updateFrame(self):
    if self.imageSource.ready():
      image = self.imageSource.getImage()
      if self.binFrames == 0:
        if self.manualFoundYeast:
          self.setImage(image)
        elif self.foundYeast:
          self.correctYeastImage(image)
        else:
          processedImage, self.oldFiducials = ImageProcessing.ProcessImage(image, oldFiducials = self.oldFiducials)
          if len(self.oldFiducials) == 6:
            self.analyzeImage(image)
          else:
            self.setImage(processedImage)
      elif self.binFrames > 0:
        self.binFrames -= 1
        self.setImage(image)
    
  def setImage(self, img):
    height, width, bpc = img.shape
    bpl = bpc * width
    self.image = QImage(img.data, width, height, bpl, QImage.Format_RGB888)
    self.IWidget.setImage(self.image)

  def restartCapture(self, green=False, reset=True):
    self.setButtonVisibility(False)
    if reset:
      self.initVars()
      self.binFrames += 2
    self.imageSource.startCapture(green)

  def closeEvent(self, event):
    self.imageSource.stopCapture()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  mainWindow = ScanWidget()
  sys.exit(app.exec_())
