#!/bin/bash
module load gcc/5.2.0
OLD=$LD_LIBRARY_PATH
LD_LIBRARY_PATH="$SCRATCH/apbs/lib:$LD_LIBRARY_PATH"
$SCRATCH/apbs/bin/apbs "$@" > /dev/null 2>&1

LD_LIBRARY_PATH=$OLD
