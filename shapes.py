import cv2
import numpy as np
from math import atan, degrees
from operator import itemgetter

DIST_MINUS_PLUS = 201.0

def getContourContents(img, mark):
  cimg = np.zeros_like(img)
  cv2.drawContours(cimg, [mark], 0, 255, -1)
  pts = np.where(cimg == 255)
  cells = img[pts[0], pts[1]] 
  #cv2.imshow("temp", cimg)
  #cv2.waitKey()
  return cells

def distance(a, b):
  x = a[0]-b[0]
  y = a[1]-b[1]
  return ((x**2)+(y**2))**.5

#Heavily modified- expects a list of [contour, position]. Can't select
# yourself as closest
def closest(item, listItems):
  closestIndex = 0
  closestDist = 999999
  for i in range(len(listItems)):
    dist = distance(item, listItems[i][1])
    if dist < closestDist and dist > 1:
      closestDist = dist
      closestIndex = i
  return closestIndex

def farthest(item, listItems):
  farthestIndex = 0
  farthestDist = 0
  for i in range(len(listItems)):
    dist = distance(item, listItems[i][1])
    if dist > farthestDist and dist > 1:
      farthestDist = dist
      farthestIndex = i
  return farthestIndex

def getAngle(p1, p2):
  dX = (p1[0]-p2[0])
  dY = (p1[1]-p2[1])
  if dX == 0:
    if dY >= 0:
      return 90
    else:
      return 270
  else:
    theta = atan(float(dY)/dX)
    return degrees(theta)

class YeastField():
  def __init__(self, baseImg):
    self.baseImg = baseImg
    self.sorted = False
    self.strips = []

  def addCircles(self, circles):
    if len(self.strips) > 0:
      self.strips = []
    if(len(circles) % 4 != 0) or (len(circles) == 0):
      return
    centers = []
    for i in range(len(circles)):
      (x,y),r = cv2.minEnclosingCircle(circles[i])
      centers.append((x,y,i))
    centers = sorted(centers, key=itemgetter(0,1))
    for strip in range(int(len(centers)/4)):
      stripCircles = []
      for spot in range(4):
        index = centers[strip*4+spot][2]
        stripCircles.append(circles[index])
      structure = YeastPAD(self.baseImg.copy())
      structure.addCircles(stripCircles)
      self.strips.append(structure)
    self.sorted = True
    for strip in self.strips:
      self.sorted = self.sorted and strip.sorted


class YeastPAD():
  def __init__(self, baseImg):
    self.plus = None
    self.minus = None
    self.c1 = None
    self.c2 = None
    self.c3 = None
    self.c4 = None
    self.sorted = False
    self.minCircleSep = 0
    self.baseImg = baseImg

  def getCircleData(self, circleNumber, channelNumber):
    circles = self.getCircles()
    relevantCircle = circles[circleNumber]
    rawData = getContourContents(self.baseImg, relevantCircle[0])
    integrated = rawData[:,channelNumber].sum()
    avg = rawData[:,channelNumber].mean()
    return [integrated, avg]

  def getCorrections(self):
    if not self.sorted:
      return False, None, None, None
    #print(self.c1[1], self.c4[1])
    angle = getAngle(self.c1[1], self.c4[1])
    scale = distance(self.c1[1], self.c4[1])/DIST_MINUS_PLUS
    if scale == 0:
      return False, None, None, None
    return True, angle, scale, self.c1[1]

  def addCircles(self, circles):
    if(len(circles) != 4):
      print(len(circles))
      return
    circles = circles
    circles = self.addCenter(circles)
    self.findMinCircleSep(circles)
    self.setCircles(circles)
    self.sortCircles()
    self.sorted = self.sanityCheck()

  def addCenter(self, circles):
    for i in range(len(circles)):
      (x,y),r = cv2.minEnclosingCircle(circles[i])
      circles[i] = [circles[i], (x,y)]
    return circles

  def sortCircles(self):
    #print(self.c1[1][0], self.c4[1][0])
    #print(self.c1[1][1], self.c4[1][1])
    # > [1][0] sorts horizontal images, < [1][1] sorts vertical
    if self.c1[1][1] < self.c4[1][1]:
      c1 = self.c1
      c2 = self.c2
      c3 = self.c3
      c4 = self.c4
      self.c1 = c4
      self.c2 = c3
      self.c3 = c2
      self.c4 = c1
      #print("Flipped")

  def sanityCheck(self):
    ab = distance(self.c1[1], self.c2[1])
    bc = distance(self.c2[1], self.c3[1])
    cd = distance(self.c3[1], self.c4[1])
    ac = distance(self.c1[1], self.c3[1])
    bd = distance(self.c2[1], self.c4[1])
    ad = distance(self.c1[1], self.c4[1])
    sanity = isclose(ab, bc, rel_tol=.05)
    sanity = sanity and isclose(ab, cd, rel_tol=.05)
    sanity = sanity and isclose(ab+bc, ac, rel_tol=.05)
    sanity = sanity and isclose(bc+cd, bd, rel_tol=.05)
    sanity = sanity and isclose(ab+bc+cd, ad, rel_tol=.05)
    sanity = sanity and isclose(ab*3, ad, rel_tol=.05)
    '''
    print("\n***********")
    print(isclose(ab, bc, rel_tol=.05))
    print(isclose(ab, cd, rel_tol=.05))
    print(isclose(ab+bc, ac, rel_tol=.05))
    print(isclose(bc+cd, bd, rel_tol=.05))
    print(isclose(ab+bc+cd, ad, rel_tol=.05))
    print(isclose(ab*3, ad, rel_tol=.05))
    print("***********\n")'''
    return sanity

  def setCircles(self, inCircles):
    circles = []
    for c in inCircles:
      circles.append(c)
    firstIndex = farthest(circles[0][1], circles)
    self.c1 = circles[firstIndex]
    del circles[firstIndex]
    secondIndex = closest(self.c1[1], circles)
    self.c2 = circles[secondIndex]
    del circles[secondIndex]
    thirdIndex = closest(self.c2[1], circles)
    self.c3 = circles[thirdIndex]
    del circles[thirdIndex]
    fourthIndex = closest(self.c3[1], circles)
    self.c4 = circles[fourthIndex]

  def getCircles(self):
    if not self.sorted:
      return
    return [self.c1, self.c2, self.c3, self.c4]

  def findMinCircleSep(self, circles):
    dists = []
    for circle in circles:
      minDist = 99999
      for c in circles:
        dist = distance(circle[1], c[1])
        if dist < minDist and dist > 1:
          minDist = dist
      dists.append(minDist)
    self.minCircleSep = np.array(dists).mean()

  def findPosShapes(self, shapes, circles):
    posibilities = []
    for shape in shapes:
      validShape = False
      for circle in circles:
        if distance(circle[1], shape[1]) < self.minCircleSep:
          validShape = True
          continue
      if validShape:
        posibilities.append(shape)
    return posibilities

