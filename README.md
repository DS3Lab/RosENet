<img src="logo.png" align="left" width="300">

# RosENet

This is the repository for the RosENet project.

RosENet: A 3D Convolutional Neural Network for predicting absolute binding affinity using molecular mechanics energies

Hussein Hassan-Harrirou¹, Ce Zhang¹, Thomas Lemmin <sup>1,2,*</sup>

¹DS3Lab, System Group, Department of Computer Sciences, ETH Zurich, CH-8092 Zurich, Switzerland

²Institute of Medical Virology, University of Zurich (UZH), CH-8057 Zurich, Switzerland

\*corresponding author: thomas.lemmin@inf.ethz.ch

## Prerequisites

A script `install.sh` is included, which creates a Conda environment and install the necessary requirements.

Rosetta and Pyrosetta must be installed manually due to the required license.

Pyrosetta can be copied next to the RosENet folder or by adding it to the `PYTHONPATH`.

You must set the path to Rosetta's main folder in the attribute `rosetta.root` in file `RosENet/constants.py` [LINK](RosENet/constants.py#L65)

## How to run

This repository is built as a Python module. To execute it, one should go above the root folder and run the following command:

```
python3 -m RosENet -- arguments
```

Currently, six actions are implemented:

1. preprocess
2. voxelize
3. postprocess
4. train
5. evaluate
6. predict

These actions are also thought to be executed in this order.
Preprocessing will compute the file transformations and energy minimization on the text files.
Voxelization allows to create the 3D images for HTMD, Rosetta and electronegativity features and combine them.
Postprocessing will transform the 3D images into a TFRecords format to be used as input for the neural networks.
Training, evaluation and prediction have the usual meanings.

Substeps in `preprocess` are cached. If some steps fail for some reason (usually faulty installations), the correct procedure after fixing the original problem is to clean the cached dataset. To do this, run `bash clear_dataset.sh <dataset>`, where `<dataset>` is the path to the dataset (i.e. `test_dataset`).

## Folder structure

To ease the setup, there are some requirements to the structure of the inputs.
The coarse unit of work is the dataset. A dataset is a folder with pdb folders and a file called labels.
The next unit of work is the pdb folder. A pdb folder stores a {code}_protein.pdb file and a {code}_ligand.mol2.
The labels file stores a line per pdb folder with the binding affinity assigned to it, separated by a space


A valid folder structure:
```
test_dataset\
             10gs\
                  10gs_protein.pdb
                  10gs_ligand.mol2
             labels
```

A valid `labels` file:
```
10gs 12
```

## Neural networks

There are three CNNs implemented in the module, but any other implementation can be used. The only requirement is following TensorFlow's Estimator API.
It is easy to replicate the same structure as the ones given here.

After training a neural network, the module will save the trained network in the dataset folder, with the essential parameters also written in the folder name. Additionally, a line with the minimal validation error and the epoch when it was achieved will be saved in a results file in the dataset folder. The random seed used during training will also be stored in this line. This seed will be necessary to load the network afterwards. 

## Selecting feature subsets

To select feature subsets, we can use the channel selectors. These are implemented by matching them as a substring of the feature names. Multiple channel selectors can be combined with underscored.

The feature names are: 

* `htmd_hydrophobic`
* `htmd_aromatic`
* `htmd_hbond_acceptor`
* `htmd_hbond_donor`
* `htmd_positive_ionizable`
* `htmd_negative_ionizable`
* `htmd_metal`
* `htmd_occupancies`
* `elec_p`
* `elec_l`
* `rosetta_atr_p`
* `rosetta_rep_p`
* `rosetta_sol_p_pos`
* `rosetta_elec_p_pos`
* `rosetta_sol_p_neg`
* `rosetta_elec_p_neg`
* `rosetta_atr_l`
* `rosetta_atr_p`
* `rosetta_sol_l_pos`
* `rosetta_elec_l_pos`
* `rosetta_sol_l_neg`
* `rosetta_elec_l_neg`

All `htmd` feature names represent both the protein and ligand features, so they are effectively two channels.

For example, using `htmd_rosetta` will include all the HTMD features, and all the Rosetta features.

The combination used in the paper release is `aromatic_acceptor_ion_rosetta`, adding to 20 feature maps.


## Setting the randomness

The neural network actions use a seed parameter. For training, this seed is optional and can be randomly chosen by the module.

The seed is used to identify different trainings of the same model/data. When evaluating and predicting, the seed must be specified. The seed can be found in the name of the trained model folder, located under the training dataset folder with name format `_<model_name>_<features_string>_<seed>`.

## Settings

There are a few parameters that may be modified to change the behavior of the module. The file `settings.py` stores these options.
There we can change the voxelization methods and the size of the voxel image. We can also change the parameters for TensorFlow's input pipeline.

## Running instructions

To run the actions mentioned above with the example dataset, we need to run the following commands:

### Data preparation

For the example dataset, substitute `<dataset>` with `test_dataset`

1. preprocess
```
python3 -m RosENet -- preprocess <dataset>
```
2. voxelize
```
python3 -m RosENet -- voxelize <dataset>
```
3. postprocess
```
python3 -m RosENet -- postprocess <dataset>
```

### Network training/evaluation

Substitute `<*_dataset>` with the paths to the respective datasets. 

Substitute `<model>` for the path of a network model code. Some examples are located under `RosENet/models` (i.e. `RosENet/models/resnet.py`)

Substitute `<feature_string>` for an underscore-separated string of channel selectors.

Substitute `<seed>` for a non-negative integer to be used as seed.

4. train
```
python3 -m RosENet -- train <train_dataset> <validation_dataset> <model> <features_string> [<seed>]
```
5. evaluate
```
python3 -m RosENet -- evaluate <train_dataset> <evaluation_dataset> <model> <features_string> <seed>
```
6. predict
```
python3 -m RosENet -- predict <train_dataset> <prediction_dataset> <model> <features_string> <seed>
```

### Preprocessed datasets

The datasets for training and validation of RosENet have been published and are accesible in https://doi.org/10.5281/zenodo.4625486

