import Repo.storage.storage as storage
import tensorflow as tf
import Repo.network.models as models

class _ModelAction:
	def __init__(self, model_object, dataset_object, channels, action):
		self.dataset_object = dataset_object
		self.model_object = model_object
		self.channels = channels
  		input_fn = input.load_fn(dataset_object, channels, settings.rotate, action)
    	self.iterator = input_fn().make_initializable_iterator()
		model_fn = model_object.load_fn()
		self.id, self.X, self.y = iterator.get_next()
		self.shape = tf.shape(self.y)[0]
		model = model_fn(self.X, self.y, action, settings.rotate)
    	self.op = model.train_op
    	self.loss = model.loss
	
	def do(self, sess = None):
		if sess is None:
			sess = tf.get_default_session()
		try:
			sess.run(self.iterator.initializer)
			self.start_epoch()
			while True:
				self.do_batch()
		except (KeyboardInterrupt, SystemExit):
			raise
		except Exception as e:
			pass
		return self.end_epoch()

	def presave(self, seed):
		self.saver = tf.train.Saver()
		checkpoint_folder = self.dataset_object.model(self.model_object, self.channels, seed)
		storage.make_directory(checkpoint_folder)
		self.save_path = checkpoint_folder / "model.ckpt"

	def save(self, sess = None):
		if sess is None:
			sess = tf.get_default_session()
		saver.save(sess, str(self.save_path.absolute()))
	
	@property
	def dataset_name(self):
		return self.dataset_object.name

	@property
	def model_name(self):
		return self.model_object.name


class _ModelTrain(_ModelAction):
	def __init__(self, model_path, dataset_path, channels):
		super(_ModelTrain, self).__init__(model_path,
										  dataset_path,
										  channels,
										  tf.estimator.ModeKeys.TRAIN)
	def start_epoch(self):
		self.size = 0
		self.loss_value = 0
	
	def do_batch(self):
		_, loss, batch_shape = sess.run([self.op, self.loss, self.shape])
		self.size += batch_shape
		self.loss_value = batch_shape*loss

	def end_epoch(self):
		return np.sqrt(self.loss_value/self.size)

class _ModelEvaluate(_ModelAction):
	def __init__(self, model_path, dataset_path, channels):
		super(_ModelTrain, self).__init__(model_path,
										  dataset_path,
										  channels,
										  tf.estimator.ModeKeys.EVAL)
	def start_epoch(self):
		self.size = 0
		self.loss_value = 0
	
	def do_batch(self):
		loss, batch_shape = sess.run([self.loss, self.shape])
		self.size += batch_shape
		self.loss_value = batch_shape*loss

	def end_epoch(self):
		return np.sqrt(self.loss_value/self.size)

class _ModelPredict(_ModelAction):
	def __init__(self, model_path, dataset_path, channels):
		super(_ModelTrain, self).__init__(model_path,
										  dataset_path,
										  channels,
										  tf.estimator.ModeKeys.EVAL)
	def start_epoch(self):
		self.predictions = {}
	
	def do_batch(self):
		names, predictions = sess.run([self.id, self.y])
		for name, prediction in zip(names, predictions):
			self.predictions[name] = prediction

	def end_epoch(self):
		return self.predictions

class _Model:
    _instance_dict = {}
    def __init__(self, path):
        self.path = path

	def train_object(self, dataset_object, channels):
		return _ModelTrain(self.path, dataset_object.path, channels)
	
	def evaluate_object(self, dataset_object, channels):
		return _ModelEvaluate(self.path, dataset_object.path, channels)
	
	def predict_object(self, dataset_object, channels):
		return _ModelEvaluate(self.path, dataset_object.path, channels)

	@property
	def name(self):
		return self.path.stem

    def load_fn(self):
		return getattr(models,self.path.stem)

def ModelObject(path):
    if str(path.absolute()) not in _Model._instance_dict:
        _Model._instance_dict[str(path.absolute())] = _Model(path)
    return _Model._instance_dict[str(path.absolute())]

