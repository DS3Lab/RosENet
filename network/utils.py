import tensorflow as tf
import numpy as np

def save_results(model_train_object, channels="", *args):
    """Save information about a trained model in csv format.

    model_train_object : _ModelTrain
        ModelTrain object representing the instantiation of the training
    channels : string
        Channel selectors used for the training
    args : list of various
        Data to be written in the file
    """
    result_line = ",".join([model_train_object.dataset_name, model_train_object.model_name] +  [str(a) for a in args]) + "\n"
    model_train_object.results.write(model_train_object.results.read()+result_line)

def random_rotation_matrix():
    """Create a random 3D matrix in TensorFlow"""
    A = tf.random_normal((3,3))
    Q, _ = tf.linalg.qr(A)
    Q = tf.convert_to_tensor([[tf.sign(tf.linalg.det(Q)),0,0],
                                [0,1,0],
                                [0,0,1]],dtype=tf.float32) @ Q
    return Q

def line3D(o,t,step):
    l0 = tf.linspace(o[0],t[0],step)
    l1 = tf.linspace(o[1],t[1],step)
    l2 = tf.linspace(o[2],t[2],step)
    return tf.stack((l0,l1,l2),axis=1)

def outer_sum_diag(a,b):
    return tf.expand_dims(a,axis=-2) + tf.expand_dims(b,axis=0)

def random_rot(X, input_shape, output_shape):
    output_step = output_shape[0]
    batch_size = tf.shape(X)[0]
    m = (np.array(input_shape[:-1]) - 1)/2
    o = -(np.array(output_shape)-1)/2
    corners = np.array([[0,0,0],
                        [output_step-1,0,0],
                        [0,output_step-1,0],
                        [0,0,output_step-1]]) + o
    corners = tf.convert_to_tensor(corners, dtype=tf.float32)
    rotation_matrix = random_rotation_matrix()
    rotated_corners = corners @ rotation_matrix
    rotated_corners = rotated_corners + tf.convert_to_tensor(m, dtype=tf.float32)
    o = rotated_corners[0]
    a = rotated_corners[1]
    b = rotated_corners[2]
    c = rotated_corners[3]
    line_oa = line3D(o,a,output_step)
    vector_ob = line3D(o,b,output_step) - o
    vector_oc = line3D(o,c,output_step) - o
    plane_oab = outer_sum_diag(vector_ob,line_oa)
    rotated_query_points = outer_sum_diag(plane_oab, vector_oc)
    rotated_query_points = tf.cast(tf.round(rotated_query_points),tf.int64)
    rotated_query_points = tf.expand_dims(rotated_query_points, axis=0)
    rotated_query_points = tf.reshape(rotated_query_points, [1,-1,3])
    rotated_query_points = tf.tile(rotated_query_points, [batch_size, 1, 1])
    batch_column = tf.cast(tf.reshape(tf.tile(tf.reshape(tf.range(batch_size),(-1,1,1)), [1, 1, np.prod(output_shape)]),(-1,np.prod(output_shape),1)),tf.int64)
    rotated_query_points = tf.concat((batch_column,rotated_query_points),axis=2)
    X_output = tf.gather_nd(X, rotated_query_points)
    X_output = tf.reshape(X_output, [batch_size] + output_shape + [input_shape[-1]])
    return X_output

def basic_rot(X, axis, ccw=True):
    rot_axes = [x for x in [0,1,2] if x != axis]
    axis_1, axis_2 = rot_axes
    perm = [x if x not in rot_axes else axis_1 if x == axis_2 else axis_2  for x in [0,1,2,3]]
    rev_axis = axis_1 if ccw else axis_2
    return tf.reverse(tf.transpose(X,perm),[rev_axis])

def basic_rot_5D(X, axis, ccw=True):
    axis = axis + 1
    rot_axes = [x for x in [1,2,3] if x != axis]
    axis_1, axis_2 = rot_axes
    perm = [x if x not in rot_axes else axis_1 if x == axis_2 else axis_2  for x in [0,1,2,3,4]]
    rev_axis = axis_1 if ccw else axis_2
    return tf.reverse(tf.transpose(X,perm),[rev_axis])


def rots_90(X):
    x_90 = basic_rot(X, 0)
    x_180 = tf.reverse(X, [1,2])
    x_270 = basic_rot(X, 0, ccw=False)
    maps = [X, x_90, x_180, x_270]
    extended_maps = list(maps)
    for m in maps:
      z_90 = basic_rot(m, 2)
      z_180 = tf.reverse(m, [0,1])
      z_270 = basic_rot(m, 2, ccw=False)
      y_90 = basic_rot(m, 1)
      y_270 = basic_rot(m, 1, ccw=False)
      extended_maps += [z_90, z_180, z_270, y_90, y_270]
    return tf.stack(extended_maps)

def rots_90_5D(X):
    x_90 = basic_rot_5D(X, 0)
    x_180 = tf.reverse(X, [1,2])
    x_270 = basic_rot_5D(X, 0, ccw=False)
    maps = [X, x_90, x_180, x_270]
    extended_maps = list(maps)
    for m in maps:
      z_90 = basic_rot_5D(m, 2)
      z_180 = tf.reverse(m, [0,1])
      z_270 = basic_rot_5D(m, 2, ccw=False)
      y_90 = basic_rot_5D(m, 1)
      y_270 = basic_rot_5D(m, 1, ccw=False)
      extended_maps += [z_90, z_180, z_270, y_90, y_270]
    return tf.stack(extended_maps)

def random_rot_90(X,shape):
    def my_func(X):
        # x will be a numpy array with the contents of the placeholder below
        anti = np.random.randint(0,2,1)
        if anti == 0:
            shift = np.random.randint(0,3,1)
            x, y, z = ((np.array([0,1,2]) + shift) % 3) + 1
            flip = np.random.choice([None,(1,2),(1,3),(2,3)],1)[0]
            X = X.transpose((0,x,y,z,4))
            if flip is not None:
                a,b = flip
                X = np.flip(X,(a,b))
        else:
            shift = np.random.randint(0,3,1)
            x, y, z = ((np.array([1,0,2]) + shift) % 3) + 1
            flip = np.random.choice([1,2,3,None],1)[0]
            X = X.transpose((0,x,y,z,4))
            if flip is not None:
                X = np.flip(X,flip)
            else:
                X = np.flip(X,(1,2,3))
        return X
    return tf.reshape(tf.py_func(my_func, [X], tf.float32),shape)

def all_rot_90(X,shape):
    def my_func(X):
        # x will be a numpy array with the contents of the placeholder below
        results = []
        for point in X:
            for shift in range(3):
                x, y, z = ((np.array([0,1,2]) + shift) % 3)
                for flip in [None,(0,1),(0,2),(1,2)]:
                    aux = point.transpose((x,y,z,3))
                    if flip is not None:
                        a,b = flip
                        results.append(np.flip(aux,(a,b)))
                    else:
                        results.append(aux)
            for shift in range(3):
                x, y, z = ((np.array([1,0,2]) + shift) % 3)
                for flip in [0,1,2,None]:
                    aux = point.transpose((x,y,z,3))
                    if flip is not None:
                        results.append(np.flip(aux,flip))
                    else:
                        results.append(np.flip(aux,(0,1,2)))
        ret = np.stack(results,axis=0)
        return ret
    return tf.reshape(tf.py_func(my_func, [X], tf.float32),shape)
