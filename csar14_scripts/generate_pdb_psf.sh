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
    vmd -e $psf_script -args $file
  fi
} 
export -f process

find /cluster/scratch/hhussein/pdbbind2018 -name "*_protein.pdb" | parallel -n 1 bash -c ": && process {}"
