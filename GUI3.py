from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QAction, QMenuBar, QActionGroup, QMenu, QDialog, QWidgetAction, QComboBox
from PyQt5.QtCore import QTimer, QRectF, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QImage, QFont, QPixmap
'''
from PyQt5.QtWidgets import , QPushButton, QApplication, QLabel, QFrame, QComboBox, QLabel, QMainWindow, QAction, QActionGroup, QMenuBar
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QRectF, QPoint, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QImage, QIcon'''
import sys
import ImageSource, ImageProcessing, FileHandler
from CategoryGUI import Ui_Dialog as Form
from PADReview import Ui_Form as uiForm
import platform
import numpy as np
import threading, time

border_size = 20.0
default_test = '12LanePADKenya2015'
default_category = 'General'
default_sample = 'Alum (Granules)'
name = "Herb Scanner"
version = 1.21
nameAndVersion = "%s-v%.2f" % ( name, version )
DEFAULTS = "Herbs"

class NNThread(threading.Thread):
  def __init__(self, instance, sample, review, os, upload = False):
    threading.Thread.__init__(self)
    self.instance = instance
    self.sample = sample
    self.review = review
    self.upload = upload
    self.os = os

  def run(self):
    if self.upload:
      self.runUpload()
    else:
      self.runNN()

  def runUpload(self):
    print("Starting Upload...")
    status = 'Uploading... '
    data = FileHandler.getMetaData(self.instance, self.sample)
    data['uploaded'] = status
    self.updateReview(status, self.review.pushButton_2)
    FileHandler.uploadImage(self.instance, self.sample)
    data = FileHandler.getMetaData(self.instance, self.sample)
    status = data['uploaded']
    self.updateReview(status, self.review.pushButton_2)

  def runNN(self):
    print("Starting NN...")
    drug = 'Predicting... '
    data = FileHandler.getMetaData(self.instance, self.sample)
    data['sample_pred'] = drug
    FileHandler.saveMetaData(data, instance=self.instance, sample=self.sample)
    self.updateReview(drug, self.review.pushButton)
    drug, percent = FileHandler.readImage(self.instance, self.sample, self.os)
    data = FileHandler.getMetaData(self.instance, self.sample)
    data['sample_pred'] = drug
    FileHandler.saveMetaData(data, instance=self.instance, sample=self.sample)
    self.updateReview(drug, self.review.pushButton)

  def updateReview(self, text, button):
    try:
      sample = self.review.listWidget.currentItem().text()
      instance = self.review.listWidget_2.currentItem().text()
      if sample == self.sample and instance == self.instance:
        button.setText(text)
    except Exception as e:
      pass

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
    self.setDefaults()
    self.initVars()
    self.initUI()
    self.setUpImage()

  def initVars(self):
    self.testing = False
    self.yeast = False
    self.os = platform.system()
    self.oldFiducials = []
    self.binFrames = 10
    self.foundYeast = False
    self.manualFoundYeast = False
    self.prefix = ""

  def setDefaults(self):
    self.test = default_test
    self.drug = default_sample
    self.category = default_category

  def getData(self):
    data = {}
    data['sample_name'] = self.drugBox.currentText()
    data['test_name'] = self.test
    data['category_name'] = self.category
    data['uploaded'] = False
    return [data]

  def saveImage(self):
    print("Saving image")
    if not self.yeast:
      data = self.getData()
      self.prefix = FileHandler.savePADImage(self.rawImage, self.finalImage, data, self.qr)
      self.setUpSubMenus(self.reviewMenu)
    if self.yeast and self.foundYeast:
      FileHandler.saveYeastImage(self.finalImage)
    elif self.yeast and self.manualFoundYeast:
      FileHandler.saveYeastWhiteImage(self.whiteImage, self.finalImage)
    self.restartCapture()

  def setButtonVisibility(self, visibility):
    self.saveButton.setVisible(visibility)
    self.resetButton.setVisible(visibility)

  def initUI(self):
    CenterWindow(self, 800, 480, 1.2)
    self.setWindowTitle(nameAndVersion)
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
    self.drugBox = QComboBox(self)
    self.setupDrugBox()
    if self.yeast:
      self.takeButton = QPushButton("Take image", self)
      self.setupButton(self.takeButton, self.manualYeastImage, 400, 520)
      self.takeButton.setVisible(True)
    self.setUpMenu()
    self.show()

  def setupDrugBox(self):
    available = FileHandler.getBriefData(defaults=DEFAULTS)
    self.drugBox.addItems(available['samples'])
    index = self.drugBox.findText(self.drug)
    self.drugBox.setCurrentIndex(index)
    self.drugBox.setFont(QFont("Arial", 20))
    self.drugBox.move(350, 20)
    self.drugBox.resize(300,40)

  def readDialog(self):
    self.drug = self.drugBox.currentText()
    self.category = self.form.category_box.currentText()
    self.test = self.form.test_box.currentText()
    print(self.drug, self.category, self.test)

  def openDialog(self):
    dialog = QDialog()
    dialog.ui = Form()
    dialog.ui.setupUi(dialog)
    self.form = dialog.ui
    self.setUpDialog()
    dialog.accepted.connect(self.readDialog)
    dialog.exec_()
    dialog.show()

  def openReview(self):
    dialog = QDialog()
    dialog.ui = uiForm()
    dialog.ui.setupUi(dialog)
    self.review = dialog.ui
    self.setUpReview()
    dialog.exec_()
    dialog.show()

  def setUpDialog(self):
    available = FileHandler.getBriefData(defaults='Herbs')
    self.form.category_box.addItems(available['categories'])
    index = self.form.category_box.findText(self.category)
    self.form.category_box.setCurrentIndex(index)
    self.form.test_box.addItems(available['tests'])
    index = self.form.test_box.findText(self.test)
    self.form.test_box.setCurrentIndex(index)

  def setUpReview(self):
    self.populateSamples()
    self.review.listWidget_2.currentItemChanged.connect(self.showSamples)
    self.review.listWidget.currentItemChanged.connect(self.showPADs)
    self.review.listWidget.setCurrentRow(0)

  def showSamples(self, a, b):
    if a is not None:
      instance = a.text()
      sample = self.review.listWidget.currentItem().text()
      metadata = FileHandler.getMetaData(instance, sample)
      imgPath = FileHandler.getSavedImage(instance, sample)
      self.review.label.setPixmap(QPixmap(imgPath))
      self.setButton(metadata, self.review.pushButton_4, 'sample_name')
      self.setButton(metadata, self.review.pushButton_7, 'category_name')
      self.setButton(metadata, self.review.pushButton_5, 'test_name')
      self.setClickableButton(metadata, self.review.pushButton, 'sample_pred')
      self.setClickableButton(metadata, self.review.pushButton_2, 'uploaded')

  def predictDrug(self):
    print("Getting prediction")
    print(threading.active_count())
    if threading.active_count() < 2:
      instance = self.review.listWidget_2.currentItem().text()
      sample = self.review.listWidget.currentItem().text()
      thread = NNThread(instance, sample, self.review, self.os, upload = False)
      thread.start()
    else:
      self.review.pushButton.setText('Processor Busy')

  def uploadDrug(self):
    print("Uploading")
    instance = self.review.listWidget_2.currentItem().text()
    sample = self.review.listWidget.currentItem().text()
    thread = NNThread(instance, sample, self.review, upload = True)
    thread.start()

  def setClickableButton(self, data, button, target):
    try: button.clicked.disconnect()
    except Exception: pass
    if target in data.keys():
      if target == 'sample_pred':
        button.setText(data[target])
      elif target == 'uploaded':
        if data[target]:
          button.setText('Upload Successful!')
        else:
          button.setText('Upload')
          button.clicked.connect(self.uploadDrug)
    else:
      if target == 'sample_pred':
        button.setText('Predict')
        button.clicked.connect(self.predictDrug)
      elif target == 'uploaded':
        button.setText('Upload')
        button.clicked.connect(self.uploadDrug)

  def setButton(self, data, button, target):
    if target in data.keys():
      button.setText(data[target])
    else:
      button.setText('Unknown')

  def showPADs(self, a, b):
    self.review.listWidget_2.clear()
    sampleInstances = FileHandler.getSavedSampleInstances(a.text())
    if sampleInstances is not None:
      for instance in sampleInstances:
        if instance != '.DS_Store':
          self.review.listWidget_2.addItem(instance)
    self.review.listWidget_2.setCurrentRow(0)

  def populateSamples(self):
    samples = FileHandler.getSavedSamples()
    for sample in samples:
      if sample != '.DS_Store':
        self.review.listWidget.addItem(sample)

  def setUpMenu(self):
    mainmenu = self.menuBar()
    menu = mainmenu.addMenu('Set Defaults')
    act = QAction('Set Defaults', menu)
    act.triggered.connect(self.openDialog)
    menu.addAction(act)
    self.reviewMenu = mainmenu.addMenu('Review Samples')
    act = QAction('Review Samples', self.reviewMenu)
    act.triggered.connect(self.openReview)
    self.reviewMenu.addAction(act)
    mainmenu.adjustSize()

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

  def unholyHack(self, action):
    parentMenu = action.parentWidget()
    grandParentMenu = parentMenu.parent()
    instance = parentMenu.title()
    sample = grandParentMenu.title()
    if action.text() == 'No prediction':
      #data = FileHandler.getMetaData(instance, sample)
      #data['sample_pred'] = 'Processing...'
      #FileHandler.saveMetaData(data, instance=instance, sample=sample)
      self.runNN(parentMenu, instance, sample)
    elif action.text() == 'Not Uploaded':
      FileHandler.uploadImage(instance, sample)
    parentMenu.clear()
    self.buildMetaData(parentMenu, instance, sample)

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

  def setUpSubMenus(self, menu):
    menu.clear()
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

if __name__ == '__main__':
  app = QApplication(sys.argv)
  mainWindow = ScanWidget()
  sys.exit(app.exec_())
