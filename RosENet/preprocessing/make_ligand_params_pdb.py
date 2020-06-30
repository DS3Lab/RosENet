from RosENet.preprocessing.step import Step
import RosENet.rosetta.rosetta as rosetta

class MakeLigandParamsPDB(metaclass=Step):
    """Preprocessing step that create the ligand.params and ligand.pdb files at
    the beginning of the pipeline."""

    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.ligand.params,
                pdb_object.ligand.pdb]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        ligand_mol2_path = pdb_object.ligand.mol2.path
        params_filename = ligand_mol2_path.stem
        working_directory = ligand_mol2_path.parent
        return rosetta.molfile_to_params(
                working_directory = working_directory,
                output_path = params_filename,
                input_path = ligand_mol2_path)

