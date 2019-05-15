"""
Storage module to centralize and abstract most of the IO operations in the project.
"""

from prody import parsePDB, writePDB
import shutil
import h5py
import json
import numpy as np
import tensorflow as tf

def delete(path):
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

def clear_directory(path, no_fail=True):
    if path.exists() and not no_fail:
        shutil.rmtree(path)
        make_directory(path)

def make_directory(path, no_fail=True):
    path.mkdir(exist_ok = no_fail, parents=True)

def move(origin, destination, no_fail=False):
    if origin.exists() or not no_fail:
        if destination.is_dir():
            destination = destination / origin.name
        origin.rename(destination)

def read_image(image_path):
    with h5py.File(str(image_path), "r") as f:
        return np.array(f["grid"])

def write_image(image_path, image):
    with h5py.File(str(image_path), "w", libver='latest') as f:
        f.create_dataset("grid", dtype='f4', data=image)

def read_json(json_path):
    with json_path.open("r") as f:
        data = json.load(f)
    return data

def write_json(json_path, data):
    with json_path.open("w") as f:
        json.dump(data, f) 

def read_pdb(pdb_path):
    return parsePDB(str(pdb_path))

def write_pdb(pdb_path, pdb):
    return writePDB(str(pdb_path), pdb)

def write_tfrecords(path, data):
    with tf.python_io.TFRecordWriter(str(path)) as writer:
        for datum in data:
            writer.write(datum)

def read_attributes(attr_path):
    return np.load(str(attr_path).strip(".npz")+".npz")

def write_attributes(attr_path, attributes):
    return np.savez(str(attr_path), attributes)

def read_plain(file_path):
    with open(file_path, "r") as f:
        data = f.read()
    return data

def write_plain(file_path, text):
    with open(file_path, "w") as f:
        if isinstance(text, str):
            f.write(text)
        elif isinstance(text, list):
            for line in text:
                f.write(line.strip("\n")+"\n")
        else:
            f.write(str(text))
