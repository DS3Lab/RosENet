#!/bin/bash

function process {
folder=$(dirname $1)
if [ ! -f $folder/score.sc ]; then
  rm $folder/processed
fi
}

export -f process

find /cluster/scratch/hhussein/pdbbind2018/ -name "processed" | parallel -n 1 bash -c ": && process"
