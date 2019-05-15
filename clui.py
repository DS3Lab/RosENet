import multiprocessing
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
from argparse import ArgumentParser
from pathlib import Path
from DrugDiscovery.objects.model import ModelObject
from DrugDiscovery.objects.dataset import DatasetObject
from DrugDiscovery.preprocessing import preprocess
from DrugDiscovery.voxelization import voxelize
from DrugDiscovery.postprocessing import postprocess

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
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    if gpu is not None:
        os.environ["CUDA_VISIBLE_DEVICES"]=gpu
    from DrugDiscovery.network.network import train, evaluate, predict
    parser = ArgumentParser(description="DrugDiscovery Tool",
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
    args = parser.parse_args(arguments[1:3])
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
        args = parser.parse_args(arguments[3:7])
        other_dataset= DatasetObject(Path(args.validation_dataset))
        network = ModelObject(Path(args.network))
        channels = args.channels
        seed = int(args.seed)
    if action in ["preprocess", "voxelize"]:
        pdbs = dataset_object.list()
        pdbs = map(dataset_object.__getitem__, pdbs)
        p = multiprocessing.Pool(gpu)
    if action == "preprocess":
        p.map(preprocess, pdbs)
    elif action == "voxelize":
        p.map(voxelize, pdbs)
    elif action == "postprocess":
        postprocess(dataset)
    if action == "train":
        from DrugDiscovery.network.network import train
        train(dataset, other_dataset, network, seed, channels)
    elif action == "evaluate":
        from DrugDiscovery.network.network import evaluate
        evaluate(dataset, other_dataset, network, seed, channels)
    elif action == "predict":
        from DrugDiscovery.network.network import predict
        predict(dataset, other_dataset, network, seed, channels)
