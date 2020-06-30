from RosENet.preprocessing.step import Step
from RosENet.preprocessing.minimize_rosetta import MinimizeRosetta
import RosENet.constants as constants
import RosENet.rosetta.rosetta as rosetta

class MakeProteinPDB(metaclass=Step, requirements=[MinimizeRosetta]):
    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.minimized.protein.pdb]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        complex = pdb_object.minimized.complex.pdb.read()
        protein = complex.select(constants.protein_selector)
        pdb_object.minimized.protein.pdb.write(protein)

