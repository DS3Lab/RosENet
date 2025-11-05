from .compute_rosetta_energy import ComputeRosettaEnergy
from .make_pdbqt import MakePDBQT
from .compute_xtb_charges import ComputeXTBCharges

def preprocess(pdb_object):
    ComputeRosettaEnergy.run_until(pdb_object,callbacks=[lambda x: print(x)])
    MakePDBQT.run_until(pdb_object,callbacks=[lambda x: print(x)])
    ComputeXTBCharges.run_until(pdb_object,callbacks=[lambda x: print(x)])
