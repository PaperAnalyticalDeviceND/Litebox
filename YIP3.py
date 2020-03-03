import cv2
import numpy as np
from PIL import Image
from shapes import imgStack, YeastField
import pandas as pd

MIN_CIRCLE_SIZE = 280
MAX_CIRCLE_SIZE = 500
DEBUG = False

def runProcess(img):
  structures = YeastField(img.copy())
  imgs, contours, hierarchy = getContours(img, 150)
  circles = selectCircles(contours, hierarchy, img.copy())
  structures.addCircles(circles)
  if not structures.sorted:
    imgs, circles, structures = additionalPass(imgs, circles, structures, 150, 150, 8, img, img)
  img2 = img.copy()
  for structure in structures.strips:
    if structure.sorted:
      img2 = cv2.drawContours(img2, [structure.c1[0]], -1, (0,255,0), 1)
      #printData(structure, 0, "green")
      img2 = cv2.drawContours(img2, [structure.c2[0]], -1, (0,0,255), 1)
      #printData(structure, 1, "red")
      img2 = cv2.drawContours(img2, [structure.c3[0]], -1, (255,0,0), 1)
      #printData(structure, 2, "blue")
      img2 = cv2.drawContours(img2, [structure.c4[0]], -1, (0,255,255), 1)
      #printData(structure, 3, "yellow")
  return img2, structures.sorted

def fullProcess(img, imgR, targetDir='./', ROI=None):
  pass1, processedImg, success, structures = firstPass(img, imgR, ROI)
  data = None
  if success:
    for structure in structures.strips:
      saveAll(structure, targetDir)
      #print(data)
      #data = saveAll(structure)
  return pass1, processedImg, data

def displayAll(structure):
  retStr = printData(structure, 0, "green")
  retStr += printData(structure, 1, "red")
  retStr += printData(structure, 2, "blue")
  retStr += printData(structure, 3, "yellow")
  return retStr

def saveAll(structure, targetDir, raw=True):
  [i0,a0] = saveData(structure, 0, raw)
  [i1,a1] = saveData(structure, 1, raw)
  [i2,a2] = saveData(structure, 2, raw)
  [i3,a3] = saveData(structure, 3, raw)
  targetFile = targetDir+'redAvg.csv'
  try:
    df = pd.read_csv(targetFile, index_col=0)
    index = df.shape[1]+1
    df[str(index)] = [a3, a2, a1, a0]
  except Exception as e:
    print(e)
    df = pd.DataFrame({'1':[a3, a2, a1, a0]})
  #print(df)
  df.to_csv(path_or_buf=targetFile, mode='w')

def saveData(structure, circle, raw):
  if raw:
    [redInt, redAvg] = structure.getCircleData(circle, 2)
  else:
    [redInt, redAvg] = getOffsetData(structure, circle, 2)
  return [redInt, redAvg]

def isCircle(contour):
  area = cv2.contourArea(contour)
  (x,y),r = cv2.minEnclosingCircle(contour)
  r = int(r)
  circleArea = np.pi*(r*r)
  if DEBUG:
    print(area, circleArea)
  if abs(circleArea-area) < (.4*area) and area > MIN_CIRCLE_SIZE and area < MAX_CIRCLE_SIZE:
    return True
  return False

def selectCircles(contours, hierarchy, img):
  circles = []
  for i in range(len(contours)):
    contour = i
    if isCircle(contours[contour]):
      if childrenNotCircles(contours, hierarchy, contour):
        circles.append(contours[contour])
        if DEBUG:
          cv2.drawContours(img, contours[contour], -1, (0,255,255), 2)
      elif DEBUG:
        cv2.drawContours(img, contours[contour], -1, (255,255,0), 2)
    elif DEBUG:
      cv2.drawContours(img, contours[contour], -1, (0,255,0), 2)
    if DEBUG:
      cv2.imshow("Process", img)
      cv2.waitKey()
  return circles

def childrenNotCircles(contours, hierarchy, parentContour):
  if hierarchy[0][parentContour][2] == -1:
    return True
  ret = True
  startContour = hierarchy[0][parentContour][2]
  curContour = startContour
  if -1 == hierarchy[0][curContour][0]:
    return not isCircle(contours[curContour])
  while ret and (-1 != hierarchy[0][curContour][0]):
    ret = not isCircle(contours[curContour])
    curContour = hierarchy[0][curContour][0]
  return ret

def additionalPass(imgs, circles, structure, high, low, triesLeft, img, imgR):
  low = low - 10
  imgs, contours, hierarchy = getContours(img, low)
  circles = selectCircles(contours, hierarchy, img.copy())
  structure.addCircles(circles)
  if not structure.sorted:
    high = high + 10
    imgs, contours, hierarchy = getContours(img, high)
    circles = selectCircles(contours, hierarchy, img.copy())
    structure.addCircles(circles)
    if not structure.sorted and triesLeft > 0:
      return additionalPass(imgs, circles, structure, high, low, triesLeft-1, img, imgR)
    else:
      return imgs, circles, structure
  else:
    return imgs, circles, structure

