from neopixel import *
import RPi.GPIO as io
import argparse
LED_COUNT      = 56      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor$
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def ribbonControl(r,g,b,w):
  io.setmode(io.BCM)
  io.setwarnings(False)
  io.setup(17, io.OUT)
  print(r,g,b,w)
  if r==0 and g==255 and b==0 and w==0:
    print("LED on")
    io.output(17,1)
  else:
    print("LED off")
    io.output(17,0)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Set LEDs to given rgbw values")
  parser.add_argument('integers', type=int, nargs=4)
  args = parser.parse_args()
  r = args.integers[0]
  g = args.integers[1]
  b = args.integers[2]
  w = args.integers[3]
  strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
  strip.begin()
  #G-d alone knows why it's ordered like this
  color = Color(g, r, b, w)
  for i in range(strip.numPixels()):
    strip.setPixelColor(i, color)
  strip.show()
  ribbonControl(r,g,b,w)
