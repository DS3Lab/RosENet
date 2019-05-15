import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import random
import DrugDiscovery.settings as settings
from DrugDiscovery.network.utils import save_results
import time

def train(dataset_train, dataset_evaluate, model_object, seed=None, channels=""):
    if seed is None:
        seed = random.randint(0,2147483647)
    tf.set_random_seed(seed)
    model_train_object = model_object.train_object(dataset_train,channels,seed)
    model_valid_object = model_object.evaluate_object(dataset_evaluate,channels,seed)
    model_train_object.presave(seed)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        min_validation = float('inf')
        epoch_min_validation = -1
        for num_epochs in range(settings.max_epochs):
            t1 = time.time()
            tr_loss = model_train_object.do(sess)
            t2 = time.time() - t1
            print(f"Train loss: {tr_loss} Elapsed: {t2}")
            t1 = time.time()
            va_loss = model_valid_object.do(sess)
            t2 = time.time() - t1
            print(f"Validation loss: {va_loss} Elapsed: {t2}")
            if min_validation > va_loss:
                min_validation = va_loss
                epoch_min_validation = num_epochs
                model_train_object.save(sess)
            print(f"Best validation: {min_validation} Epoch: {epoch_min_validation}")
        save_results(model_train_object, channels, min_validation, epoch_min_validation, seed)

def evaluate(dataset_train, dataset_evaluate, model_object, seed, channels=""):
    model_train_object = model_object.train_object(dataset_train, channels, seed)
    model_valid_object = model_object.evaluate_object(dataset_evaluate, channels, seed)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        model_train_object.load(sess)
        val_loss = model_valid_object.do(sess)
    print(val_loss)
    return val_loss

def predict(dataset_train, dataset_predict, model_object, seed, channels=""):
    model_train_object = model_object.train_object(dataset_train, channels, seed)
    model_pred_object = model_object.predict_object(dataset_predict, channels, seed)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        model_train_object.load(sess)
        results = model_pred_object.do(sess)
    print(results)
    return results
