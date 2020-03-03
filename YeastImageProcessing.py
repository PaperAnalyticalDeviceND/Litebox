import cv2
import numpy as np
import zbar
from PIL import Image
from math import atan, degrees

#Circle positions:
#(84 59) 526
#(151 56) 527
#(219 56) 525
#(286 56) 526
#Plus position:
#(39 60) 46
#Minus position:
#(327 58) 193
#dist = 288

NEW_POINTS = np.float32([[54, 59], [114,59], [256, 56], [316, 56]])
DIST = 288

def quadView(v1, v2, v3=None, v4=None):
  v1=cv2.resize(v1, None, fx=.5, fy=.5, interpolation = cv2.INTER_CUBIC)
  v2=cv2.resize(v2, None, fx=.5, fy=.5, interpolation = cv2.INTER_CUBIC)
  finalView = np.hstack((v1, v2))
  if v3 is not None:
    v3=cv2.resize(v3, None, fx=.5, fy=.5, interpolation = cv2.INTER_CUBIC)
    v4=cv2.resize(v4, None, fx=.5, fy=.5, interpolation = cv2.INTER_CUBIC)
    botView = np.hstack((v3, v4))
    finalView = np.vstack((finalView, botView))
  return finalView

def getPlus():
  img = cv2.imread('plusSign.png')
  img2, contours, hierarchy, blurred = processImg(img)
  marks = selectMarkers(contours, hierarchy, 1)
  return marks[0]

def getMinus():
  img = cv2.imread('minusSign.png')
  img2, contours, hierarchy, blurred = processImg(img)
  marks = selectMarkers(contours, hierarchy, 1)
  return marks[0]

def processImg(img):
  blurred = cv2.blur(img, (2,2))
  edges = cv2.Canny(blurred, 40, 150)
  img2, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  return img2, contours, hierarchy, blurred

def FindContours(img):
  img2, contours, hierarchy, blurred = processImg(img)
  marks = selectMarkers(contours, hierarchy, 0)
  img, p1v, p2v, shapes = findShapes(img, marks)
  img3 = cv2.drawContours(blurred, marks, -1, (255,0,0), 1)
  if len(shapes)==6 and (shapes[-1] is not None) and (shapes[-2] is not None):
    print("Yay!")
    orderedPoints = extractStructure(shapes)
    warped = WarpImg(img, orderedPoints)
    warped = cv2.resize(warped, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    return quadView(img, img3, p1v, warped)
  #img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2RGB)'''
  return quadView(img, img3, p1v, p2v)

def getDir(a,b):
  x = a[0]-b[0]
  y = a[1]-b[1]
  return x/y

def extractStructure(shapes):
  plus = shapes[-2]
  minus = shapes[-1]
  circles = shapes[0:4]
  circle0, circles = getRightCircle(circles, minus)
  circle1, circles = getRightCircle(circles, circle0)
  circle2, circles = getRightCircle(circles, circle1)
  circle3, circles = getRightCircle(circles, circle2)
  return [circle0, circle1, circle2, circle3, plus, minus]

def getRightCircle(circles, previous):
  newI = closest(previous, circles)
  newCircle = circles[newI]
  circles.remove(newCircle)
  return newCircle, circles

def closest(item, listItems):
  closestIndex = 0
  closestDist = 999999
  for i in range(len(listItems)):
    dist = distance(item, listItems[i])
    if dist < closestDist:
      closestDist = dist
      closestIndex = i
  return closestIndex

def farthest(item, listItems):
  farthestIndex = 0
  farthestDist = 0
  for i in range(len(listItems)):
    dist = distance(item, listItems[i])
    if dist > farthestDist:
      farthestDist = dist
      farthestIndex = i
  return farthestIndex

def distance(a, b):
  x = a[0]-b[0]
  y = a[1]-b[1]
  return ((x**2)+(y**2))**.5

def average(a, b):
  x = a[0]+b[0]
  y = a[1]+b[1]
  return [int(x/2), int(y/2)]

def WarpImg(img, oldPoints):
  angle, scale = getAngle(oldPoints[-2], oldPoints[-1])
  midpoint = average(oldPoints[-2],oldPoints[-1])
  midpoint = (midpoint[1], midpoint[0])
  print(angle)
  M = cv2.getRotationMatrix2D(midpoint, angle, 1.0)
  out = cv2.warpAffine(img, M, (int(scale*img.shape[1]), int(scale*img.shape[0])))
  return out

def getAngle(p1, p2):
  dist = distance(p1, p2)
  dX = (p1[0]-p2[0])/dist
  dY = (p1[1]-p2[1])/dist
  if dX == 0:
    if dY >= 0:
      return 90, DIST/dist
    else:
      return 270, DIST/dist
  else:
    theta = atan(dY/dX)
    return degrees(theta), DIST/dist

def checkShape(mark, shape):
  return cv2.matchShapes(mark, shape, cv2.CONTOURS_MATCH_I1, 0)

def findShapes(img, marks):
  start = img.copy()
  img2 = img.copy()
  font = cv2.FONT_HERSHEY_SIMPLEX
  shapes = []
  minus = None
  plus = None
  plusShape = getPlus()
  minusShape = getMinus()
  plusConf = .3
  minusConf = .1
  print("==============")
  for mark in marks:
    area = cv2.contourArea(mark)
    (x,y),r = cv2.minEnclosingCircle(mark)
    center = (int(x),int(y))
    r = int(r)
    circleArea = np.pi*(r*r)
    print("------%d---------" %area)
    if area < 30:
      continue
    minusS = checkShape(mark, minusShape)
    plusS = checkShape(mark, plusShape)
    if minusS < minusConf:
      minusConf = minusS
      cv2.drawContours(img, [mark], 0, (0,255,0),1)
      minus = [int(x),int(y)]
      print("Found minus w/ area %d" %(area))
    elif plusS < plusConf:
      plusConf = plusS
      cv2.drawContours(img, [mark], 0, (0,255,0),1)
      plus = [int(x),int(y)]
      print("Found plus w/ area %d" %(area))
    elif abs(circleArea-area) < 100 and area > 200:
      cv2.circle(img, center, r, (0,255,0),1)
      shapes.append([int(x),int(y)])
    else:
      cv2.drawContours(img2, [mark], 0, (255,0,0),1)
      cv2.putText(img2, str(area), center, font, 1, (0,0,0), 1)
  shapes.append(plus)
  shapes.append(minus)
  return start, img, img2, shapes

def selectMarkers(contours, hierarchy, targetDepth):
  Markers = []
  for i in range(len(contours)):
    contour = i
    depth = 0
    while hierarchy[0][contour][2] != -1:
      contour = hierarchy[0][contour][2]
      depth += 1
    if hierarchy[0][contour][2] != -1:
      depth += 1
    if depth == targetDepth:
      Markers.append(contours[contour])
  return Markers

if __name__ == '__main__':
  cv2.imread
  startImg = cv2.imread('nl.png')
  endImg = FindContours(startImg)
  cv2.imshow('frame',endImg)
  cv2.waitKey()
  cv2.destroyAllWindows()