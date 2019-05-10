#!/bin/bash
rosetta=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/source/bin/rosetta_scripts.static.linuxgccrelease
rosettadb=/cluster/scratch/hhussein/rosetta_bin_linux_2018.33.60351_bundle/main/database/
script_folder=$(pwd)
export rosetta
export rosettadb
export script_folder

function make_rosetta() {
  folder=$(dirname "$1")
  cd $(dirname "$1")
  if [ ! -f "processed" ]; then
    echo "################################################ $(basename $folder)"
    complex=$(basename "$1") name=$(basename "$1" .pdb) params="${name/complex/ligand}.params" envsubst < $script_folder/flags_relax.txt > "flags_relax.txt"
    echo $folder
    python3 $script_folder/get_closest_lig_atom.py ./$(basename "$1") ./constraints
    touch "processed"
    ($rosetta @flags_relax.txt -parser:protocol "$script_folder/relax.xml" -database $rosettadb ) && echo "Finished $(basename $folder) correctly"
  fi
}
export -f make_rosetta

if [ $# -eq 1 ]; then
  rm -f "/cluster/scratch/hhussein/pdbbind2018/$1/score.sc"
  rm -f "/cluster/scratch/hhussein/pdbbind2018/$1/processed"
  rm -f "/cluster/scratch/hhussein/pdbbind2018/$1/*_00*"
  bash -c "make_rosetta /cluster/scratch/hhussein/pdbbind2018/$1/$1_complex.pdb"
else
find /cluster/scratch/hhussein/pdbbind2018/ -name "*_complex.pdb" | shuf | parallel -j 24 -n 1 --ungroup  bash -c ": && make_rosetta {}"
fi
