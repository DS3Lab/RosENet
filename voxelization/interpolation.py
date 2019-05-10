def voxel_interpolation(int_type, points, values, targets):
    """Method to apply an interpolation method to a set of atom coordinates with
    assigned values, and distribute them to a set of target points.

    Parameters
    ----------
    int_type : str or callable
        Interpolation name or function handle following scipy.interpolate.Rbf.
    points : numpy.ndarray
        Atom coordinates.
    values : numpy.ndarray
        Atom values to spacially distribute.
    targets : numpy.ndarray
        3D voxel positions to compute the distributed values at.
    """
    mask = np.linalg.norm(points, axis=-1) <= 12.5*np.sqrt(3)
    points = points[mask]
    values = values[mask, :]
    points_x, points_y, points_z = [c.flatten()
                                    for c in np.split(points, 3, axis=1)]
    targets_x, targets_y, targets_z = [
        c.flatten() for c in np.split(targets, 3, axis=1)]
    res = np.stack([Rbf(points_x, points_y, points_z,
                        values[..., i], function=int_type)(targets_x, targets_y, targets_z)
                    for i in range(values.shape[-1])], axis=-1)
    return res
