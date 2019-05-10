#!/bin/bash
file="$HOME/minimized_folders_new"
while mapfile -t -n 24 ary && ((${#ary[@]})); do
    for folder in "${ary[@]}"; do
        python compute_rosetta_energy.py --root_folder $folder &
    done
    wait
done < $file
