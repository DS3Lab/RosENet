def message_callbacks(callbacks, message):
    for callback in callbacks:
        callback(message)
