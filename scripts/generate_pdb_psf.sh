#!/bin/bash

script_folder=$(realpath $(dirname ${BASH_SOURCE[0]}))
module load vmd
psf_script=$script_folder/generate_psf.tcl
export psf_script

function process {
  file=$1
  folder=$(dirname $file)
  pdb_name=$(basename $folder)
  cd $folder
  if [ ! -f "${pdb_name}_protein_autopsf.pdb" ]; then
    python2 /cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/tools/protein_tools/scripts/clean_pdb.py $file ignorechain
    new_file=$(basename $file .pdb)
    echo $new_file
    vmd -e $psf_script -args ${new_file}_ignorechain.pdb
    mv ${new_file}_ignorechain_autopsf.pdb ${new_file}_autopsf.pdb
    mv ${new_file}_ignorechain_autopsf.psf ${new_file}_autopsf.psf
    rm ${new_file}_ignorechain.pdb
  fi
} 
export -f process

if [ $# -eq 1 ]; then
  rm "/cluster/scratch/hhussein/pdbbind2018/$1/$1_protein_autopsf.pdb"
  rm "/cluster/scratch/hhussein/pdbbind2018/$1/$1_protein_autopsf.psf"
  process "/cluster/scratch/hhussein/pdbbind2018/$1/$1_protein.pdb"
else
  find /cluster/scratch/hhussein/pdbbind2018 -name "*_protein.pdb" | parallel -n 1 bash -c ": && process {}"
fi
