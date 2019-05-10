def standardize_residues(structure):
    residue_names = structure.getResnames()
    for nonstd, std in constants.nonstd2stdresidues:
        residue_names[residue_names==nonstd] = std
    structure.setResnames(residue_names)

def fix_chains(structure):
    chains = set(structures.getChids())
    valid_chains = "ABCDEFGHIJKLMNOPQRSTUVwxYz0123456789abcdefghijklmnopqestuvy"
    chain_dict = dict(zip(chains, valid_chains[:len(chains)]))
    structure.setChids(np.vectorize(chain_dict.get)(chains))

def fix_ligand_names(structure):
    n_atoms = structure.numAtoms()
    structure.setResnames(np.array([constants.ligand_resname]*n_atoms))
    structure.setChids(np.array([constants.ligand_chid]*n_atoms))

def fix_water_chains(structure):
    chains = structure.getChids()
    residues = structure.getResnames()
    chains[residues==constants.water_residue] = constants.water_chain
    structure.setChids(chains)

def fix_metal_chains(structure):
    chains = structure.getChids()
    residues = structure.getResnames()
    for metal in constants.accepted_metals:
      chain[res==metal] = constants.metal_chain
    structure.setChids(chains)

def cleanup_and_merge(protein_path, ligand_path, complex_path):
    protein = parsePDB(str(protein_path))
    ligand = parsePDB(str(ligand_path))
    fix_chains(protein)
    fix_ligand_names(ligand)
    complex = protein + ligand
    standardize_residues(complex)
    fix_water_chains(complex)
    fix_metal_chains(complex)
    writePDB(str(complex_path), complex)

def protein_optimization(complex_path):
    complex = Molecule(str(complex_path))
    prot = complex.copy(); prot.filter("protein")
    lig = complex.copy(); lig.filter(constants.ligand_selector)
    prot = proteinPrepare(prot, pH=7.0)
    mol = Molecule(name="complex")
    mol.append(prot)
    mol.append(lig)
    mol.write(str(complex_path))

def make_complex_pdb(protein_path, ligand_path, output_path):
    cleanup_and_merge(protein_path, ligand_path, output_path)
    protein_optimization(output_path)
    complex = parsePDB(str(complex_pdb))
    standardize_residues(complex)
    writePDB(str(complex_pdb), complex)
