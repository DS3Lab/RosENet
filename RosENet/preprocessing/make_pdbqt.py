from RosENet.preprocessing.step import Step
from RosENet.preprocessing.make_protein_pdb import MakeProteinPDB
from RosENet.preprocessing.make_ligand_mol2 import MakeLigandMOL2
import RosENet.constants as constants
import subprocess

class MakePDBQT(metaclass=Step, requirements=[MakeProteinPDB, MakeLigandMOL2]):
    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.minimized.ligand.pdbqt,
                pdb_object.minimized.protein.pdbqt]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        subprocess.run([constants.mgl_python_path,
                        constants.preprocess_vina_path,
                        pdb_object.minimized.protein.pdb.path,
                        pdb_object.minimized.ligand.mol2.path])

