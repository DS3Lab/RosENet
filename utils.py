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


def normalize_max(x):
    return x / np.max(x)

def gaussian_filter(position_matrix, sigma, max_one=False):
  radius_matrix = np.linalg.norm(position_matrix, axis=3)
  gaussian_filter = (1/(np.sqrt(2*np.pi)*sigma)) * np.exp(-(1/(2*sigma**2)) * radius_matrix)
  return gaussian_filter

def angular_filter(position_matrix, radius_matrix, sigma):
  right_product = (radius_matrix ** (1 / sigma - 3)) * (np.exp(-2 * radius_matrix / sigma)) ** 2
  angular_filter = np.prod(position_matrix, axis=3) * right_product
  return angular_filter

def rotate_45_matrix(position_matrix, vector):
  cos_theta = np.dot([1, 1, 1], vector) / (3 * np.linalg.norm(vector))
  sin_theta = np.sqrt(1 - cos_theta ** 2)
  rot_axis = np.cross([1, 1, 1], vector) / (3 * np.linalg.norm(vector))
  rot_matrix = cos_theta * np.identity(3) + sin_theta * np.cross(np.identity(3), rot_axis) + (1 - cos_theta) * np.tensordot(rot_axis, rot_axis, axes=0)
  return np.dot(position_matrix, rot_matrix.T)

def exp_vdw_filter(distance, sigma, cutoff = 5):
  filtered = (1 - np.exp(-((sigma / distance) ** 12)))
  filtered[distance >= cutoff] = 0
  return filtered

def clip_max_zero(image):
  image = image.clip(max=0, min=np.percentile(image, 5))

def clip_min_zero(image):
  image = image.clip(min=0, max=np.percentile(image, 95))

def clip(image):
  image = image.clip(max=np.percentile(image,95), min=np.percentile(image,5))

