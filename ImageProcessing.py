import cv2
import numpy as np
import zbar
from PIL import Image

minDiameter = 10
lanesStart = 706
lanesWidth = 689
laneWidth = 53
laneYStart = 359
laneYEnd = 1095

dst_points_old = [[85, 1163], [686, 1163], [686, 77], [82, 64], [82, 226], [244, 64]]
dst_points_new = [[85, 1163], [686, 1163], [686, 77], [82, 64], [82, 237], [255, 64]]

def userProcessImage(img, oldFiducials):
  processed = drawWork(img, oldFiducials)
  return processed, oldFiducials

def ProcessImage(img, oldFiducials = []):
  img, fiducials = FindContours(img)
  fiducials = sortFiducials(fiducials, oldFiducials)
  processed = drawWork(img, fiducials)
  return processed, fiducials

def FindContours(img):
  blurred = cv2.blur(img, (2,2))
  edges = cv2.Canny(blurred, 40, 150)
  img2, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2RGB)
  #img, fiducials = findFiducials(contours, hierarchy, img2)
  #return img, fiducials
  fiducials = findFiducials(contours, hierarchy)
  return img, fiducials

def compareFiducials(fiducials, oldFiducials):
  newFiducials = []
  if len(fiducials) < len(oldFiducials):
    newFiducials = oldFiducials
  else:
    newFiducials = fiducials
  return newFiducials

def sortFiducials(fiducials, oldFiducials):
  quadrants = [[],[],[],[]]
  total = np.sum(np.asarray(fiducials), axis=0)
  if len(fiducials) > 6:
    fiducials = []
  '''if len(fiducials) == 5:
    centerX = total[0]/len(fiducials)
    centerY = total[1]/len(fiducials)
    for point in fiducials:
      assign(point, centerX, centerY, quadrants)
    if len(quadrants[1]) == 2 and 1 == len(quadrants[0]) and 1 == len(quadrants[2]) and 1 == len(quadrants[3]):
      fiducials = sort10(quadrants)
    else:
      print("Failed")
      fiducials = []'''
  if len(fiducials) == 6:
    centerX = total[0]/len(fiducials)
    centerY = total[1]/len(fiducials)
    for point in fiducials:
      assign(point, centerX, centerY, quadrants)
    if len(quadrants[1]) == 3 and 1 == len(quadrants[0]) and 1 == len(quadrants[2]) and 1 == len(quadrants[3]):
      fiducials = sort1(quadrants)
    elif len(quadrants[2]) == 3 and 1 == len(quadrants[0]) and 1 == len(quadrants[1]) and 1 == len(quadrants[3]):
      fiducials = sort2(quadrants)
    else:
      print("Failed")
      fiducials = []
  fiducials = compareFiducials(fiducials, oldFiducials)
  return fiducials

def assign(point, centerX, centerY, quadrants):
  if point[0] > centerX:
    if point[1] > centerY:
      quadrants[0].append(point)
    else:
      quadrants[1].append(point)
  else:
    if point[1] > centerY:
      quadrants[2].append(point)
    else:
      quadrants[3].append(point)

def sort1(quadrants):
  fiducials = []
  MaxSort = np.argmax(quadrants[1], 0)
  MinSort = np.argmin(quadrants[1], 0)
  BR = MinSort[0]
  TL = MaxSort[1]
  if BR == TL:
    return []
  TR = range(3)
  TR.remove(BR)
  TR.remove(TL)
  TR = TR[0]
  fiducials.append(quadrants[3][0]) #6
  fiducials.append(quadrants[2][0]) #5
  fiducials.append(quadrants[0][0]) #4
  fiducials.append(quadrants[1][TR]) #2
  fiducials.append(quadrants[1][BR]) #1
  fiducials.append(quadrants[1][TL]) #3
  #print("SORT1")
  return fiducials

