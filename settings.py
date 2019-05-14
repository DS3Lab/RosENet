from Repo.voxelization.filter import exp_12
size = 25
voxelization_type = "filter"
voxelization_fn = "exp_12"
voxelization = ("filter", exp_12)
options = f"_{voxelization_type}_{voxelization_fn}_{size}"
max_epochs = 100
parallel_calls = 20
shuffle_buffer_size = 1000
batch_size = 128
prefetch_buffer_size = 10
rotate = True

