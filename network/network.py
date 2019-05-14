import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import random

def train(dataset_train, dataset_evaluate, model_object, seed=None, channels=""):
    if seed is None:
        seed = random.randint(0,2147483647)
    tf.random.set_random_seed(seed)
    model_train_object = model_object.train_object(dataset_train)
    model_valid_object = model_object.evaluate_object(dataset_evaluate)
    model_train_object.presave(seed)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        min_validation = float('inf')
        epoch_min_validation = -1
        for num_epochs in range(settings.max_epochs):
            tr_loss = model_train_object.do(sess)
            val_loss = model_valid_object.do(sess)
            if min_validation > va_loss:
                min_validation = va_loss
                epoch_min_validation = num_epochs
                model_train_object.save(sess)
        save_results(dataset_train, model_object, channels, min_validation, epoch_min_validation, seed)

def evaluate(dataset_train, dataset_evaluate, model_object, seed, channels=""):
    model_train_object = model_object.train_object(dataset_train)
    model_valid_object = model_object.evaluate_object(dataset_evaluate)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        model_train_object.load(seed)
        val_loss = model_valid_object.do(sess)
    return val_loss

def predict(dataset_train, dataset_predict, model_object, seed, channels=""):
    model_train_object = model_object.train_object(dataset_train)
    model_pred_object = model_object.predict_object(dataset_predict)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        model_train_object.load(seed)
        results = model_pred_object.do(sess)
    return results
