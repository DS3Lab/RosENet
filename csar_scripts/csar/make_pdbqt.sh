#!/bin/bash
pythonsh="/cluster/scratch/hhussein/MGLTools-1.5.6/bin/pythonsh"
find /cluster/scratch/hhussein/Structures/ -type d -maxdepth 2 -mindepth 2 | parallel -n 1 bash $pythonsh preprocess_vina.py {}
