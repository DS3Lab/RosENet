import numpy as np
import tensorflow as tf
from RosENet.storage import storage

def combine_maps(pdb_object):
    """Postprocessing step for combining the feature map images into one image

    Parameters
    ----------
    pdb_object : PDBObject
        PDB object which images will be combined
    """
    features = [pdb_object.image.htmd.read(),
                pdb_object.image.electronegativity.read(),
                pdb_object.image.rosetta.read()]
    grid = np.concatenate(features, axis=-1)
    storage.make_directory(pdb_object.image.combined.path.parent)
    pdb_object.image.combined.write(grid)


def serialize_file(file, target, type):
    """Serialize image file to Tensorflow serialized format

    Parameters
    ----------
    file : pathlib.Path
        Path for the image file.
    target : float
        Ground truth binding affinity for the image.
    """
    datapoint = storage.read_image(file)
    features = datapoint.flatten()
    label = bytes(file.stem,"utf-8")
    type = 0 if type == "Kd" else 1
    example = tf.train.Example(features=tf.train.Features(feature={
            'id' : tf.train.Feature(bytes_list=tf.train.BytesList(value=[label])),
            'X' : tf.train.Feature(float_list=tf.train.FloatList(value=features)),
            'y' : tf.train.Feature(float_list=tf.train.FloatList(value=np.array([target]))),
            'type' : tf.train.Feature(int64_list=tf.train.Int64List(value=[type]))
            }))
    return example.SerializeToString()

def write_tfrecords(files, dataset_object, number, labels):
    """Serialize the given images and store them in a TFRecords file, together with their binding affinity values.

    files : list of pathlib.Path
        List of files to be written inside the TFRecords file.
    dataset_object : DatasetObject
        Dataset of the images.
    number : int
        ID number of the TFRecords file.
    labels : dict
        Dictionary relating image names to their binding affinities.
    """
    output = [serialize_file(file, float(labels[file.stem][0]), labels[file.stem][1]) for file in files]
    dataset_object.tfrecord(number).write(output)

def chunk_by_size(files, recommended_tf_size=float(100*(2**20))):
    """Split the images into chunks according to the TFRecords recommended size, which is 100MB.

    files : list of pathlib.Path
        List of image paths to be split.
    recommended_tf_size : float
        Maximum size of each chunk, 100MB by default.
    """
    average_size = sum(map(lambda x: x.stat().st_size, files)) / float(len(files))
    files_per_chunk = np.ceil(recommended_tf_size / average_size)
    chunks = int(np.ceil(float(len(files)) / files_per_chunk))
    return np.array_split(np.array(files), chunks)

def generate_tfrecords(dataset_object):
    """Generate TFRecords from a dataset's combined images.

    dataset_object : DatasetObject
        Dataset of the images.
    """
    files = dataset_object.images
    chunks= chunk_by_size(files)
    storage.clear_directory(dataset_object.tfrecords, no_fail=True)
    storage.make_directory(dataset_object.tfrecords, no_fail=True)
    lines = dataset_object.labels.read().splitlines()
    lines = [line.split(" ") for line in lines]
    pdb_labels = dict([(line[0],line[1:]) for line in lines])
    for i, chunk in enumerate(chunks):
        write_tfrecords(chunk, dataset_object, i, pdb_labels)

