import numpy as np

def combine_maps(pdb_object):
    features = [image.read() 
            for name, image in pdb_object.image.__dict__.items() 
            if name != "combined"]
    grid = np.concatenate(features)
    pdb_object.image.combined.write(grid)

def generate_tfrecords(root_object):
    root_object.image.combined.
import os
os.environ["CUDA_VISIBLE_DEVICES"]=""
import tensorflow as tf
import h5py
import numpy as np
from pathlib import Path
import pandas as pd
import shutil

def serialize_file(file, target):
    datapoint = file.read()
    features = datapoint.flatten()
    example = tf.train.Example(features=tf.train.Features(feature={
        'X' : tf.train.Feature(float_list=tf.train.FloatList(value=features)),
        'y' : tf.train.Feature(float_list=tf.train.FloatList(value=np.array([target])))
        }))
    return example.SerializeToString()

def write_tfrecords(files, root_object, number):
    lines = root_object.labels.read()
    pdb_labels = dict([tuple(line.split(" ") for line in lines)])
    output = [serialize_file(file, pdb_labels[pdb_code]) for file in files]
    root_object.tfrecords[number].write(output)

def chunk_by_size(files, recommended_tf_size=float(100*(2**20))):
  average_size = sum(map(lambda x: x.stat().st_size, files)) / float(len(files))
  files_per_chunk = np.ceil(recommended_tf_size / average_size)
  chunks = int(np.ceil(float(len(files)) / files_per_chunk))
  return np.array_split(np.array(files), chunks)

def generate_tfrecords(root_object):
  files = root_object.image.combined.list()
  chunks= chunk_by_size(files)
  storage.clear_directory(root_object.tfrecords.path, no_fail=True)
  storage.make_directory(root_object.tfrecords.path, no_fail=True)
  for i, chunk in enumerate(chunks):
      root_object.tfrecords[i].write(
    chunk_output = train_folder / f'{i}.tfrecord'
    generate_tfrecord(chunk, str(chunk_output))

