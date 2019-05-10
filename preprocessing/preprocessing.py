from string import Template
from make_complex_pdb import make_complex_pdb as _make_complex_pdb
from make_ligand_mol2_renamed import make_ligand_mol2_renamed as _make_ligand_mol2_renamed

def make_ligand_params_pdb(pdb_object):
    ligand_mol2_path = pdb_object.ligand.mol2.path
    params_filename = ligand_mol2_path.stem
    working_directory = ligand_mol2_path.parent
    return rosetta.run("molfile_to_params",
            cwd = working_directory,
            output = params_filename,
            input = ligand_mol2_path)

def make_complex_pdb(pdb_object):
    protein_path = pdb_object.protein.pdb.path
    ligand_path = pdb_object.ligand.pdb.path
    complex_path = pdb_object.complex.pdb.path
    return _make_complex_pdb(protein_path, ligand_path, complex_path)

def minimize_rosetta(pdb_object):
    generate_minimization_flags_file(pdb_object)
    generate_constraint_file(pdb_object)
    working_directory = pdb_object.path
    rosetta.run("minimize", cwd = working_directory)
    hide_not_minimal_complexes(pdb_object)

def generate_minimization_flags_file(pdb_object):
    complex_path = pdb_object.complex.pdb.path
    complex = str(complex_path.name)
    name = str(complex_path.stem)
    params = pdb_object.ligand.params.path
    template = Template(storage.read_plain(constants.flags_relax_path))
    substitution = {'complex' : complex,
                    'name' : name,
                    'params' : params}
    output = template.substitute(substitution)
    pdb_object.flags_relax.write(output)

def generate_constraint_file(pdb_object):
    complex = pdb_object.complex.read()
    output_path = pdb_object.constraints.path
    metals = complex.select(constants.metal_selector)
    result = []
    if metals:
      for atom in metals:
        pos = atom.getCoords()
        close_ligand = complex.select(constants.close_ligand_selector, t=pos)
        if close_ligand:
          for close in close_ligand:
            result.append((atom.getName(),
                           str(atom.getResnum())+atom.getChid(),
                           close.getName(),
                           str(close.getResnum())+close.getChid()))
    pdb_object.constraints.write(
            [f"AtomPair {r[0]} {r[1]} {r[2]} {r[3]} SQUARE_WELL 2.5 -2000\n" for r in results])

def hide_non_minimal_complexes(pdb_object):
    scores = rosetta.parse_scores(pdb_object.minimized.scores.read())
    hidden_folder = pdb_object.hidden_complexes.path
    storage.make_directory(hidden_folder)
    for number in scores.keys()[1:]:
        complex_path = pdb_object.minimized.complex.pdb[number].path
        ligand_path = pdb_object.minimized.ligand.mol2[number].path
        storage.move_file(complex_path, hidden_folder, no_fail=True)
        storage.move_file(ligand_path, hidden_folder, no_fail=True)

def make_protein_pdb(pdb_object):
    complex = pdb_object.minimized.complex.pdb.read()
    protein = complex.select(constants.protein_selector)
    pdb_object.minimized.protein.pdb.write(protein)

def make_ligand_mol2(pdb_object):
    complex_path = pdb_object.minimized.complex.pdb.path
    renamed_mol2_path = pdb_object.ligand.renamed_mol2.path
    ligand_path = pdb_object.minimized.ligand.mol2.path
    rosetta.run("pdb_to_molfile",
                mol = renamed_mol2_path,
                complex = complex_path,
                output = ligand_path)

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

def make_ligand_mol2_renamed(path):
    ligand_mol2_path = pdb_object.ligand.mol2.path
    output_path = pdb_object.ligand.renamed_mol2.path
    _make_ligand_mol2_renamed(ligand_mol2_path, output_path)

