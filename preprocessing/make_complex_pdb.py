import numpy as np
from DrugDiscovery.preprocessing.make_ligand_params_pdb import MakeLigandParamsPDB
from DrugDiscovery.preprocessing.step import Step
from prody import parsePDB, writePDB
import DrugDiscovery.constants as constants
from htmd.molecule.molecule import Molecule
from htmd.molecule.voxeldescriptors import getVoxelDescriptors
from htmd.builder.preparation import proteinPrepare

def standardize_residues(structure):
    """Rename the residues of a structure to their standard names.

    structure : prody.AtomSelection
        Structure to be handled
    """
    residue_names = structure.getResnames()
    for nonstd, std in constants.nonstd2stdresidues.items():
        residue_names[residue_names==nonstd] = std
    structure.setResnames(residue_names)

def fix_chains(structure):
    """Rename chain names to reserve special names
    (W for water, X for ligand, Z for metals)

    structure : prody.AtomSelection
        Structure to be handled
    """
    chains = list(set(structure.getChids()))
    valid_chains = "ABCDEFGHIJKLMNOPQRSTUVwxYz0123456789abcdefghijklmnopqestuvy"
    chain_dict = dict(zip(chains, valid_chains[:len(chains)]))
    structure.setChids(np.vectorize(chain_dict.get)(structure.getChids()))

def fix_ligand_names(structure):
    """Rename ligand residue names and chain names to their reserved names.

    structure : prody.AtomSelection
        Structure to be handled
    """
    n_atoms = structure.numAtoms()
    structure.setResnames(np.array([constants.ligand_resname]*n_atoms))
    structure.setChids(np.array([constants.ligand_chid]*n_atoms))

def fix_water_chains(structure):
    """Rename water molecule chain to its reserved name.

    structure : prody.AtomSelection
        Structure to be handled
    """
    chains = structure.getChids()
    residues = structure.getResnames()
    chains[residues==constants.water_residue] = constants.water_chain
    structure.setChids(chains)

def fix_metal_chains(structure):
    """Rename metal atom chain to its reserved name.

    structure : prody.AtomSelection
        Structure to be handled
    """
    chains = structure.getChids()
    residues = structure.getResnames()
    for metal in constants.accepted_metals:
      chains[residues==metal] = constants.metal_chain
    structure.setChids(chains)

def cleanup_and_merge(pdb_object):
    """Apply fixes to protein and ligand structures and write complex.

    pdb_object : PDBObject
        PDB structure to be handled
    """
    protein = pdb_object.protein.pdb.read()
    ligand = pdb_object.ligand.pdb.read()
    fix_chains(protein)
    fix_ligand_names(ligand)
    complex = protein + ligand
    standardize_residues(complex)
    fix_water_chains(complex)
    fix_metal_chains(complex)
    pdb_object.complex.pdb.write(complex)

def protein_optimization(complex_path):
    """Optimize protein inside complex file and rewrite complex.

    complex_path : pathlib.Path
        Path to complex file
    """
    complex = Molecule(str(complex_path))
    prot = complex.copy(); prot.filter("protein")
    lig = complex.copy(); lig.filter(constants.ligand_selector)
    #prot = proteinPrepare(prot, pH=7.0)
    mol = Molecule(name="complex")
    mol.append(prot)
    mol.append(lig)
    mol.write(str(complex_path))

class MakeComplexPDB(metaclass=Step,requirements=[MakeLigandParamsPDB]):
    @classmethod
    def files(cls, pdb_object):
        """List of files being created

            pdb_object : PDBObject
                PDB structure being handled
        """
        return [pdb_object.complex.pdb]

    @classmethod
    def _run(cls, pdb_object):
        """Inner function for the preprocessing step.

        pdb_object : PDBObject
            PDB structure being handled
        """
        complex_path = pdb_object.complex.pdb.path
        cleanup_and_merge(pdb_object)
        protein_optimization(complex_path)
        complex = pdb_object.complex.pdb.read()
        standardize_residues(complex)
        pdb_object.complex.pdb.write(complex)

