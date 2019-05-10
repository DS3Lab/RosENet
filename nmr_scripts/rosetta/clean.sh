#!/bin/bash

function process {
folder=$(dirname $1)
if [ ! -f $folder/score.sc ]; then
  rm -f $folder/processed
  rm -f $folder/constraints
  rm -f $folder/flags_relax.txt
  rm -f $folder/*_complex_*.pdb
fi
}

export -f process

find /cluster/scratch/hhussein/NMR -name "processed" | parallel -n 1 bash -c ": && process"
