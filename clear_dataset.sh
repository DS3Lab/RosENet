#! /bin/bash

DATASET_PATH=$1

find $DATASET_PATH -type f -name "metadata.json" | xargs rm
find $DATASET_PATH -type f -name "*_complex*" | xargs rm
find $DATASET_PATH -type f -name "*_ligand_*.*" | xargs rm
find $DATASET_PATH -type f -name "*_protein_*.*" | xargs rm
find $DATASET_PATH -type f -name "*_ligand.pdb" | xargs rm
find $DATASET_PATH -type f -name "*_ligand.params" | xargs rm
find $DATASET_PATH -type f -name "constraints" | xargs rm
find $DATASET_PATH -type f -name "flags_relax.txt" | xargs rm
find $DATASET_PATH -type f -name "score.sc" | xargs rm
find $DATASET_PATH -type d -name "other_complexes" | xargs rm -r

