import tensorflow as tf

LEARNING_RATE = 0.0001


def start_block(net, channels, training):
  input_net = tf.layers.conv3d(net, 4*channels, 1, 2, padding='same')
  net = conv3bn(net, channels, 1, training,stride=2)
  net = conv3bn(net, channels, 3, training)
  net = conv3bn(net, 4*channels, 1, training)
  output_net = net + input_net
  return output_net

def inner_block(net, channels, training):
  input_net = tf.layers.conv3d(net, 4*channels, 1, padding='same')
  net = conv3bn(net, channels, 1, training)
  net = conv3bn(net, channels, 3, training)
  net = conv3bn(net, 4*channels, 1, training)
  output_net = net + input_net
  return output_net


def conv3bn(net, channels, filt, training, stride=1):
  #net = tf.layers.batch_normalization(net, training=training)
  net = tf.nn.relu(net)
  net = tf.layers.conv3d(net, channels, filt, stride, padding='same')
  return net

def conv_net(X, reuse, training):
  with tf.variable_scope('ResNet', reuse=reuse):
    layers = [3,4,23,3]
    k = 64
    net = tf.layers.conv3d(X, k, 7, 2, padding='same')
    #net = tf.layers.batch_normalization(net, training=training)
    net = tf.nn.relu(net)
    net = tf.layers.max_pooling3d(net, 3, 2)
    for i in range(0,layers[0]):
      net = inner_block(net, k, training)
    for i, l in enumerate(layers[1:],1):
      net = start_block(net, k*(2**i), training)
      for j in range(0,l-1):
        net = inner_block(net, k*(2**i), training)
    net = tf.reduce_mean(net, axis=(1,2,3))
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
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      with tf.control_dependencies(update_ops):
        train_op = optimizer.minimize(loss,global_step=tf.train.get_global_step())
    else:
      if rotate:
        predictions = tf.reduce_mean(tf.reshape(predictions,(-1,24,1)), axis=1)
        loss = tf.losses.mean_squared_error(labels, predictions)
      else:
        loss = tf.losses.mean_squared_error(labels=labels, predictions=predictions)

    rmse = tf.metrics.root_mean_squared_error(labels=labels, predictions=predictions)
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
        'rmse': rmse,
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