def firstPass(img, imgR, ROI=None):
  process = imgStack(img, scale = 2.0)
  structures = YeastField(imgR.copy())
  imgs, contours, hierarchy = getContours(img, 150)
  circles = selectCircles(contours, hierarchy, img.copy())
  structures.addCircles(circles)
  if not structures.sorted:
    imgs, circles, structures = additionalPass(imgs, circles, structures, 150, 150, 8, img, imgR)
  img2 = imgR.copy()
  img2 = cv2.drawContours(img2, contours, -1, (255,255,0), 1)
  for circle in circles:
    img2 = cv2.drawContours(img2, circle, 0, (0,255,255), 2)
  imgs.append(img2)
  img3 = imgR.copy()
  for structure in structures.strips:
    if structure.sorted:
      img3 = cv2.drawContours(img3, [structure.c1[0]], -1, (0,255,0), 1)
      #printData(structure, 0, "green")
      img3 = cv2.drawContours(img3, [structure.c2[0]], -1, (0,0,255), 1)
      #printData(structure, 1, "red")
      img3 = cv2.drawContours(img3, [structure.c3[0]], -1, (255,0,0), 1)
      #printData(structure, 2, "blue")
      img3 = cv2.drawContours(img3, [structure.c4[0]], -1, (0,255,255), 1)
      #printData(structure, 3, "yellow")
  if structures.sorted:
    imgs.append(img3)
  for i in imgs:
    process.addImg(i)
  return process.getImageStack(), imgs[-1], structures.sorted, structures

def getOffsetData(structure, circle, i, offset = True):
  if offset:
    off = structure.getCircleData(0,i)
  else:
    off = [0,0]
  a = structure.getCircleData(circle,i)[0] - off[0]
  b = structure.getCircleData(circle,i)[1] - off[1]
  return [a,b]

def printData(structure, circle, color):
  retStr = color + " R val = " + str(getOffsetData(structure, circle, 2)) + "\n"
  retStr += color + " G val = " + str(getOffsetData(structure, circle, 1)) + "\n"
  retStr += color + " B val = " + str(getOffsetData(structure, circle, 0)) + "\n"
  #print(retStr)
  return(retStr)

def saveDataOld(structure, circle, color):
  file1 = open('redAvg'+str(circle+1)+'.csv', mode='a')
  file2 = open('redInt'+str(circle+1)+'.csv', mode='a')
  #file3 = open('greenAvg'+str(circle+1)+'.csv', mode='a')
  #file4 = open('greenInt'+str(circle+1)+'.csv', mode='a')
  #file5 = open('blueAvg'+str(circle+1)+'.csv', mode='a')
  #file6 = open('blueInt'+str(circle+1)+'.csv', mode='a')
  file1.write(str(structure.getCircleData(circle,2)[1] - structure.getCircleData(0,2)[1])+', ')
  file2.write(str(structure.getCircleData(circle,2)[0] - structure.getCircleData(0,2)[0])+', ')
  #file3.write(str(structure.getCircleData(circle,1)[1])+', ')
  #file4.write(str(structure.getCircleData(circle,1)[0])+', ')
  #file5.write(str(structure.getCircleData(circle,0)[1])+', ')
  #file6.write(str(structure.getCircleData(circle,0)[0])+', ')
  return printData(structure, circle, color)

def getContours(img, threshold):
  blurred = img.copy()
  imgs = prepareImg(blurred, threshold)
  edges = cv2.Canny(imgs[-1], 40, 150, L2gradient=True)
  img, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  return imgs, contours, hierarchy

def prepareImg(blurred, threshold):
  imgs = []
  blurred = cv2.bilateralFilter(blurred, 3, 75, 75)
  imgs.append(blurred)
  blurred = customGrey(blurred)
  imgs.append(blurred)
  blurred = cv2.erode(blurred, (3,3), iterations = 2)
  imgs.append(blurred)
  blurred = cv2.dilate(blurred, (3,3), iterations = 1)
  imgs.append(blurred)
  ret, blurred = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
  imgs.append(blurred)
  #print(np.average(blurred))
  blurred = cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)
  imgs.append(blurred)
  return imgs

def customGrey(img):
  hsvImg = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
  base = hsvImg[:,:,2]
  maxVal = np.array(base).max()
  minVal = np.array(base).min()
  retImg = base - minVal
  retImg2 = np.multiply(retImg, (255.0/(maxVal-minVal)))
  retImg2 = retImg2.astype('uint8')
  return retImg2

def unGodlyHack(prefix):
  startImg = cv2.imread(prefix+'white.tiff')
  redImg = cv2.imread(prefix+'green.tiff')
  pass1, finalImg, data = fullProcess(startImg, redImg, prefix)
  finalImg = cv2.cvtColor(finalImg, cv2.COLOR_BGR2RGB)
  return finalImg

if __name__ == '__main__':
  prefix = '/Users/Diyogon/Downloads/m7/'
  for i in range(2,3):
    target = str(i)
    startImg = cv2.imread(prefix+'white '+target+'.tiff')
    redImg = cv2.imread(prefix+'red '+target+'.tiff')
    pass1, finalImg, data = fullProcess(startImg, redImg)
    cv2.imshow('frame',pass1)
    cv2.imshow('frame3',finalImg)
    cv2.waitKey()
  cv2.destroyAllWindows()