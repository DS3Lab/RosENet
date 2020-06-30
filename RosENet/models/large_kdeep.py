import tensorflow as tf

LEARNING_RATE = 0.0001

def fire_module(net, squeeze, expand, training):
    net = tf.layers.conv3d(net, squeeze, [1,1,1], activation=tf.nn.relu)
    net1 = tf.layers.conv3d(net, expand, [1,1,1], activation=tf.nn.relu)
    net2 = tf.layers.conv3d(net, expand, [3,3,3], padding='same', activation=tf.nn.relu)
    return tf.concat(axis=-1, values=[net1,net2])

def conv_net(X, reuse, training):
    with tf.variable_scope('SqueezeNet', reuse=reuse):
        net = tf.layers.conv3d(X, 96, 7, 2, padding='same', activation=tf.nn.relu)
        net = fire_module(net, 16, 64,training=training)
        net = fire_module(net, 16, 64,training=training)
        net = fire_module(net, 32, 128,training=training)
        net = tf.layers.max_pooling3d(net, 3, 2)
        net = fire_module(net, 32, 128,training=training)
        net = fire_module(net, 48, 192,training=training)
        net = fire_module(net, 48, 192,training=training)
        net = fire_module(net, 64, 256,training=training)
        net = tf.layers.average_pooling3d(net, 3, 2)
        net = tf.layers.flatten(net)
        net = tf.layers.dense(net, 1)
        return net

def model_fn(features, labels, mode, rotate):
    training = mode == tf.estimator.ModeKeys.TRAIN
    predictions = conv_net(features, reuse=tf.AUTO_REUSE, training=training)

    loss = None
    train_op = None
    if training:
        loss = tf.losses.mean_squared_error(labels=labels, predictions=predictions)
        optimizer = tf.train.AdamOptimizer(learning_rate=LEARNING_RATE)
        train_op = optimizer.minimize(loss,global_step=tf.train.get_global_step())
    else:
        #When evaluating or predicting, average over the 24 90º rotations if rotations are enabled.
        if rotate:
            predictions = tf.reduce_mean(tf.reshape(predictions,(-1,24,1)),axis=1)
            loss = tf.losses.mean_squared_error(labels,predictions)
        else:
            loss = tf.losses.mean_squared_error(labels=labels, predictions=predictions)

    return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions=predictions,
        loss=loss,
        train_op=train_op,
        eval_metric_ops={
          'R': tf.metrics.mean(r),
          'ro_2': tf.metrics.mean(r_squared)
        })
