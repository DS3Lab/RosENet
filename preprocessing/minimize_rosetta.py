from DrugDiscovery.preprocessing.step import Step
from DrugDiscovery.preprocessing.make_complex_pdb import MakeComplexPDB
from string import Template
import DrugDiscovery.constants as constants
import DrugDiscovery.rosetta.rosetta as rosetta
import DrugDiscovery.storage.storage as storage

def generate_minimization_flags_file(pdb_object):
    """Generate minimization flags file for Rosetta minimization.

    pdb_object : PDBObject
        PDB structure to be handled
    """
    complex_path = pdb_object.complex.pdb.path
    complex = complex_path.name
    name = complex_path.stem
    params = pdb_object.ligand.params.path.name
    template = Template(storage.read_plain(constants.flags_relax_path))
    substitution = {'complex' : complex,
                    'name' : name,
                    'params' : params}
    output = template.substitute(substitution)
    pdb_object.flags_relax.write(output)

def generate_constraint_file(pdb_object):
    """Generate constraint file for Rosetta minimization.
    Constraints are added to maintain contact ions close to their original positions.

    pdb_object : PDBObject
        PDB structure to be handled
    """
    complex = pdb_object.complex.pdb.read()
    output_path = pdb_object.constraints.path
    metals = complex.select(constants.metal_selector)
    results = []
    if metals:
      for atom in metals:
          pos = atom.getCoords()
          close_ligand = complex.select(constants.close_ligand_selector, t=pos)
          if close_ligand:
            for close in close_ligand:
                results.append((atom.getName(),
                           str(atom.getResnum())+atom.getChid(),
                              close.getName(),
                             str(close.getResnum())+close.getChid()))
    pdb_object.constraints.write(
            [f"AtomPair {r[0]} {r[1]} {r[2]} {r[3]} SQUARE_WELL 2.5 -2000\n" for r in results])

def hide_non_minimal_complexes(pdb_object):
    """Generate constraint file for Rosetta minimization.
    Constraints are added to maintain contact ions close to their original positions.

    pdb_object : PDBObject
        PDB structure to be handled
    """
    scores = rosetta.parse_scores(pdb_object.minimized.scores.read())
    hidden_folder = pdb_object.minimized.hidden_complexes.path
    storage.make_directory(hidden_folder)
    for number in list(scores.keys())[1:]:
        complex_path = pdb_object.minimized.complex.pdb[number].path
        storage.move(complex_path, hidden_folder, no_fail=True)



class MinimizeRosetta(metaclass=Step, requirements=[MakeComplexPDB]):
    @classmethod
    def files(cls, pdb_object):
        """List of files being created

        pdb_object : PDBObject
            PDB structure being handled
        """
        return [pdb_object.flags_relax,
                pdb_object.constraints,
                pdb_object.minimized.hidden_complexes,
                pdb_object.minimized.complex.pdb,
                pdb_object.minimized.scores]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        generate_minimization_flags_file(pdb_object)
        generate_constraint_file(pdb_object)
        rosetta.minimize(working_directory = pdb_object.path)
        hide_non_minimal_complexes(pdb_object)

