from Repo.preprocessing.step import Step
import Repo.rosetta.rosetta as rosetta

class MakeLigandParamsPDB(metaclass=Step):

    @classmethod
    def files(cls, pdb_object):
        return [pdb_object.ligand.params,
                pdb_object.ligand.pdb]

    @classmethod
    def _run(cls, pdb_object):
        ligand_mol2_path = pdb_object.ligand.mol2.path
        params_filename = ligand_mol2_path.stem
        working_directory = ligand_mol2_path.parent
        return rosetta.molfile_to_params(
                working_directory = working_directory,
                output_path = params_filename,
                input_path = ligand_mol2_path)

