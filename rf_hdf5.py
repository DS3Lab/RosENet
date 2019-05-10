import os
os.environ["CUDA_VISIBLE_DEVICES"]=""
import tensorflow as tf
import numpy as np
from pathlib import Path
import pandas as pd
import shutil
from io import StringIO

def get_pdb_core_set_list():
  pdb_core = Path('/cluster/home/hhussein/scratch/core_set_list')
  with pdb_core.open('r') as core_list_file:
    pdb_lines = [x.replace('\n','') for x in core_list_file.readlines()]
  return set(pdb_lines)

def get_pdb_labels(source):
  if source == 'PDBBind':
    csv_file = '/cluster/home/hhussein/scratch/INDEX_refined_data.2018'
    csv = pd.read_csv(csv_file,
                      comment='#',
                      delim_whitespace=True,
                      header=None,
                      usecols=[0,3])
    return dict(zip(csv[0],csv[3]))

def rf_to_tfrecords():
  folder = Path('/cluster/scratch/hhussein/rf_score')
  filenames, features = read_data()
  train_filenames, train_features, test_filenames, test_features = split_data(filenames, features)
  train_folder = folder/'train'
  test_folder = folder/'test'
  shutil.rmtree(train_folder, ignore_errors=True)
  shutil.rmtree(test_folder, ignore_errors=True)
  train_folder.mkdir(parents=True, exist_ok=True)
  test_folder.mkdir(parents=True, exist_ok=True)
  chunk_output = train_folder / 'train_0.tfrecords'
  generate_tfrecord(train_filenames, train_features, str(chunk_output))
  print('Generated {}'.format(chunk_output))
  chunk_output = test_folder / 'test_0.tfrecords'
  generate_tfrecord(test_filenames, test_features, str(chunk_output))
  print('Generated {}'.format(chunk_output))

def generate_tfrecord(filenames, features, output_file):
  pdb_labels = get_pdb_labels('PDBBind')
  with tf.python_io.TFRecordWriter(output_file) as writer:
    for i in range(len(filenames)):
      X = features[i,:].flatten()
      y = np.array([pdb_labels[filenames[i]]]).flatten()
      example = tf.train.Example(features=tf.train.Features(feature={
        'X': tf.train.Feature(float_list=tf.train.FloatList(value=X)),
        'y': tf.train.Feature(float_list=tf.train.FloatList(value=y))
      }))
      writer.write(example.SerializeToString())
  print('Done writing {}'.format(output_file))

def split_data(filenames, features):
  pdb_core = get_pdb_core_set_list()
  train_idx = [i for i, file in enumerate(filenames) if file not in pdb_core]
  test_idx = [i for i, file in enumerate(filenames) if file in pdb_core]
  train_filenames = [filenames[i] for i in train_idx]
  test_filenames = [filenames[i] for i in test_idx]
  train_features = features[train_idx]
  test_features = features[test_idx]
  return train_filenames, train_features, test_filenames, test_features  

def read_data():
  data_path = '/cluster/home/hhussein/clean_rf_features'
  with open(data_path, 'r') as f:
    lines = f.readlines()
  filename = []
  features = []
  for i in range(len(lines)//2):
    filename.append(lines[2*i].split('/')[-1][:4])
    features.append(np.genfromtxt(StringIO(lines[2*i + 1]), delimiter="\t"))
  total_features = np.array(features)
  import pdb; pdb.set_trace()
  return filename, total_features
    

if __name__ == "__main__":
  rf_to_tfrecords()

