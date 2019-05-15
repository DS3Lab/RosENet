from DrugDiscovery.preprocessing.step import Step
import DrugDiscovery.rosetta.rosetta as rosetta
from DrugDiscovery.preprocessing.make_ligand_mol2_renamed import MakeLigandMOL2Renamed

class MakeLigandMOL2(metaclass=Step,requirements=[MakeLigandMOL2Renamed]):
    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.minimized.ligand.mol2]


    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        complex_path = pdb_object.minimized.complex.pdb.path
        renamed_mol2_path = pdb_object.ligand.renamed_mol2.path
        ligand_path = pdb_object.minimized.ligand.mol2.path
        rosetta.pdb_to_molfile(
                    mol = renamed_mol2_path,
                    complex_path = complex_path,
                    output_path = ligand_path)
