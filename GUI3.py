from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton
from PyQt5.QtCore import QTimer, QRectF, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QImage, QFont
'''
from PyQt5.QtWidgets import , QPushButton, QApplication, QLabel, QFrame, QComboBox, QLabel, QMainWindow, QAction, QActionGroup, QMenuBar
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QRectF, QPoint, QTimer, pyqtSlot
from PyQt5.QtGui import QPainter, QFont, QColor, QPen, QImage, QIcon'''
import sys
import ImageSource, YIP3, FileHandler
import platform
import numpy as np

border_size = 20.0

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

  def initVars(self):
    self.testing = False
    self.yeast = True
    self.os = platform.system()
    self.oldFiducials = []
    self.manualFoundYeast = False
    self.timeToEnable = 5

  def initUI(self):
    CenterWindow(self, 800, 480, 1.2)
    self.setWindowTitle('PadScan')
    self.IWidget =  ImageWidget(self)
    self.saveButton = QPushButton("Save image", self)
    self.setupButton(self.saveButton, self.saveImage, 10, 20)
    self.resetButton = QPushButton("Discard image", self)
    self.setupButton(self.resetButton, self.restartCapture, 760, 20)
    self.takeButton = QPushButton("Take image", self)
    self.setupButton(self.takeButton, self.manualYeastImage, 400, 520)
    self.takeButton.setVisible(True)
    self.takeButton.setEnabled(False)
    self.show()

  def setupButton(self, button, program, x, y):
    button.setFont(QFont("Arial", 20))
    button.clicked.connect(program)
    button.move(x, y)
    button.adjustSize()
    button.setVisible(False)

  def saveImage(self):
    print("Saving image")
    if self.manualFoundYeast:
      #stackImage, processedImage, data = YIP3.fullProcess(self.finalImage)
      FileHandler.saveYeastWhiteImage(self.whiteImage, self.finalImage)
    else:
      print("Unreachable save state- manualFoundYeast not set")
    self.restartCapture()

  def restartCapture(self, green=False, reset=True):
    self.setButtonVisibility(False)
    self.takeButton.setEnabled(False)
    self.timeToEnable = 20
    if reset:
      self.initVars()
    self.imageSource.startCapture(green)
    print("Restarted capture")

  def setButtonVisibility(self, visibility):
    self.saveButton.setVisible(visibility)
    self.resetButton.setVisible(visibility)

  def manualYeastImage(self, img = False):
    if img is False:
      img = self.imageSource.getImage()
    self.imageSource.stopCapture()
    if not self.manualFoundYeast:
      self.whiteImage = img
      print(img)
      self.restartCapture(green=True, reset=False)
      self.manualFoundYeast = True
    else:
      self.finalImage = img
      self.saveImage()

  def setUpImage(self):
    self.imageSource = ImageSource.imageSource(self.os, self.testing, self.yeast)
    self.imageSource.setSize(self.frameSize().height(), self.frameSize().width())
    self.imageSource.startCapture()
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.updateFrame)
    self.timer.start(1)

  def updateFrame(self):
    if self.imageSource.ready():
      image = self.imageSource.getImage()
      self.setImage(image)
      if not self.takeButton.isEnabled():
        if self.timeToEnable > 0:
          self.timeToEnable -= 1
        else:
          self.takeButton.setEnabled(True)


  def setImage(self, img):
    height, width, bpc = img.shape
    bpl = bpc * width
    self.image = QImage(img.data, width, height, bpl, QImage.Format_RGB888)
    self.IWidget.setImage(self.image)

  def closeEvent(self, event):
    self.imageSource.stopCapture()

if __name__ == '__main__':
  app = QApplication(sys.argv)
  mainWindow = ScanWidget()
  sys.exit(app.exec_())
