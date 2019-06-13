import tensorflow as tf
import numpy as np
import os.path
import PIL
from PIL import Image, ImageEnhance, ImageStat
import time

def loadNN(nnet_file = 'tensor_100_9.nnet'):
  with open(nnet_file) as fin:
      content = fin.readlines()
  fin.close
  content = [x.strip() for x in content]
  drugs = ""
  exclude = ""
  model_checkpoint = ""
  typ = ""

  for line in content:
      if 'DRUGS' in line:
          drugs = line[6:].split(',')
      elif 'LANES' in line:
          exclude = line[6:]
      elif 'WEIGHTS' in line:
          model_checkpoint = line[8:]
      elif 'TYPE' in line:
          typ = line[5:]

  #test for Tensorflow
  if typ != "tensorflow":
      print('Not tensorflow network!')
      return
  else:
      return drugs, exclude, model_checkpoint, typ

def identify(image, drugs, exclude, model_checkpoint, typ):
    #reshape the image to an (1, 154587) vector
    image = np.mat(np.asarray(image).flatten())
    #create session
    with tf.Session() as sess:
        #load in the saved weights
        model_loc = "/home/pi/Documents/"+model_checkpoint
        saver = tf.train.import_meta_graph(model_loc+'.meta')
        saver.restore(sess, model_loc)#tf.train.latest_checkpoint('tf_checkpoints/', model_for_identification+'.index'))

        #get graph to extract tensors
        graph = tf.get_default_graph()
        pred = graph.get_tensor_by_name("pred:0")
        output = graph.get_tensor_by_name("output:0")
        X = graph.get_tensor_by_name("X:0")
        keep_prob = graph.get_tensor_by_name("keep_prob:0")

        #saver.restore(sess, model_for_identification)

        #find the prediction
        result = sess.run(pred, feed_dict={X: image, keep_prob: 1.})
        #we can look at the softmax output as well
        prob_array = sess.run(output, feed_dict={X: image, keep_prob: 1.})
        print("result",result,"prob",prob_array)

        #return result (add 1 as indexed from 1 not 0)
        return result[0], prob_array

def processImage(image_loc, drugs, exclude, model_checkpoint, typ):
  print(image_loc)
  print(drugs)
  print(exclude)
  print(model_checkpoint)
  print(typ)
  img = PIL.Image.open(image_loc)

  #check image rectified
  width, height = img.size
  if width != 730 or height != 1220:
      print("Image not rectified", width, height)

  #crop out active area
  img = img.crop((71, 359, 71+636, 359+490))
  #lanes split
  lane = []

  #loop over lanes
  for i in range(0,12):
      if chr(65+i) not in exclude:
          lane.append(img.crop((53*i, 0, 53*(i+1), 490)))

  #reconstruct
  imgout = Image.new("RGB", (53 * len(lane), 490))

  #loop over lanes
  for i in range(0,len(lane)):
      imgout.paste(lane[i], (53*i, 0, 53*(i+1), 490))

  #resize
  imgout = imgout.resize((227,227), Image.ANTIALIAS)
  imgout.save("roi.jpg")
  #catagorize
  predicted_drug, predicted_prob = identify(imgout, drugs, exclude, model_checkpoint, typ)
  return predicted_drug, predicted_prob

def readImage(image_loc, system):
  if system == 'Linux':
    import tensorflow as tf
    import numpy as np
    import os.path
    import PIL
    from PIL import Image, ImageEnhance, ImageStat
    import time
    drugs, exclude, model_checkpoint, typ = loadNN('/home/pi/Documents/msh_tanzania_3k_12.nnet')
    pd, pp = processImage(image_loc, drugs, exclude, model_checkpoint, typ)
    print(pd, pp)
    return drugs[pd], pp[0][pd]
  else:
    return 'AmoxTest', 1.0

if __name__ == '__main__':
  readImage("./PAD/33233/2018_11_26_16\/58\/31/processed.jpg")