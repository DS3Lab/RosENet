import RosENet.storage.storage as storage
import RosENet.network.input as input
import RosENet.settings as settings
import tensorflow as tf
import importlib.util
import numpy as np
from RosENet.objects.file import File

class _ModelAction:
    """Model action base class. Represents an action (training, evaluation or prediction)
    of a dataset using a model(neural network)"""
    def __init__(self, model_object, dataset_object, channels, action, seed):
        self.dataset_object = dataset_object
        if not self.results.path.exists():
            self.results.write("")
        self.model_object = model_object
        self.channels = channels
        input_fn = input.load_fn(dataset_object, channels, settings.rotate, action)
        self.iterator = input_fn().make_initializable_iterator()
        model_fn = model_object.load_fn()
        self.id, self.X, self.y = self.iterator.get_next()
        self.shape = tf.shape(self.y)[0]
        model = model_fn(self.X, self.y, action, settings.rotate)
        self.op = model.train_op
        self.loss = model.loss
        self.predictions = model.predictions
        checkpoint_folder = self.dataset_object.model(self.model_object, self.channels, seed)
        storage.make_directory(checkpoint_folder)
        self.save_path = checkpoint_folder / "model.ckpt"
        self.saver = tf.train.Saver()
    
    def do(self, sess = None):
        if sess is None:
            sess = tf.get_default_session()
        try:
            sess.run(self.iterator.initializer)
            self.start_epoch()
            while True:
                self.do_batch(sess)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            pass
        return self.end_epoch()

    def save(self, sess = None):
        if sess is None:
            sess = tf.get_default_session()
        self.saver.save(sess, str(self.save_path.absolute()))
    
    @property
    def dataset_name(self):
        return self.dataset_object.name

    @property
    def model_name(self):
        return self.model_object.name

    @property
    def results(self):
        return File.create(f"{self.dataset_name}.txt",self.dataset_object.path)

    def load(self, sess = None):
        if sess is None:
            sess = tf.get_default_session()
        self.saver.restore(sess, str(self.save_path))

class _ModelTrain(_ModelAction):
    def __init__(self, model_path, dataset_path, channels,seed):
        super(_ModelTrain, self).__init__(model_path,
                                          dataset_path,
                                          channels,
                                          tf.estimator.ModeKeys.TRAIN,
                                          seed)
    def start_epoch(self):
        self.size = 0
        self.loss_value = 0
    
    def do_batch(self, sess):
        _, loss, batch_shape = sess.run([self.op, self.loss, self.shape])
        self.size += batch_shape
        self.loss_value = batch_shape*loss

    def end_epoch(self):
        return np.sqrt(self.loss_value/self.size)

class _ModelEvaluate(_ModelAction):
    def __init__(self, model_path, dataset_path, channels, seed):
        super(_ModelEvaluate, self).__init__(model_path,
                                          dataset_path,
                                          channels,
                                          tf.estimator.ModeKeys.EVAL,
                                          seed)
    def start_epoch(self):
        self.size = 0
        self.loss_value = 0
    
    def do_batch(self, sess):
        loss, batch_shape = sess.run([self.loss, self.shape])
        self.size += batch_shape
        self.loss_value = batch_shape*loss

    def end_epoch(self):
        return np.sqrt(self.loss_value/self.size)

class _ModelPredict(_ModelAction):
    def __init__(self, model_path, dataset_path, channels, seed):
        super(_ModelPredict, self).__init__(model_path,
                dataset_path, 
                channels,
                tf.estimator.ModeKeys.EVAL,
                seed)
    def start_epoch(self):
        self.prediction_dict = {}
    
    def do_batch(self, sess):
        names, predictions = sess.run([self.id, self.predictions])
        for name, prediction in zip(names, predictions):
            self.prediction_dict[str(name)] = prediction

    def end_epoch(self):
      return self.prediction_dict

class _Model:
    """Inner Model class, represents a CNN."""
    _instance_dict = {}
    def __init__(self, path):
        self.path = path

    def train_object(self, dataset_object, channels, seed):
        return _ModelTrain(self, dataset_object, channels, seed)
    
    def evaluate_object(self, dataset_object, channels, seed):
        return _ModelEvaluate(self, dataset_object, channels, seed)
    
    def predict_object(self, dataset_object, channels, seed):
        return _ModelPredict(self, dataset_object, channels, seed)

    @property
    def name(self):
        return self.path.stem

    def load_fn(self):
        spec = importlib.util.spec_from_file_location("aux_module", str(self.path.absolute()))
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        return foo.model_fn
        #return __import__(str(self.path.absolute()), fromlist=["model_fn"])

def ModelObject(path):
    if str(path.absolute()) not in _Model._instance_dict:
        _Model._instance_dict[str(path.absolute())] = _Model(path)
    return _Model._instance_dict[str(path.absolute())]

