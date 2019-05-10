import os
os.environ["CUDA_VISIBLE_DEVICES"]=""
import tensorflow as tf
import h5py
import numpy as np
from pathlib import Path
import pandas as pd
import shutil


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

def get_file_list(path):
  return list(folder.glob('*.hdf5'))

def split_dataset(files, train_percentage):
  n = len(files)
  indexes = np.arange(n)
  shuffled_indexes = np.random.permutation(indexes)

  percentages = np.arange(n,dtype=float) / n
  train_indexes = shuffled_indexes[percentages <= train_percentage]
  test_indexes = shuffled_indexes[percentages > train_percentage]
  train_files = [files[i] for i in train_indexes]
  test_files = [files[i] for i  in test_indexes]

  return train_files, test_files


def generate_tfrecord(files, output_file):
  pdb_labels = get_pdb_labels('PDBBind')
  with tf.python_io.TFRecordWriter(output_file) as writer:
    for file in files:
      pdb_code = file.stem[:4]
      with h5py.File(str(file)) as hdf5_file:
        datapoint = np.array(hdf5_file['grid'], dtype=np.float32)
        X = datapoint.flatten()
        y = np.array([pdb_labels[pdb_code]])
        example = tf.train.Example(features=tf.train.Features(feature={
          'X': tf.train.Feature(float_list=tf.train.FloatList(value=X)),
          'y': tf.train.Feature(float_list=tf.train.FloatList(value=y))
        }))
        writer.write(example.SerializeToString())
      file.unlink()
  print('Done writing {}'.format(output_file))

def chunk_by_size(files, recommended_tf_size=float(100*(2**20))):
  average_size = sum(map(lambda x: x.stat().st_size, files)) / float(len(files))
  files_per_chunk = np.ceil(recommended_tf_size / average_size)
  chunks = int(np.ceil(float(len(files)) / files_per_chunk))
  return np.array_split(np.array(files), chunks)

def hdf5_to_tfrecords(folder, split):
  files = get_file_list(folder)
  train_files, test_files = split_dataset(files, split)
  train_chunks = chunk_by_size(train_files)
  test_chunks = chunk_by_size(test_files)
  train_folder = folder / 'train'
  test_folder = folder / 'test'
  shutil.rmtree(train_folder, ignore_errors=True)
  shutil.rmtree(test_folder, ignore_errors=True)
  train_folder.mkdir(parents=True, exist_ok=True)
  test_folder.mkdir(parents=True, exist_ok=True)
  for i, chunk in enumerate(train_chunks):
    chunk_output = train_folder / 'train_{}.tfrecords'.format(i)
    generate_tfrecord(chunk, str(chunk_output))
    print('Generated {}'.format(chunk_output))
  for i, chunk in enumerate(test_chunks):
    chunk_output = test_folder / 'test_{}.tfrecords'.format(i)
    generate_tfrecord(chunk, str(chunk_output))
    print('Generated {}'.format(chunk_output))

def split_dataset_refined_core(files):
  pdb_core = get_pdb_core_set_list()
  train_files = [file for file in files if file.stem[:4] not in pdb_core]
  print(len(train_files))
  test_files = [file for file in files if file.stem[:4] in pdb_core and file.stem[5] == "_"]
  print(len(test_files))
  return train_files, test_files

def hdf5_to_tfrecords_refined_core(folder):
  files = get_file_list(folder)
  train_files, test_files = split_dataset_refined_core(files)
  train_chunks = chunk_by_size(train_files)
  test_chunks = chunk_by_size(test_files)
  train_folder = folder / 'train'
  test_folder = folder / 'test'
  shutil.rmtree(train_folder, ignore_errors=True)
  shutil.rmtree(test_folder, ignore_errors=True)
  train_folder.mkdir(parents=True, exist_ok=True)
  test_folder.mkdir(parents=True, exist_ok=True)
  for i, chunk in enumerate(train_chunks):
    chunk_output = train_folder / 'train_{}.tfrecords'.format(i)
    generate_tfrecord(chunk, str(chunk_output))
    print('Generated {}'.format(chunk_output))
  for i, chunk in enumerate(test_chunks):
    chunk_output = test_folder / 'test_{}.tfrecords'.format(i)
    generate_tfrecord(chunk, str(chunk_output))
    print('Generated {}'.format(chunk_output))


import argparse
parser = argparse.ArgumentParser(usage='%(prog)s A ? [B | C]')
parser.add_argument('-f', '--folder', dest='folder', default=str(Path.home()))
parser.add_argument('-c', '--core', dest='core', action='store_true')
parser.add_argument('-s', '--split', dest='split', type=float)

if __name__ == "__main__":
  args = parser.parse_args()
  folder = args.folder
  split = args.split
  folder = Path(folder)
  if args.core:
    hdf5_to_tfrecords_refined_core(folder) 
  else:
    hdf5_to_tfrecords(folder, split)

