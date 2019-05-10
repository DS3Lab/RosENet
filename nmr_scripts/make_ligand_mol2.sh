#!/bin/bash
script=/cluster/home/hhussein/scratch/rosetta_bin_linux_2018.33.60351_bundle/main/source/src/apps/public/ligand_docking/pdb_to_molfile.py
export script

function make_ligand_mol2() {
  dir=$(dirname $1)
  complex=$1
  name=$(basename "$1" .pdb)
  code=$(echo $name | cut -f 1 -d "_")
  mol="$dir/${code}_ligand_renamed.mol2"
  out=$dir/${name/complex/ligand}.mol2
  python2 $script $mol $complex > $dir/${name/complex/ligand}.mol2
}
export -f make_ligand_mol2

find /cluster/scratch/hhussein/NMR -name "*_complex_*.pdb" -maxdepth 2 | parallel -n 1 bash -c ": && make_ligand_mol2 {}"
