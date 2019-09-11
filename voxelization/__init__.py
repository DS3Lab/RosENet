from .voxelizers import VoxelizeHTMD, VoxelizeRosetta, VoxelizeElectronegativity
from DrugDiscovery.postprocessing.postprocessing import combine_maps
from DrugDiscovery import settings

def voxelize(pdb_object):
    try:
        VoxelizeHTMD(pdb_object, settings.size)
        VoxelizeRosetta(pdb_object, settings.voxelization, settings.size)
        VoxelizeElectronegativity(pdb_object, settings.voxelization, settings.size)
        combine_maps(pdb_object)
    except:
        pass
