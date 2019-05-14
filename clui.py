import multiprocessing
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from Repo.objects.dataset import DatasetObject
from Repo.preprocessing import preprocess
from Repo.voxelization import voxelize
from Repo.postprocessing import postprocess

def parse_arguments():
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
    from Repo.network.network import train, evaluate, predict
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
    dataset = Path(args.dataset)
    if action in ["train", "evaluate", "predict"]:
        parser = ArgumentParser()
        parser.add_argument("validation_dataset")
        parser.add_argument("network")
        parser.add_argument("channels")
        parser.add_argument("seed", default=None, required=False)
        args = parser.parse_args(arguments[3:7])
        other_dataset= DatasetObject(Path(args.validation_dataset))
        network = args.network
    dataset_object = DatasetObject(dataset)
    if action in ["preprocess", "voxelize"]:
        pdbs = dataset_object.list()
        pdbs = map(dataset_object.__getitem__, pdbs)
        p = multiprocessing.Pool(gpu)
    if action == "preprocess":
        p.map(preprocess, pdbs)
    elif action == "voxelize":
        p.map(voxelize, pdbs)
    elif action == "postprocess":
        postprocess(dataset_object)
    if action == "train":
        from Repo.network.network import train
        train(dataset, other_dataset, network, seed, channels)
    elif action == "evaluate":
        from Repo.network.network import evaluate
        evaluate(dataset, other_dataset, network, seed, channels)
    elif action == "predict":
        from Repo.network.network import predict
        predict(dataset, other_dataset, network, seed, channels)

#def preprocess(pdb_object):
#    ComputeRosettEnergies.run_until(pdb_object,callbacks=[lambda x: print(x)])
#    MakePDBQT.run_until(pdb_object,callbacks=[lambda x: print(x)])
#
#def voxelize(pdb_object):
#    VoxelizeHTMD(test_object, settings.size)
#    VoxelizeRosetta(test_object, settings.voxelization, settings.size)
#    VoxelizeElectronegativity(test_object, settings.voxelization, settings.size)
#    combine_maps(pdb_object)

#def postprocess(dataset_object):
#    generate_tfrecords(dataset_object)
