import numpy as np
import scipy.ndimage


def isfloat(value):
    """Check if value is a float
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def apply_gaussian_filter(center, window, intensity, sigma, out):
    kernel = np.zeros(len(center) * (window,))
    kernel[len(center) * (window // 2,)] = 1
    kernel = scipy.ndimage.gaussian_filter(kernel, sigma) * intensity
    min_xyz = center - np.array(kernel.shape) // 2
    min_x, min_y, min_z = min_xyz.clip(min=0)
    max_xyz = center + (np.array(kernel.shape) - np.array(kernel.shape) // 2)
    max_x, max_y, max_z = np.minimum(max_xyz, out.shape)
    k_min_x, k_min_y, k_min_z = -min_xyz.clip(max=0)
    k_max_x, k_max_y, k_max_z = np.array(kernel.shape) - (np.array(max_xyz) - np.minimum(max_xyz, out.shape))
    kernel = kernel[k_min_x:k_max_x, k_min_y:k_max_y, k_min_z:k_max_z]
    out[min_x:max_x, min_y:max_y, min_z:max_z] = \
        np.maximum(kernel, out[min_x:max_x, min_y:max_y, min_z:max_z])
