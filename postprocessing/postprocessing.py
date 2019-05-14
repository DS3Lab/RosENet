import numpy as np
import tensorflow as tf
from Repo.storage import storage

def combine_maps(pdb_object):
    features = [pdb_object.image.htmd.read(),
                pdb_object.image.electronegativity.read(),
                pdb_object.image.rosetta.read()]
    for image in features:
        print(image.shape)
    grid = np.concatenate(features, axis=-1)
    storage.make_directory(pdb_object.image.combined.path.parent)
    pdb_object.image.combined.write(grid)


def serialize_file(file, target):
    datapoint = storage.read_image(file)
    features = datapoint.flatten()
    label = bytes(file.stem,"utf-8")
    example = tf.train.Example(features=tf.train.Features(feature={
            'id' : tf.train.Feature(bytes_list=tf.train.BytesList(value=[label])),
            'X' : tf.train.Feature(float_list=tf.train.FloatList(value=features)),
            'y' : tf.train.Feature(float_list=tf.train.FloatList(value=np.array([target])))
            }))
    return example.SerializeToString()

def write_tfrecords(files, root_object, number, labels):
    output = [serialize_file(file, float(labels[file.stem])) for file in files]
    root_object.tfrecord(number).write(output)

def chunk_by_size(files, recommended_tf_size=float(100*(2**20))):
  average_size = sum(map(lambda x: x.stat().st_size, files)) / float(len(files))
  files_per_chunk = np.ceil(recommended_tf_size / average_size)
  chunks = int(np.ceil(float(len(files)) / files_per_chunk))
  return np.array_split(np.array(files), chunks)

def generate_tfrecords(dataset_object):
  files = dataset_object.images
  chunks= chunk_by_size(files)
  storage.clear_directory(dataset_object.tfrecords, no_fail=True)
  storage.make_directory(dataset_object.tfrecords, no_fail=True)
  lines = dataset_object.labels.read().splitlines()
  pdb_labels = dict([tuple(line.split(" ")) for line in lines])
  print(pdb_labels)
  for i, chunk in enumerate(chunks):
      write_tfrecords(chunk, dataset_object, i, pdb_labels)

