import os
os.environ["CUDA_VISIBLE_DEVICES"]=""
import tensorflow as tf
import h5py
import numpy as np
from pathlib import Path
import pandas as pd
import shutil
import itertools
from collections import defaultdict

core_clusters = [['3AO4', '3ZSO', '3ZSX', '3ZT2', '4CIG'], ['1A30', '1EBY', '1G2K', '2QNQ', '3O9I'], ['3OE4', '3OE5', '3OZS', '3OZT'], ['2ZB1', '3E92', '3E93', '4F9W'], ['1BZC', '2HB1', '2QBP', '2QBQ', '2QBR'], ['2WEG', '3DD0', '3KWA', '3RYJ', '4JSZ'], ['2VVN', '2W4X', '2W66', '2WCA', '2XJ7'], ['2WVT', '2XII', '4J28', '4JFS', '4PCS'], ['1Z95', '3B5R', '3B65', '3B68', '3G0W'], ['2C3I', '3BGZ', '3JYA', '4K18', '5DWR'], ['1K1I', '1O3F', '1UTO', '3GY4', '4ABG'], ['2VKM', '3RSX', '3UDH', '4DJV', '4GID'], ['3ARP', '3ARQ'], ['3EBP'], ['2V00', '3PRS', '3PWW', '3URI', '3WZ8'], ['1QKT', '2P15', '2POG', '2QE4', '4MGD'], ['1R5Y', '1S38', '3GC5', '3GE7', '3RR4'], ['4AGN', '4AGP', '4AGQ', '5A7B', '5ABA'], ['1PS3', '3D4Z', '3DX1', '3DX2', '3EJR'], ['1PXN', '2FVD', '2XNB', '3PXF', '4EOR'], ['1LPG', '1MQ6', '1Z6E', '2XBV', '2Y5H'], ['3COY', '3COZ', '3IVG', '4DDH', '4DDK'], ['2WN9', '2WNC', '2X00', '2XYS', '2YMD'], ['1NC1', '1NC3', '1Y6R', '4F2W', '4F3C'], ['2FXS', '2IWX', '2VW5', '2WER', '2YGE'], ['3QGY', '4M0Y', '4QD6', '4RFM'], ['1OWH', '1SQA', '3KGP'], ['3QQS', '3R88', '3TWP', '4GKM', '4OWM'], ['1NVQ', '2BR1', '2BRB', '3JVR', '3JVS'], ['2R9W', '3GR2', '3GV9', '4JXS', '4KZ6'], ['1P1N', '1P1Q', '1SYI', '2AL5'], ['1BCU', '1OYT', '2ZDA', '3BV9', '3UTU'], ['3U8K', '3U8N', '3WTJ', '3ZDG', '4QAC'], ['1E66', '1GPK', '1GPN', '1H22', '1H23'], ['1O0H', '1U1B', '1W4O'], ['2ZCQ', '2ZCR', '2ZY1', '3ACW', '4EA2'], ['1VSO', '3FV1', '3FV2', '3GBB', '4DLD'], ['3NQ9', '3UEU', '3UEV', '3UEW', '3UEX'], ['3KR8', '4J21', '4J3L'], ['4E5W', '4IVB', '4IVC', '4IVD', '4K77'], ['3F3A', '3F3C', '3F3D', '3F3E', '4MME'], ['2V7A', '3K5V', '3MSS', '3PYY', '4TWP'], ['1QF1', '1Z9G', '3FCQ', '4TMN', '5TMN'], ['3CYZ'], ['2CBV', '2CET', '2J78', '2J7H', '2WBG'], ['2WTV', '3E5A', '3MYG', '3UO4', '3UP2'], ['3EHY', '3LKA', '3NX7', '3TSK', '4GR0'], ['3G2Z', '3G31', '4DE1', '4DE2'], ['3UI7', '3UUO', '4LLX', '4MRW', '4MRZ', '4MSN', '5C1W', '5C28', '5C2H'], ['4BKT', '4W9C', '4W9H', '4W9I', '4W9L'], ['1YC1', '2XDL', '2YKI', '3B27', '3RLR'], ['4E6Q', '4F09', '4GFM', '4HGE', '4JIA'], ['4CR9', '4CRA', '4CRC', '4TY7'], ['3CJ4', '3GNW', '4EO8', '4IH5', '4IH7'], ['2P4Y', '2YFE', '3B1M', '3FUR', '3U9Q'], ['4KZQ', '4KZU'], ['3P5O', '3U5J', '4LZS', '4OGJ', '4WIV'], ['1Q8T', '1Q8U', '1YDR', '1YDT', '3AG9'], ['2XB8', '3N76', '3N7A', '3N86', '4CIW']]

core2cluster = dict(itertools.chain(*[[(x,i) for x in y] for i, y in enumerate(core_clusters)]))

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
  if len(files) == 0:
    return np.array([])
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
  test_files = [file for file in files if file.stem[:4] in pdb_core]
  test_chunks = defaultdict(list)
  for file in test_files:
    cluster_id = core2cluster[file.stem[:4].upper()]
    test_chunks[cluster_id].append(file)
  return train_files, test_chunks

def hdf5_to_tfrecords_refined_core(folder):
  files = get_file_list(folder)
  train_files, test_chunks = split_dataset_refined_core(files)
  train_chunks = chunk_by_size(train_files)
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
  for i, chunk in test_chunks.items():
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

