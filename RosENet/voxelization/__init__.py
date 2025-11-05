from .voxelizers import (VoxelizeHTMD, VoxelizeRosetta, VoxelizeElectronegativity,
                          VoxelizeXTBCharges, VoxelizeShape, VoxelizeHBondGeometry)
from RosENet.postprocessing.postprocessing import combine_maps
from RosENet import settings

def voxelize(pdb_object):
    try:
        VoxelizeHTMD(pdb_object, settings.size)
        VoxelizeRosetta(pdb_object, settings.voxelization, settings.size)
        VoxelizeElectronegativity(pdb_object, settings.voxelization, settings.size)
        VoxelizeXTBCharges(pdb_object, settings.voxelization, settings.size)
        VoxelizeShape(pdb_object, settings.size)
        VoxelizeHBondGeometry(pdb_object, settings.size)
        combine_maps(pdb_object)
    except:
        pass
