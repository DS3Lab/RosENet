import DrugDiscovery.utils as utils

class Step(type):

    def __new__(cls, name, bases, dct, requirements=[]):
        x = super(Step, cls).__new__(cls,name, bases, dct)
        x.requirements = requirements
        x.successors = []
        x.name = name
        for requirement in requirements:
            requirement.successors.append(x)
        return x


    def clean(cls, pdb_object):
        if not cls.computed(pdb_object):
            return
        for successor in cls.successors:
            successor.clean(pdb_object)
        pdb_object.uncomplete(cls.name)
        for file in cls.files(pdb_object):
            file.delete()

    def run(cls, pdb_object, callbacks=[], force=False, surrogate=False):
        if cls.computed(pdb_object) and not force:
            if not surrogate:
                utils.message_callbacks(callbacks, (cls.name, pdb_object, "already_done"))
            return True
        elif not cls.ready(pdb_object):
            if not surrogate:
                utils.message_callbacks(callbacks, (cls.name, pdb_object, "not_ready"))
            return False
        utils.message_callbacks(callbacks, (cls.name, pdb_object, "start"))
        try:
            cls._run(pdb_object)
        except Exception as e:
            utils.message_callbacks(callbacks, (cls.name, pdb_object, "error", e))
            return False
        pdb_object.complete(cls.name)
        utils.message_callbacks(callbacks, (cls.name, pdb_object, "end"))
        return True

    def computed(cls, pdb_object):
        return cls.name in pdb_object.completed_steps


    def ready(cls, pdb_object):
        return all(map(lambda x: x.computed(pdb_object), cls.requirements))

    def run_until(cls, pdb_object, callbacks=[], surrogate=False):
        for requirement in cls.requirements:
            if not requirement.run_until(pdb_object, callbacks, surrogate=True):
                return False
        return cls.run(pdb_object,callbacks, force=False, surrogate=surrogate)
        

