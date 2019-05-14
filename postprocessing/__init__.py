from .postprocessing import generate_tfrecords

def postprocess(dataset_object):
    generate_tfrecords(dataset_object)
