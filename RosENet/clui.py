import multiprocessing
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
from argparse import ArgumentParser
from pathlib import Path
from RosENet.objects.model import ModelObject
from RosENet.objects.dataset import DatasetObject
from RosENet.preprocessing import preprocess
from RosENet.voxelization import voxelize
from RosENet.postprocessing import postprocess
from RosENet.preprocessing.minimize_rosetta import hide_non_minimal_complexes

def parse_arguments():
    """Parse arguments and perform the selected action."""
    arguments = sys.argv[1:]
    optional_parser = ArgumentParser()
    optional_parser.add_argument("--njobs", default=None)
    optional_parser.add_argument("--gpu", default=None)
    optional_parser.add_argument("extra", nargs="*")
    optional = optional_parser.parse_args(arguments)
    njobs = optional.njobs
    gpu = optional.gpu
    if njobs is None:
        njobs = multiprocessing.cpu_count()-1
    else:
        njobs = int(njobs)
    print("#####",njobs)
    print(optional.extra)
    arguments = optional.extra
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    if gpu is not None:
        os.environ["CUDA_VISIBLE_DEVICES"]=gpu
    from RosENet.network.network import train, evaluate, predict
    parser = ArgumentParser(description="RosENet Tool",
                            usage='''tool <command> [<args>]

preprocess		Compute steps previous to voxelization
voxelize		Compute 3D image voxelization
postprocess		Format image for TensorFlow
train			Train neural network
evaluate		Evaluate neural network
predict			Predict binding affinity
''')
    parser.add_argument("action", help='Command to run')
    parser.add_argument("dataset", help='Dataset path')
    args = parser.parse_args(arguments[0:2])
    action  = args.action
    dataset = DatasetObject(Path(args.dataset))
    if action in ["train", "evaluate", "predict"]:
        parser = ArgumentParser(usage=
'''{train,evaluate,predict} second_dataset network channels [seed]

second_dataset has the following meanings:
If action is train:     second_dataset is the validation dataset
If action is evaluate:  second_dataset is the evaluation dataset
If action is predict:   second_dataset is the prediction dataset

In training if no seed is given, it will be randomly chosen
The seed is necesary for evaluation and prediction to chose the
correct instance of the trained model.
''')
        parser.add_argument("validation_dataset")
        parser.add_argument("network")
        parser.add_argument("channels")
        parser.add_argument("seed", nargs="?", default=None)
        args = parser.parse_args(arguments[2:6])
        other_dataset= DatasetObject(Path(args.validation_dataset))
        network = ModelObject(Path(args.network))
        channels = args.channels
        seed = int(args.seed)
    if action in ["preprocess", "voxelize"]:
        import random
        pdbs = dataset.list()
        random.shuffle(pdbs)
        pdbs = map(dataset.__getitem__, pdbs)
        p = multiprocessing.Pool(gpu)
    if action == "preprocess":
        #p.map(hide_non_minimal_complexes, pdbs)
        p.map(preprocess, pdbs)
    elif action == "voxelize":
        p.map(voxelize, pdbs)
    elif action == "postprocess":
        postprocess(dataset)
    if action == "train":
        from RosENet.network.network import train
        train(dataset, other_dataset, network, seed, channels)
    elif action == "evaluate":
        from RosENet.network.network import evaluate
        evaluate(dataset, other_dataset, network, seed, channels)
    elif action == "predict":
        from RosENet.network.network import predict
        predict(dataset, other_dataset, network, seed, channels)
