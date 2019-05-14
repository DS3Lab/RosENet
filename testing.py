from Repo.objects.pdb import PDBObject 
from Repo.objects.dataset import DatasetObject
from pathlib import Path
#from Repo.preprocessing.preprocessing import *
from Repo.voxelization.voxelizers import *
from Repo.voxelization.filter import exp_12, gaussian
from Repo.preprocessing.make_ligand_params_pdb import MakeLigandParamsPDB
from Repo.preprocessing.make_pdbqt import MakePDBQT

test_object = PDBObject(Path("/cluster/scratch/hhussein/test_dataset/10gs"))
MakePDBQT.run_until(test_object,callbacks=[lambda x: print(x)])
MakeLigandParamsPDB.clean(test_object)

#print(test_object.protein.pdb.read())

#make_ligand_params_pdb(test_object)
#make_complex_pdb(test_object)
#minimize_rosetta(test_object)
#make_protein_pdb(test_object)
#make_ligand_mol2_renamed(test_object)
#make_ligand_mol2(test_object)
#make_pdbqt(test_object)
#compute_rosetta_energy(test_object)

VoxelizeHTMD(test_object, 25)
#voxelize_rosetta(test_object, ("filter", exp_12), 25)
#voxelize_electronegativity(test_object, ("filter", exp_12), 25)
#obj = DatasetObject(Path("/cluster/scratch/hhussein/test_dataset"))
#obj.completed_steps("10gs")
#obj.complete("10gs", "test")
#obj.completed_steps("10gs")
