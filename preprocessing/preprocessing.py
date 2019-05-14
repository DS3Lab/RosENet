from string import Template
from .make_complex_pdb import make_complex_pdb as _make_complex_pdb
from .make_ligand_mol2_renamed import make_ligand_mol2_renamed as _make_ligand_mol2_renamed
from .compute_rosetta_energy import compute_rosetta_energy as _compute_rosetta_energy
import Repo.rosetta.rosetta as rosetta
import Repo.storage.storage as storage 
import Repo.constants as constants
import subprocess

def make_ligand_params_pdb(pdb_object):
    ligand_mol2_path = pdb_object.ligand.mol2.path
    params_filename = ligand_mol2_path.stem
    working_directory = ligand_mol2_path.parent
    return rosetta.molfile_to_params(
            working_directory = working_directory,
            output_path = params_filename,
            input_path = ligand_mol2_path)

def make_complex_pdb(pdb_object):
    protein_path = pdb_object.protein.pdb.path
    ligand_path = pdb_object.ligand.pdb.path
    complex_path = pdb_object.complex.pdb.path
    return _make_complex_pdb(protein_path, ligand_path, complex_path)

def minimize_rosetta(pdb_object):
    generate_minimization_flags_file(pdb_object)
    generate_constraint_file(pdb_object)
    working_directory = pdb_object.path
    pdb_object.minimized.scores.delete()
    rosetta.minimize(working_directory = working_directory)
    hide_non_minimal_complexes(pdb_object)

def generate_minimization_flags_file(pdb_object):
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
    scores = rosetta.parse_scores(pdb_object.minimized.scores.read())
    hidden_folder = pdb_object.minimized.hidden_complexes.path
    hidden_folder.delete()
    storage.make_directory(hidden_folder)
    for number in list(scores.keys())[1:]:
        complex_path = pdb_object.minimized.complex.pdb[number].path
        storage.move(complex_path, hidden_folder, no_fail=True)

def make_protein_pdb(pdb_object):
    complex = pdb_object.minimized.complex.pdb.read()
    protein = complex.select(constants.protein_selector)
    pdb_object.minimized.protein.pdb.write(protein)

def make_ligand_mol2(pdb_object):
    complex_path = pdb_object.minimized.complex.pdb.path
    renamed_mol2_path = pdb_object.ligand.renamed_mol2.path
    ligand_path = pdb_object.minimized.ligand.mol2.path
    rosetta.pdb_to_molfile(
                mol = renamed_mol2_path,
                complex_path = complex_path,
                output_path = ligand_path)

def make_pdbqt(pdb_object):
    path = pdb_object.path
    subprocess.run([constants.mgl_python_path,
                    constants.preprocess_vina_path,
                    path])

def compute_rosetta_energy(pdb_object):
    complex_path = pdb_object.minimized.complex.pdb.path
    params = pdb_object.ligand.params.path
    output_path = pdb_object.minimized.complex.attr.path
    _compute_rosetta_energy(complex_path, params, output_path)

def make_ligand_mol2_renamed(pdb_object):
    ligand_pdb_path = pdb_object.ligand.pdb.path
    ligand_mol2_path = pdb_object.ligand.mol2.path
    output_path = pdb_object.ligand.renamed_mol2.path
    _make_ligand_mol2_renamed(ligand_pdb_path, ligand_mol2_path, output_path)

