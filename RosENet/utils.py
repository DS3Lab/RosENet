def message_callbacks(callbacks, message):
    """Utility function to broadcast messages to a list of callbacks.

    callbacks : list of callable
        List of callbacks
    message : various
        Message to broadcast
    """
    for callback in callbacks:
        callback(message)
