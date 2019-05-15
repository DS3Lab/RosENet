import random
import tensorflow as tf
import numpy as np
from DrugDiscovery.network.utils import random_rot, rots_90, random_rot_90, all_rot_90
import DrugDiscovery.settings as settings

def parse_fn(training,shape):
    def fn(example):
        example_fmt = {
        "id": tf.VarLenFeature(tf.string),
        "X": tf.FixedLenFeature((int(np.prod(shape)),), tf.float32),
        "y": tf.FixedLenFeature((1,), tf.float32)
        }
        parsed = tf.parse_single_example(example, example_fmt)
        X = tf.reshape(parsed['X'], shape=list(shape))
        y = parsed['y']
        id = parsed['id'].values
        return id, X, y
    return fn

def rotate_fn(training, shape):
    def fn(id, X, y):
        if training:
            X = random_rot_90(X,list((-1,) + tuple(shape)))
        else:
            X = all_rot_90(X, list((-1,) + tuple(shape)))
        return id, X, y
    return fn

def take_channels(ch, channel_order):
    idx = [i for i,x in enumerate(channel_order) if x in ch]
    def f(id, X, y):
        ret = tf.gather(X,idx,axis=-1)
        return id, ret, y
    return ch, f

def make_input_fn(input_path, shape, training, rot, merge):
    def in_fn():
        channel_order = ['htmd_hydrophobic',
                         'htmd_aromatic',
                         'htmd_hbond_acceptor',
                         'htmd_hbond_donor',
                         'htmd_positive_ionizable',
                         'htmd_negative_ionizable',
                         'htmd_metal',
                         'htmd_occupancies',
                         'htmd_hydrophobic',
                         'htmd_aromatic',
                         'htmd_hbond_acceptor',
                         'htmd_hbond_donor',
                         'htmd_positive_ionizable',
                         'htmd_negative_ionizable',
                         'htmd_metal',
                         'htmd_occupancies',
                         'elec_p',
                         'elec_l',
                         'rosetta_atr_p',
                         'rosetta_rep_p',
                         'rosetta_sol_p_pos',
                         'rosetta_elec_p_pos',
                         'rosetta_sol_p_neg',
                         'rosetta_elec_p_neg',
                         'rosetta_atr_l',
                         'rosetta_atr_p',
                         'rosetta_sol_l_pos',
                         'rosetta_elec_l_pos',
                         'rosetta_sol_l_neg',
                         'rosetta_elec_l_neg']
        files = tf.data.Dataset.list_files(str(input_path))
        dataset = files.apply(
                    tf.data.experimental.parallel_interleave(tf.data.TFRecordDataset,
                                                             settings.parallel_calls))
        dataset = dataset.map(parse_fn(training,shape), settings.parallel_calls)
        take = list(channel_order)
        filts = []
        if "rosetta" in merge:
              filts.append(lambda x: "rosetta" in x)
        if "electronegativity" in merge:
            filts.append(lambda x: x.startswith("elec"))
        if "htmd" in merge:
            filts.append(lambda x: "htmd" in x)
        take = [x for x in take if any([f(x) for f in filts])]
        channel_order, take_fn = take_channels(take, channel_order)
        dataset = dataset.map(take_fn, settings.parallel_calls)
        seed_t = tf.py_func(lambda : random.randint(0,214748364), [], tf.int64)
        dataset = dataset.shuffle(settings.shuffle_buffer_size, seed=seed_t)
        shape[-1] = len(channel_order)
        if not training and rot:
            dataset = dataset.batch(20)
        else:
            dataset = dataset.batch(settings.batch_size)
            dataset = dataset.prefetch(buffer_size=settings.prefetch_buffer_size)
        if rot:
            dataset = dataset.map(rotate_fn(training,shape),settings.parallel_calls)
        return dataset
    return in_fn

def load_fn(dataset_object, channels, rotate, training):
	name = dataset_object.name
	shape = [settings.size]*3 + [30]
	training = (training == tf.estimator.ModeKeys.TRAIN)
	dataset_files = dataset_object.tfrecords / '*.tfrecords'
	return make_input_fn(dataset_files, shape, training, rotate, channels)