def isclose(x, y, rel_tol):
  dif = abs(x-y)
  max_tol = max(abs(x), abs(y))
  max_tol *= rel_tol
  return dif <= max_tol

class imgStack():
  #Assumes that the first image is the correct size, no assumptions about color.
  def __init__(self, img, scale=1.0):
    self.scale = scale
    self.numImgs = 1
    image = self.correctScaleAndColor(img) #Needs to stay after setting numImgs and scale
    self.imgList = [image]
    self.name = "ImageStack"

  def correctScaleAndColor(self, image):
    #If it's not the first image, resize it to the first image
    if self.numImgs > 1:
      image = cv2.resize(image, dsize = (self.imgList[-1].shape[1], self.imgList[-1].shape[0]), interpolation = cv2.INTER_CUBIC)
    else:
      image = cv2.resize(image, dsize = None, fx=self.scale, fy=self.scale, interpolation = cv2.INTER_CUBIC)
    #If there are less than 3 channels, convert to RGB
    if len(image.shape) < 3:
      image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image

  def addImg(self, img):
    self.numImgs += 1
    image = img.copy()
    image = self.correctScaleAndColor(image)
    self.imgList.append(image)

  def display(self):
    cv2.imshow(self.name, self.computeDisplayImage())
    cv2.waitKey()
    cv2.destroyAllWindows()

  def computeDisplayImage(self):
    finalStack = None
    if (self.numImgs % 2) == 1:
      TempImage = np.zeros(self.imgList[-1].shape, dtype='uint8')
    #Deliberately int arithmatic- we want to add one and round down
    stackHeight = int((self.numImgs+1)/2)
    verticalScale = 1.0/stackHeight
    for layer in range(stackHeight):
      image1 = cv2.resize(self.imgList[layer*2], None, fx=.5, fy=verticalScale, interpolation = cv2.INTER_CUBIC)
      if layer*2+1 == self.numImgs:
        image2 = cv2.resize(TempImage, None, fx=.5, fy=verticalScale, interpolation = cv2.INTER_CUBIC)
      else:
        image2 = cv2.resize(self.imgList[layer*2+1], None, fx=.5, fy=verticalScale, interpolation = cv2.INTER_CUBIC)
      imageLayer = np.hstack((image1, image2))
      if finalStack is None:
        finalStack = imageLayer
      else:
        finalStack = np.vstack((finalStack, imageLayer))
    return finalStack

  def getImageStack(self):
    return self.computeDisplayImage()


if __name__ == '__main__':
  startImg = cv2.imread('nl.png')
  stack = imgStack(startImg)
  stack.display()
  stack.addImg(startImg)
  stack.display()
  stack.addImg(startImg)
  stack.display()
  stack.addImg(startImg)
  stack.display()
  stack.addImg(startImg)
  stack.display()
  stack.addImg(startImg)
  stack.display()