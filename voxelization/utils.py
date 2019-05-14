import numpy as np

def grid_around(center, size, spacing=1.0):
    """Generate an array of 3D positions for a voxel cube of the given size and
    coarseness.

    center : numpy.ndarray
        3D coordinates of the cube's center.
    size : numpy.ndarray
        Number of voxels for each of the cube's dimensions.
    spacing : float
        Distance between voxel centers.
    """
    size_ang = ((size - 1) / 2.) * spacing
    ex_min = center - size_ang
    ex_max = center + size_ang

    x = np.linspace(ex_min[0], ex_max[0], size)
    y = np.linspace(ex_min[1], ex_max[1], size)
    z = np.linspace(ex_min[2], ex_max[2], size)
    return np.stack(np.meshgrid(x, y, z, indexing='ij'), axis=-1)


def clip1d(value, upp_limit):
    """Clip a single array by a limit and zero. If the limit is negative,
    use it as lower bound, otherwise use it as upper bound.

    value : numpy.ndarray
        Array to be clipped.
    upp_limit : float
        Threshold to use as bound.
    """
    low_limit = 0
    if upp_limit < 0:
        upp_limit, low_limit = low_limit, upp_limit
    return np.clip(value, low_limit, upp_limit) / (low_limit + upp_limit)


def clip(values, limits):
    """Clip a list of arrays by a list of limits

    values : list of numpy.ndarray
        List of arrays to be clipped.
    limits : list of float
        List of thresholds to use as bounds.
    """
    if values.shape[-1] == 1:
        return clip1d(values, limits[0])
    return np.stack((clip1d(values[...,i], limits[i]) for i in range(values.shape[-1])), axis=-1)


def get_keys(pdb):
    """Get the unique key names to the atoms of the structure.

    pdb : prody.AtomGroup
        Structure of atoms.
    """
    resnums = pdb.getResnums()
    chids = pdb.getChids()
    names = pdb.getNames()
    keys = np.char.add(np.char.mod(
        '%s-', np.char.replace(np.char.add(np.char.mod('%s ', resnums), chids), ' ', '-')), names)
    return keys


def save_grid(saving_path, image):
    """Save 3D image to HDF5 format.

    saving_path : str or os.PathLike
        Destination path to save the image.
    image : numpy.ndarray
        3D image to be saved.
    """
    with h5py.File(str(saving_path), "w", libver='latest') as f:
        f.create_dataset("grid", dtype='f4', data=image)

