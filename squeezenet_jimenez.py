#os.environ["CUDA_VISIBLE_DEVICES"]="-1"
import tensorflow as tf
import pickle
import numpy as np

with open(r'C:\Users\hhassan\Documents\Master Thesis\Resources\PDBBind\sandbox\1b51\images_original\1b51_0_0001.pkl','rb') as file:
    u = pickle._Unpickler(file)
    u.encoding = 'latin1'
    data = u.load()

learning_rate = 0.001
num_steps = 2000
batch_size = 128

def conv_net(data, reuse):
    with tf.variable_scope('SqueezeNet', reuse=reuse):
        channels = data.keys() - 1
        x = np.stack([channel for key, channel in data.items() if key is not 'origin'])
        x = np.rollaxis(x, 0, 4)
        net = tf.reshape(x, shape=[-1, 65, 65, 65, channels])
        net = tf.cast(net, dtype=tf.float32)

        net = tf.layers.max_pooling3d(net, 3, 3, padding='same', name='downsample_1')
        net = tf.layers.conv3d(net, 96, [11, 11, 11], name='conv1', activation='relu')
        net = tf.layers.conv3d(net, 16, [1, 1, 1], name='fire2_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 64, [1, 1, 1], name='fire2_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 64, [2, 2, 2], padding='same', name='fire2_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_1')
        net = tf.layers.conv3d(net, 16, [1, 1, 1], name='fire3_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 64, [1, 1, 1], name='fire3_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 64, [2, 2, 2], padding='same', name='fire3_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_2')
        net = tf.layers.conv3d(net, 32, [1, 1, 1], name='fire4_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 128, [1, 1, 1], name='fire4_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 128, [2, 2, 2], padding='same', name='fire4_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_3')
        net = tf.layers.max_pooling3d(tf.cast(net, tf.float32),[3,3,3], strides=2, name='maxpool4')
        net = tf.layers.conv3d(net, 32, [1, 1, 1], name='fire5_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 128, [1, 1, 1], name='fire5_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 128, [2, 2, 2], padding='same', name='fire5_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_4')
        net = tf.layers.conv3d(net, 48, [1, 1, 1], name='fire6_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 192, [1, 1, 1], name='fire6_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 192, [2, 2, 2], padding='same', name='fire6_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_5')
        net = tf.layers.conv3d(net, 48, [1, 1, 1], name='fire7_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 192, [1, 1, 1], name='fire7_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 192, [2, 2, 2], padding='same', name='fire7_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_6')
        net = tf.layers.conv3d(net, 64, [1, 1, 1], name='fire8_squeeze', activation='relu')
        net1 = tf.layers.conv3d(net, 256, [1, 1, 1], name='fire8_expand1', activation='relu')
        net2 = tf.layers.conv3d(net, 256, [2, 2, 2], padding='same', name='fire8_expand2', activation='relu')
        net = tf.concat(axis=-1, values=[net1, net2], name='merge_7')
        net = tf.layers.average_pooling3d(net, [2,2,2], 3, padding='same', name='avg8')
        net = tf.layers.flatten(net, name='flatten')
        net = tf.layers.dense(net, 1)
    return net


def model_fn(features, labels, mode):
    labels = tf.cast(tf.reshape(labels, [-1,1]), dtype=tf.float32)
    val_train = conv_net(features, reuse=False)
    val_test = conv_net(features, reuse=True)

    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode, predictions=val_test)

    loss_op = tf.losses.mean_squared_error(labels=labels, predictions=val_train)
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(loss_op,
                                  global_step=tf.train.get_global_step())

    metric = tf.metrics.root_mean_squared_error(labels=labels, predictions=val_train)

    estim_specs = tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=val_test,
        loss=loss_op,
        train_op=train_op,
        eval_metric_ops={'rmse': metric})

    return estim_specs

model = tf.estimator.Estimator(model_fn)

del data['origin']
input = np.stack(list(data.values()))
input = np.rollaxis(input,0,4)

input_fn = tf.estimator.inputs.numpy_input_fn(
    x=input,
    y=np.array([1.0]),
    batch_size=1,
    num_epochs=None,
    shuffle=False)
model.train(input_fn, steps=num_steps)

input_fn = tf.estimator.inputs.numpy_input_fn(
    x=input,
    y=np.array([1.0]),
    batch_size=1,
    shuffle=False)

e = model.evaluate(input_fn)

print("RMSE:", e['rmse'])