#!/bin/bash
pythonsh="/cluster/scratch/hhussein/MGLTools-1.5.6/bin/pythonsh"
find /cluster/scratch/hhussein/pdbbind2018/ -type d -maxdepth 1 -mindepth 1 | sort | parallel -n 1 $pythonsh preprocess_vina.py {}