def sort10(quadrants):
  fiducials = []
  print("Sort10")
  fids = [[82, 64], [82, 226], [244, 64]]
  TR = (-1,-1,-1,-1)
  BR = (-1,-1,-1,-1)
  TL = (-1,-1,-1,-1)
  for q in quadrants[1]:
    mod = [800-q[0], q[1]]
    closest = getClosest(mod,fids)
    if closest == 0 and TR == (-1,-1,-1,-1):
      TR = q
    elif closest == 1 and BR == (-1,-1,-1,-1):
      BR == q
    elif closest == 2 and TL == (-1,-1,-1,-1):
      TL = q
  if TR == (-1,-1,-1,-1):
    return []
  fiducials.append(quadrants[3][0]) #6
  fiducials.append(quadrants[2][0]) #5
  fiducials.append(quadrants[0][0]) #4
  fiducials.append(TR) #2
  fiducials.append(BR) #1
  fiducials.append(TL) #3
  return fiducials

def getClosest(f, fids):
  fids = np.asarray(fids)
  d = np.sum((f-fids)**2, axis=1)
  return np.argmin(d)

def sort2(quadrants):
  fiducials = []
  MaxSort = np.argmax(quadrants[2], 0)
  MinSort = np.argmin(quadrants[2], 0)
  BR = MaxSort[0]
  TL = MinSort[1]
  if BR == TL:
    return []
  TR = range(3)
  TR.remove(BR)
  TR.remove(TL)
  TR = TR[0]
  fiducials.append(quadrants[0][0]) #6
  fiducials.append(quadrants[1][0]) #5
  fiducials.append(quadrants[3][0]) #4
  fiducials.append(quadrants[2][TR]) #2
  fiducials.append(quadrants[2][BR]) #1
  fiducials.append(quadrants[2][TL]) #3
  #print("SORT2")
  return fiducials

def findFiducials(contours, hierarchy):
  fiducials = []
  Markers = selectMarkers(contours, hierarchy)
  for mark in Markers:
    #cv2.drawContours(img, contours, mark, (0,255,0), 1)
    x, y, w, h = cv2.boundingRect(contours[mark])
    x = x+int(w/2)
    y = y+int(h/2)
    for point in fiducials:
      if abs(point[0]-x) < 5 and abs(point[1]-y) < 5:
        break
    else:
      diameter = min(w,h)
      sqrtArea = cv2.contourArea(contours[mark])**.5
      if diameter > minDiameter and sqrtArea > (.85 * diameter):
        fiducials.append([x, y, diameter, -1])
  return fiducials

def selectMarkers(contours, hierarchy):
  Markers = []
  for i in range(len(contours)):
    contour = i
    depth = 0
    while hierarchy[0][contour][2] != -1:
      contour = hierarchy[0][contour][2]
      depth += 1
    if hierarchy[0][contour][2] != -1:
      depth += 1
    if depth >= 3:
    #if depth >= 5:
      Markers.append(contour)
  return Markers

def drawWork(img, fiducials):
  processed = img.copy()
  color = (0,255,0)
  if len(fiducials) != 6:
    color = (0, 0, 255)
  for fiducial in fiducials:
    if fiducial[0] > 0:
      cv2.circle(processed, (fiducial[0], fiducial[1]), fiducial[2], color, 2)
  return processed

def rectifyImage(img, fiducials):
  output, passed = singleRectifyAttempt(img, fiducials, dst_points_new)
  if not passed:
    output, passed = singleRectifyAttempt(img, fiducials, dst_points_old)
  return output, passed

def singleRectifyAttempt(img, fiducials, points):
  src_points = fiducials
  dst_points = points
  srcpoints = np.array(src_points[:4], np.float32)
  dstpoints = np.array(dst_points[:4], np.float32)
  transformation = cv2.getPerspectiveTransform(srcpoints, dstpoints)
  output = cv2.warpPerspective(img, transformation, (730, 1220),borderMode=cv2.BORDER_REPLICATE)
  error = getError(fiducials, transformation)
  print("error = "+ str(error))
  return output, error < 20

def getError(fiducials, transformation):
  error = 0
  for i in range(2):
    if fiducials[4+i][0]>0:
      check, trueChecks = getCheck(fiducials, transformation, 4+i)
      for j in range(1):
        dist = check[:, j]-trueChecks[i]
        dist = dist**2
        dist = dist**.5
        error += np.sum(dist)
  return error

