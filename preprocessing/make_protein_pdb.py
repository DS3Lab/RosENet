from Repo.preprocessing.step import Step
from Repo.preprocessing.minimize_rosetta import MinimizeRosetta
import Repo.constants as constants
import Repo.rosetta.rosetta as rosetta

class MakeProteinPDB(metaclass=Step, requirements=[MinimizeRosetta]):
    @classmethod
    def files(cls, pdb_object):
        return [pdb_object.minimized.protein.pdb]

    @classmethod
    def _run(cls, pdb_object):
        complex = pdb_object.minimized.complex.pdb.read()
        protein = complex.select(constants.protein_selector)
        pdb_object.minimized.protein.pdb.write(protein)

