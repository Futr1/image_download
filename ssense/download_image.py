import os

def count_subfolders(directory):
    return sum(os.path.isdir(os.path.join(directory, item)) for item in os.listdir(directory))

out_image_path = 'output'
print(f"Number of subfolders: {count_subfolders(out_image_path)}")
