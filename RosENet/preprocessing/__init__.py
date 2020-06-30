from .compute_rosetta_energy import ComputeRosettaEnergy
from .make_pdbqt import MakePDBQT

def preprocess(pdb_object):
    ComputeRosettaEnergy.run_until(pdb_object,callbacks=[lambda x: print(x)])
    MakePDBQT.run_until(pdb_object,callbacks=[lambda x: print(x)])
