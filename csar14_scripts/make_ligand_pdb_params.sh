#!/bin/bash

function make_params_pdb() {
  cd $(dirname "$1")
  mol=$(basename "$1")
  filename=$(basename "$1" .mol2)
  python2 /cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/scripts/python/public/molfile_to_params.py -n WER -p $filename --conformers-in-one-file --keep-names --clobber $mol
}
export -f make_params_pdb

find /cluster/scratch/hhussein/CSAR14 -name "*_ligand.mol2" | parallel -n 1 bash -c ": && make_params_pdb {}"
