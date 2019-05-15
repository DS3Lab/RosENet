from DrugDiscovery.preprocessing.step import Step
from DrugDiscovery.preprocessing.make_protein_pdb import MakeProteinPDB
from DrugDiscovery.preprocessing.make_ligand_mol2 import MakeLigandMOL2
import DrugDiscovery.constants as constants
import subprocess

class MakePDBQT(metaclass=Step, requirements=[MakeProteinPDB, MakeLigandMOL2]):
    @classmethod
    def files(cls, pdb_object):
        return [pdb_object.minimized.ligand.pdbqt,
                pdb_object.minimized.protein.pdbqt]

    @classmethod
    def _run(cls, pdb_object):
        subprocess.run([constants.mgl_python_path,
                        constants.preprocess_vina_path,
                        pdb_object.minimized.protein.pdb.path,
                        pdb_object.minimized.ligand.mol2.path])

