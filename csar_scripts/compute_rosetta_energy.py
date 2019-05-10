#!/usr/bin/env python3

from __future__ import print_function

import argparse
import os
import h5py
from pyrosetta.rosetta.protocols.scoring import Interface
from pyrosetta.rosetta import *
from pyrosetta import *
from pathlib import Path
import numpy as np
from multiprocessing import Pool, cpu_count
from collections import defaultdict
from pyrosetta.toolbox.atom_pair_energy import print_residue_pair_energies
init('-in:auto_setup_metals') #-mute core.conformation.Conformation')

def compute_atom_pair_energy(pdb_filename,  ligand_params, interface_cutoff = 21.0):
  if type(ligand_params) is str:
    ligand_params = [ligand_params]
  ligand_params = Vector1([str(ligand_params)])

  pose = Pose()
  res_set = pose.conformation().modifiable_residue_type_set_for_conf()
  res_set.read_files_for_base_residue_types( ligand_params )

  pose.conformation().reset_residue_type_set_for_conf( res_set )
  pose_from_file(pose, str(pdb_filename))
  scorefxn = create_score_function('ref2015')
  pose_score = scorefxn(pose)

  #detect interface
  fold_tree = pose.fold_tree()
  for jump in range(1, pose.num_jump()+1):
    name = pose.residue(fold_tree.downstream_jump_residue(jump)).name()
    if name == 'WER':
      break
  interface = Interface(jump)
  interface.distance(interface_cutoff)
  interface.calculate(pose)

  energies = []
  en = defaultdict(lambda:np.zeros((1,4)))
  keys = []
  for rnum1 in range(1, pose.total_residue() + 1):
    if interface.is_interface(rnum1):
      r1 = pose.residue(rnum1)
      for a1 in range(1, len(r1.atoms()) + 1):
        seq1 = pose.pdb_info().pose2pdb(rnum1).strip().replace(' ','-')
        at1 = r1.atom_name(a1).strip()
        key1 = seq1 + '-' + at1
        for rnum2 in range(rnum1+1, pose.total_residue() + 1):
          if interface.is_interface(rnum2):
            r2 = pose.residue(rnum2)
            for a2 in range(1, len(r2.atoms())+1):
              seq2 = pose.pdb_info().pose2pdb(rnum2).strip().replace(' ','-')
              at2 = r2.atom_name(a2).strip()
              key2 = seq2 + '-' + at2
              ee = etable_atom_pair_energies(r1, a1, r2, a2, scorefxn)
              if all(e == 0.0 for e in ee):
                continue
              en[key1] += np.array(ee)
              en[key2] += np.array(ee)
  energy_matrix = np.array([v for v in en.values()])
  return list(en.keys()), energy_matrix

def get_radii_and_charges(pdb_filename, ligand_params):
  keys = []
  charges = []
  radii = []

  if type(ligand_params) is str:
    ligand_params = [ligand_params]
  ligand_params = Vector1([str(ligand_params)])

  pose = Pose()
  res_set = pose.conformation().modifiable_residue_type_set_for_conf()
  res_set.read_files_for_base_residue_types(ligand_params)

  pose.conformation().reset_residue_type_set_for_conf(res_set)
  pose_from_file(pose, str(pdb_filename))
  for rnum1 in range(1, pose.total_residue() + 1):
      r1 = pose.residue(rnum1)
      for a1 in range(1, len(r1.atoms()) + 1):
          seq1 = pose.pdb_info().pose2pdb(rnum1).strip().replace(' ','-')
          at1 = r1.atom_name(a1).strip()
          key1 = seq1 + '-' + at1
          charges.append(r1.atomic_charge(a1))
          radii.append(r1.atom_type(a1).lj_radius())
          keys.append(key1)

  return keys, charges, radii

def extract_and_save(pdb_file):
  folder = pdb_file.parent
  pdb_code = folder.stem
  ligand_params = folder / f'{pdb_code}_ligand.params'
  output_file = folder / (pdb_file.stem + '.attr')
  try:
    e_keys, e_values = compute_atom_pair_energy(pdb_file,  ligand_params)
    rc_keys, charges, radii = get_radii_and_charges(pdb_file,  ligand_params)
  except Exception as e:
    print("Error at ", pdb_file)
    print(e)
    return
  energy_keys = np.array(e_keys)
  energy_values = np.array(e_values)
  rc_keys = np.array(rc_keys)
  radius_values = np.array(radii)
  charge_values = np.array(charges)
  np.savez_compressed(str(output_file), 
                      energy_keys=e_keys,
                      energy_values=energy_values,
                      rc_keys=rc_keys,
                      radius_values=radius_values,
                      charge_values=charge_values)
  print("COMPLETED", pdb_file)

def update_radii_charges(pdb_file):
  folder = pdb_file.parent
  pdb_code = folder.stem
  print(pdb_code)
  ligand_params = folder / f'{pdb_code}_ligand.params'
  output_file = folder / (pdb_file.stem + '.attr')
  rc_keys, charges, radii = get_radii_and_charges(pdb_file,  ligand_params)
  rc_keys = np.array(rc_keys)
  radius_values = np.array(radii)
  charge_values = np.array(charges)
  old_data = np.load(str(output_file) + '.npz')
  e_keys = old_data['energy_keys']
  energy_values = old_data['energy_values']
  np.savez_compressed(str(output_file),
                      energy_keys=e_keys,
                      energy_values=energy_values,
                      rc_keys=rc_keys,
                      radius_values=radius_values,
                      charge_values=charge_values)



def get_files(folder):
  return [x for x in folder.glob('*/*_complex_*.pdb') if not (x.parent/(x.stem +'.attr.npz')).exists()]

def get_fix_files(folder):
  return [x for x in folder.glob('*/*_complex_*.pdb') if (x.parent/(x.stem +'.attr.npz')).exists()]

if __name__ == "__main__":
  print(cpu_count())
  p = Pool(cpu_count()//3)
  p.map(extract_and_save, get_files(Path('/cluster/scratch/hhussein/Structures/set1/')))
  p.map(extract_and_save, get_files(Path('/cluster/scratch/hhussein/Structures/set2/')))
