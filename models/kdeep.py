import tensorflow as tf

LEARNING_RATE = 0.0001

def fire_module(net, squeeze, expand, training):
  net = tf.layers.conv3d(net, squeeze, [1,1,1], activation=tf.nn.relu)
  net1 = tf.layers.conv3d(net, expand, [1,1,1], activation=tf.nn.relu)
  net2 = tf.layers.conv3d(net, expand, [3,3,3], padding='same', activation=tf.nn.relu)
  return tf.concat(axis=-1, values=[net1,net2])

def conv_net(X, reuse, training):
  with tf.variable_scope('SqueezeNet', reuse=reuse):
    print(X)
    net = tf.layers.conv3d(X, 96, 1, 2, padding='same', activation=tf.nn.relu)
    print(net)
    net = fire_module(net, 16, 64,training=training)
    net = fire_module(net, 16, 64,training=training)
    net = fire_module(net, 32, 128,training=training)
    net = tf.layers.max_pooling3d(net, 3, 2)
    print(net)
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
      if rotate:
        predictions = tf.reduce_mean(tf.reshape(predictions,(-1,24,1)),axis=1)
        loss = tf.losses.mean_squared_error(labels,predictions)
        #loss = tf.squared_difference(labels[0], tf.reduce_mean(predictions))
      else:
        loss = tf.losses.mean_squared_error(labels=labels, predictions=predictions)
    r_squared = r_square(labels, predictions)
    r = R(labels, predictions) 

    tf.summary.scalar("rmse", tf.sqrt(loss))
    tf.summary.scalar("ro_2", r_squared)
    tf.summary.scalar('R', r)
    tf.summary.merge_all()

    return tf.estimator.EstimatorSpec(
      mode=mode,
      predictions=predictions,
      loss=loss,
      train_op=train_op,
      eval_metric_ops={
        'R': tf.metrics.mean(r),
        'ro_2': tf.metrics.mean(r_squared)
      })

def R(y_true, y_pred):
  y_mean = tf.reduce_mean(y_true)
  centered_y = y_true - y_mean
  y_pred_mean = tf.reduce_mean(y_pred)
  centered_y_pred = y_pred - y_pred_mean
  numerator = tf.reduce_sum(tf.multiply(centered_y, centered_y_pred))
  denominator_1 = tf.sqrt(tf.reduce_sum(tf.square(centered_y)))
  denominator_2 = tf.sqrt(tf.reduce_sum(tf.square(centered_y_pred)))
  return numerator / (denominator_1 * denominator_2)


def r_square(y_true, y_pred,epsilon=1e-10):
    eps = tf.constant(epsilon)
    true_mean = tf.reduce_mean(y_true)
    sum_squared_diff_pred = tf.reduce_sum(tf.squared_difference(y_true,y_pred))
    sum_squared_diff_mean = tf.reduce_sum(tf.squared_difference(y_true,true_mean))
    return tf.subtract(tf.constant(1.0),tf.divide(sum_squared_diff_pred,(tf.add(sum_squared_diff_mean,eps))))
