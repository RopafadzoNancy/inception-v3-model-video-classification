import numpy as np
import string
import pickle
import os
import cv2
import glob
import tempfile
import tensorflow
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications.inception_v3 import decode_predictions
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from pathlib import Path
import shutil
import streamlit as st
from PIL import Image
# create directory of frames that have been splitted
def create_dir(path):
  try:
    if not os.path.exists(path):
      path = os.makedirs(path)
  except OSError:
    print('Error!')

# create frames of a video
def save_frame(video, gap=75):
  name = str(video.name).split('.')[0]
  save_path = os.path.join(name)
  create_dir(save_path)
  tfile = tempfile.NamedTemporaryFile(delete=False)
  tfile.write(video.read())
  cap = cv2.VideoCapture(tfile.name)
  index = 0

  while True:
    ret, frame = cap.read()

    if ret == False:
      cap.release()
      break

    if index == 0:
      cv2.imwrite(f'{save_path}\\{index}.png', frame)
    else:
      if index % gap == 0:
        cv2.imwrite(f'{save_path}\\{index}.png', frame)
    index += 1

  return save_path

# checking the size of the video
def file_is_of_right_size(file_size):
  """ Get size of file at given path in bytes"""

#rejects the video if size>2mb
  if file_size < 2097152:
    proceed = True
  else:
    proceed = False

  return proceed

# checks if the directory has images or not
def dirIsEmpty(path):
  if os.path.exists(path) and not os.path.isfile(path):
  # Checking if the directory is empty or not
    if not os.listdir(path):
      empty_dir = True
    else:
      empty_dir = False
    return empty_dir

# the function process the images before feeding them into the model for prediction
def processed_image(image_path):
  image_one = image.load_img(image_path, target_size = (299, 299))
  image_array = image.img_to_array(image_one)
  img_array_expanded_dims = np.expand_dims(image_array, axis=0)
  return tf.keras.applications.inception_v3.preprocess_input(img_array_expanded_dims)

def saved_inception_v3(processed_image):
  new_model = load_model('models/model.h5')
  new_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
  prediction = new_model.predict(processed_image)
  return np.round(prediction)

# the function predict the objects with in the video frames
def predictions(images):
  prepared_image = processed_image(images)
  predictions = saved_inception_v3(prepared_image)
  results = decode_predictions(predictions, top=1)
  prediction = results[0][0][-1]
  name_of_obj_detected = results[0][0][1]
  return prediction, name_of_obj_detected

def selected_frames_path(image_path, image_name):
  source_path = image_path
  # creating the directory for selected frames
  if not os.path.exists("predict_2"):
    os.makedirs("predict_2")
  destination_path = f"predict_2\\{image_name}"
  return source_path, destination_path

def frame_predictor(images_dir, object_to_look):
  required_predictions = 0

  for images in glob.iglob(f'{images_dir}\\*'):

    if required_predictions >= 5:
      break
    else:
      prediction, object_name = predictions(images)
      # checking if the prediction of model > 0.5 and the name of object is the same with that requested by the user
      if prediction > 0.5 and object_to_look == object_name:
        print(f'{object_name} {prediction}')
        image_1 = str(images).split('\\')[-1]

        # moving the required frames into new directory dst_path 
        source_path, destination_path = selected_frames_path(images, image_1)
        shutil.move(source_path, destination_path)

        required_predictions += 1

@st.cache
def load_image(image_file):
  img = Image.open(image_file)
  return img

def video_processor(video_paths, object_to_look):

  # split the video into frames if it is of good size
  frames_path = save_frame(video_paths)

  # feed the frames into the model to have output
  frame_predictor(frames_path, object_to_look)

def main():

  video_file = st.file_uploader('Upload Video', type=["mp4"])
  if video_file is not None:
    file_size = video_file.size

    if file_is_of_right_size(file_size):
      user_input = st.text_input('Name of objects to detect: ')
      
      if st.button('Search'):

        video_processor(video_file, user_input)
        saved_frame_path = 'predict_2'
        if not dirIsEmpty(saved_frame_path):
          st.subheader(user_input)
          images = Path(saved_frame_path).glob('*.png')
          for img in images:
            st.image(load_image(img),caption=user_input, width=250)
        else:
          st.subheader('No frames of '+user_input+' found!')

    else:
      st.subheader('The video is large for processing')

if __name__ == '__main__':
  st.title("Object Detection Using pretrained inception V3 Deep Learning Model")

  st.subheader(' Upload a video, a maximum size of 2mb'.title())
  main()
