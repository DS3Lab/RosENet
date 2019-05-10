
def preprocess_step(step_number, path, recompute=False):
    done = pipeline.check_done(step_number, path)
    if done and not recompute:
        return True
    else:
        pipeline.step(step_number, path, force=True)
