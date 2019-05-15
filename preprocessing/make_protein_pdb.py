from DrugDiscovery.preprocessing.step import Step
from DrugDiscovery.preprocessing.minimize_rosetta import MinimizeRosetta
import DrugDiscovery.constants as constants
import DrugDiscovery.rosetta.rosetta as rosetta

class MakeProteinPDB(metaclass=Step, requirements=[MinimizeRosetta]):
    @classmethod
    def files(cls, pdb_object):
        return [pdb_object.minimized.protein.pdb]

    @classmethod
    def _run(cls, pdb_object):
        complex = pdb_object.minimized.complex.pdb.read()
        protein = complex.select(constants.protein_selector)
        pdb_object.minimized.protein.pdb.write(protein)

