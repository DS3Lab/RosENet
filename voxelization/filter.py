def exp_12(r, rvdw):
    """Exponential filter as given by Jimenez et al. (2018) 
    10.1021/acs.jcim.7b00650

    Parameters
    ----------
    r : numpy.ndarray
        Array of distances between each atom and all voxels of the 3D image.
    rvdw : numpy.ndarray
        Array of Van der Waals radii for each atom.

    """
    rvdw = rvdw.reshape((-1,))
    rr = rvdw[:, None]/r
    ret = np.where(r == 0, 1, 1 - np.exp(-(rr)**12))
    return ret


def gaussian(r, rvdw):
    """Gaussian-like filter, constants removed as everything will be normalized.

    Parameters
    ----------
    r : numpy.ndarray
        Array of distances between each atom and all voxels of the 3D image.
    rvdw : numpy.ndarray
        Array of Van der Waals radii for each atom.

    """
    rvdw = rvdw.reshape((-1,))
    rr = r/rvdw[:, None]
    ret = np.exp(-(rr)**2)
    return ret


def voxel_filter(filter_type, points, values, targets, radii):
    """Method to apply a filter to a set of atom coordinates with assigned 
    values, and distribute them to a set of target points. Atom radii are 
    taken into consideration to adjust strength of contributions.

    Parameters
    ----------
    filter_type : callable
        Function handle implementing the filter to be applied.
    points : numpy.ndarray
        Atom coordinates.
    values : numpy.ndarray
        Atom values to spacially distribute.
    targets : numpy.ndarray
        3D voxel positions to compute the distributed values at.
    radii : numpy.ndarray
        Van der Waals radii of the atoms.
    """
    mask = np.linalg.norm(points, axis=-1) <= 12.5*np.sqrt(3)
    points = points[mask]
    values = values[mask, :]
    radii = radii[mask]
    dists = cdist(points, targets)
    aux = np.where(dists < 5, filter_type(dists, radii), 0)
    del dists
    result = np.array([values[np.argmax(aux, axis=0), i] * np.max(aux, axis=0)
                       for i in range(values.shape[-1])])
    result = np.swapaxes(result, 0, 1)
    return result
