import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define the path to the 'ssense' directory and the output directory
ssense_path = 'ssense'  # Replace with actual path
output_path = os.path.join(ssense_path, 'output')
out_image_path = 'out_image'  # Replace with actual path

# Ensure the out_image directory exists
if not os.path.exists(out_image_path):
    os.makedirs(out_image_path)

# Function to download and save an image
def download_image(image_url, save_path):
    try:
        print(f"Downloading image from: {image_url}")
        response = requests.get(image_url, timeout=10)  # Set a timeout for the request
        response.raise_for_status()  # Check if the request was successful
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Successfully downloaded and saved to: {save_path}")
    except requests.RequestException as e:
        print(f"Failed to download {image_url}: {e}")

# Function to process each line in img_urls.txt
def process_line(line):
    try:
        number, image_url = line.split(',', 1)  # Split only at the first comma
        number = number.strip()
        image_url = image_url.strip()

        # Create a directory in out_image with the name of the number
        number_folder_path = os.path.join(out_image_path, number)
        if not os.path.exists(number_folder_path):
            os.makedirs(number_folder_path)
            print(f"Created directory: {number_folder_path}")

        # Correctly format the image filename using the last parts of the URL
        image_name_parts = image_url.split('/')
        image_filename = f"{image_name_parts[-2]}-{image_name_parts[-1]}"
        save_path = os.path.join(number_folder_path, image_filename)

        # Check if the image already exists
        if os.path.exists(save_path):
            print(f"Image already exists at: {save_path}, skipping download.")
        else:
            # Download and save the image
            download_image(image_url, save_path)
    except Exception as e:
        print(f"Error processing line: {line}, Error: {e}")

# Traverse the 'output' directory
for folder_name in os.listdir(output_path):
    folder_path = os.path.join(output_path, folder_name)

    # Check if it's a directory and contains img_urls.txt
    if os.path.isdir(folder_path):
        img_urls_path = os.path.join(folder_path, 'img_urls.txt')
        if os.path.exists(img_urls_path):
            print(f"Processing file: {img_urls_path}")

            # Read the img_urls.txt file
            with open(img_urls_path, 'r') as file:
                lines = file.readlines()

            # Use ThreadPoolExecutor to process lines concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(process_line, line.strip()) for line in lines if line.strip()]
                for future in as_completed(futures):
                    future.result()  # Ensure exceptions are raised

print("Process completed.")
