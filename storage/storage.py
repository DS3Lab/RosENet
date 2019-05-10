
def read_image(image_path):
    return settings.storage_provider.image.read_image(image_path)

def write_image(image_path, image):
    return settings.storage_provider.image.write_image(image_path, image)
