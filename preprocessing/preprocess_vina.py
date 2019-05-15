"""
Module extracted from prepare_receptor4.py and prepare_ligand4.py from AutoDockTools scripts.
http://autodock.scripps.edu/faqs-help/how-to/how-to-prepare-a-receptor-file-for-autodock4
http://autodock.scripps.edu/faqs-help/how-to/how-to-prepare-a-ligand-file-for-autodock4
"""
import os 
from MolKit import Read
import MolKit.molecule
import MolKit.protein
from AutoDockTools.MoleculePreparation import AD4ReceptorPreparation, AD4LigandPreparation
import sys
import getopt


def preprocess_receptor(receptor_filename, outputfilename):
    repairs = ''
    charges_to_add = 'gasteiger'
    preserve_charge_types=None
    cleanup  = ""
    mode = "automatic"
    delete_single_nonstd_residues = False
    dictionary = None

    mols = Read(receptor_filename)
    mol = mols[0]
    preserved = {}
    if charges_to_add is not None and preserve_charge_types is not None:
        preserved_types = preserve_charge_types.split(',') 
        for t in preserved_types:
            if not len(t): continue
            ats = mol.allAtoms.get(lambda x: x.autodock_element==t)
            for a in ats:
                if a.chargeSet is not None:
                    preserved[a] = [a.chargeSet, a.charge]

    if len(mols)>1:
        ctr = 1
        for m in mols[1:]:
            ctr += 1
            if len(m.allAtoms)>len(mol.allAtoms):
                mol = m
    mol.buildBondsByDistance()

    RPO = AD4ReceptorPreparation(mol, mode, repairs, charges_to_add, 
                        cleanup, outputfilename=outputfilename,
                        preserved=preserved, 
                        delete_single_nonstd_residues=delete_single_nonstd_residues,
                        dict=dictionary)    

    if charges_to_add is not None:
        for atom, chargeList in preserved.items():
            atom._charges[chargeList[0]] = chargeList[1]
            atom.chargeSet = chargeList[0]

def preprocess_ligand(ligand_filename, outputfilename):
    verbose = None
    repairs = "" #"hydrogens_bonds"
    charges_to_add = 'gasteiger'
    preserve_charge_types=''
    cleanup  = ""
    allowed_bonds = "backbone"
    root = 'auto'
    check_for_fragments = True
    bonds_to_inactivate = ""
    inactivate_all_torsions = True
    attach_nonbonded_fragments = True
    attach_singletons = True
    mode = "automatic"
    dict = None

    mols = Read(ligand_filename)
    if verbose: print 'read ', ligand_filename
    mol = mols[0]
    if len(mols)>1:
        ctr = 1
        for m in mols[1:]:
            ctr += 1
            if len(m.allAtoms)>len(mol.allAtoms):
                mol = m
    coord_dict = {}
    for a in mol.allAtoms: coord_dict[a] = a.coords

    mol.buildBondsByDistance()
    if charges_to_add is not None:
        preserved = {}
        preserved_types = preserve_charge_types.split(',') 
        for t in preserved_types:
            if not len(t): continue
            ats = mol.allAtoms.get(lambda x: x.autodock_element==t)
            for a in ats:
                if a.chargeSet is not None:
                    preserved[a] = [a.chargeSet, a.charge]



    LPO = AD4LigandPreparation(mol, mode, repairs, charges_to_add, 
                            cleanup, allowed_bonds, root, 
                            outputfilename=outputfilename,
                            dict=dict, check_for_fragments=check_for_fragments,
                            bonds_to_inactivate=bonds_to_inactivate, 
                            inactivate_all_torsions=inactivate_all_torsions,
                            attach_nonbonded_fragments=attach_nonbonded_fragments,
                            attach_singletons=attach_singletons)
    if charges_to_add is not None:
        for atom, chargeList in preserved.items():
            atom._charges[chargeList[0]] = chargeList[1]
            atom.chargeSet = chargeList[0]
    bad_list = []
    for a in mol.allAtoms:
        if a in coord_dict.keys() and a.coords!=coord_dict[a]: 
            bad_list.append(a)
    if len(bad_list):
        print len(bad_list), ' atom coordinates changed!'    
        for a in bad_list:
            print a.name, ":", coord_dict[a], ' -> ', a.coords
    else:
        if verbose: print "No change in atomic coordinates"
    if mol.returnCode!=0: 
        sys.stderr.write(mol.returnMsg+"\n")

def process_folder(receptor, ligand):
    try:
      preprocess_receptor(receptor, receptor.replace('.pdb','.pdbqt'))
    except Exception, e:
      print 'Protein', receptor
      raise e
    try:
      preprocess_ligand(ligand, ligand.replace('.mol2','.pdbqt'))
    except Exception, e:
      print 'Ligand', ligand
      raise e

if __name__ == "__main__":
  process_folder(sys.argv[1], sys.argv[2])
