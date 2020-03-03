import cv2
import YeastImageProcessing
import YIP3

if __name__ == '__main__':
  cap = cv2.VideoCapture(0)
  ret, frame = cap.read()
  while(True):
    ret, frame = cap.read()
    frame = frame[240:481,426:855,:]
    #frame = cv2.resize(frame, None, fx=2.0, fy=2.0)

    gray1, f = YIP3.fullProcess(frame)
    cv2.imshow('frame',gray1)
    cv2.imshow('frame3',f)
    if cv2.waitKey() & 0xFF == ord('q'):
        break
  cap.release()
  cv2.destroyAllWindows()