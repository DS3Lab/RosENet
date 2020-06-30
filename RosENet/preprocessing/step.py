import RosENet.utils as utils

class Step(type):
    """Metaclass for preprocessing steps. Implements functions to run the steps
    according to their dependencies, clean the outputed data and check for
    readiness of execution."""

    def __new__(cls, name, bases, dct, requirements=[]):
        x = super(Step, cls).__new__(cls,name, bases, dct)
        x.requirements = requirements
        x.successors = []
        x.name = name
        for requirement in requirements:
            requirement.successors.append(x)
        return x


    def clean(cls, pdb_object):
        """Delete files and folders created by the step and its successor steps.

        pdb_object : PDBObject
            PDB structure to be handled
        """
        if not cls.computed(pdb_object):
            return
        for successor in cls.successors:
            successor.clean(pdb_object)
        pdb_object.uncomplete(cls.name)
        for file in cls.files(pdb_object):
            file.delete()

    def run(cls, pdb_object, callbacks=[], force=False, surrogate=False):
        """Run the preprocessing step for the given PDB structure.

        pdb_object : PDBObject
            PDB structure to be handled
        callbacks : list of callable
            List of callbacks for logging
        force : bool
            Force execution even if the step was already computed? Default False
        surrogate : bool
            Run step as consequence of another step. Default False
        """
        if cls.computed(pdb_object) and not force:
            if not surrogate:
                utils.message_callbacks(callbacks, (cls.name, pdb_object.id, "already_done"))
            return True
        elif not cls.ready(pdb_object):
            if not surrogate:
                utils.message_callbacks(callbacks, (cls.name, pdb_object.id, "not_ready"))
            return False
        utils.message_callbacks(callbacks, (cls.name, pdb_object.id, "start"))
        try:
            cls._run(pdb_object)
        except Exception as e:
            utils.message_callbacks(callbacks, (cls.name, pdb_object.id, "error", e))
            return False
        pdb_object.complete(cls.name)
        utils.message_callbacks(callbacks, (cls.name, pdb_object.id, "end"))
        return True

    def computed(cls, pdb_object):
        """Check if the step was already computed.

        pdb_object : PDBObject
            PDB structure to be handled
        """
        return cls.name in pdb_object.completed_steps


    def ready(cls, pdb_object):
        """Check if the dependencies of the step have been fulfilled.

        pdb_object : PDBObject
            PDB structure to be handled
        """
        return all(map(lambda x: x.computed(pdb_object), cls.requirements))

    def run_until(cls, pdb_object, callbacks=[], surrogate=False):
        """Run step and all dependencies necessary for its execution.

        pdb_object : PDBObject
            PDB structure to be handled
        callbacks : list of callable
            List of callbacks for logging
        surrogate : bool
            Run step as consequence of another step. Default False
        """
        for requirement in cls.requirements:
            if not requirement.run_until(pdb_object, callbacks, surrogate=True):
                return False
        return cls.run(pdb_object,callbacks, force=False, surrogate=surrogate)
        