def getCheck(fiducials, transformation, checkID = 4):
  check = np.ones((2,3), dtype='float32')
  check[0,:2] = fiducials[checkID]
  check = np.transpose(check)
  transformedCheck = np.matmul(transformation, check)
  trueChecks = np.array([[82,226,1],[244,64,1]], np.float32)
  for i in range(2):
    transformedCheck[:,i] = transformedCheck[:,i]/transformedCheck[2,i]
  return transformedCheck, trueChecks

def getQR(img):
  img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
  scanner = zbar.Scanner()
  result = scanner.scan(img)
  print(result)
  if len(result) > 0:
    code = result[0].data
    code = code.replace("padproject.nd.edu/?s=", "")
    code = code.replace("padproject.nd.edu/?t=", "")
    return code
  return "Unknown"

def findWax(img):
  img2 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
  #template = cv2.imread("/home/pi/Documents/Template2.png", 0)
  template = cv2.imread("Template2.png", 0)
  match = cv2.matchTemplate(img2, template, cv2.TM_CCOEFF_NORMED)
  cv2.normalize(match, match, 0, 255, cv2.NORM_MINMAX)
  #cv2.imwrite("./prematch.png", img2)
  #cv2.imwrite("./match.png", match)
  allowedPositions = np.ones((match.shape[0], match.shape[1]), dtype=np.uint8)
  maxConfidence = 255
  threshold = 200
  wax = []
  while(len(wax) < 2 and maxConfidence > threshold):
    _, maxConfidence, _, (a, b) = cv2.minMaxLoc(match, mask = allowedPositions)
    centerX = a + (template.shape[0]/2)
    centerY = b + (template.shape[1]/2)
    wax.append((centerX, centerY))
    print("Found wax,", centerX, centerY, maxConfidence)
    try:
      allowedPositions[(b-template.shape[1]/2):(b+template.shape[1]/2),(a-template.shape[0]/2):(a+template.shape[0]/2)] = 0
    except Exception as e:
      return []
  wax = sorted(wax, key=lambda tup:tup[1])
  return wax

def correctComb(img, finX, finY, wax=None):
  if wax is None:
    wax = findWax(img)
  if len(wax) != 2:
    print("Failed to find wax markers")
    return img, False
  topWax = (387, 214)
  botWax = (387, 1164)
  srcpoints = makeList(wax[0], wax[1])
  dstpoints = makeList(topWax, botWax)
  transformation = cv2.getPerspectiveTransform(srcpoints, dstpoints)
  output = cv2.warpPerspective(img, transformation, (730, 1220),borderMode=cv2.BORDER_REPLICATE)
  drawLines(output, topWax, botWax)
  resized = cv2.rotate(output, cv2.ROTATE_90_CLOCKWISE)
  resized = cv2.resize(resized, (finX, finY))
  return output, resized, True

def drawLines(output, topWax, botWax):
  for i in range(13):
    x = lanesStart - i*laneWidth
    cv2.line(output, (x, laneYStart), (x,laneYEnd), (0, 255, 0), 1)
  cv2.line(output, (topWax[0], topWax[1]-5), (topWax[0], topWax[1]+5), (0, 255, 0), 1)
  cv2.line(output, (topWax[0]-5, topWax[1]), (topWax[0]+5, topWax[1]), (0, 255, 0), 1)
  cv2.line(output, (botWax[0], botWax[1]-5), (botWax[0], botWax[1]+5), (0, 255, 0), 1)
  cv2.line(output, (botWax[0]-5, botWax[1]), (botWax[0]+5, botWax[1]), (0, 255, 0), 1)

def makeList(pointA, pointB):
  ret = []
  nested = [getCorners(pointA), getCorners(pointB)]
  for sublist in nested:
    for item in sublist:
      ret.append(item)
  return np.array(ret, np.float32)

def getCorners(point):
  return [(point[0]-(lanesWidth/2), point[1]), (point[0]+(lanesWidth/2), point[1])]

if __name__ == '__main__':
  raw = cv2.imread('./raw.jpg', 1)
  processed, resized = ProcessImage(raw)
  cv2.imshow('Corrected', processed)
  cv2.waitKey(0)
  cv2.destroyAllWindows()