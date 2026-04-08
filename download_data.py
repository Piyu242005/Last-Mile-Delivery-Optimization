import os
import requests
from tqdm import tqdm

# Directory where the datasets will be saved
DATASET_DIR = "Dataset"

# Official NYC TLC Trip Record Data URLs
# Using the 2015 and 2016 Parquet files (officially hosted on AWS Cloudfront by NYC)
# You can add more URLs here as needed by your project
URLS = [
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2015-01.parquet",
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2016-01.parquet",
]

def download_file(url, output_dir):
    """
    Downloads a file from a URL to the specified directory with a progress bar.
    Skips downloading if the file already exists.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = url.split("/")[-1]
    filepath = os.path.join(output_dir, filename)

    # 1. Check if file already exists
    if os.path.exists(filepath):
        print(f"[SKIP] {filename} already exists at {filepath}.")
        return

    print(f"\n[DOWNLOAD] Starting download for {filename}...")
    try:
        # 2. Use requests with stream=True for large files
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP errors
        
        # Get the total file size from headers
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte chunk size
        
        # 3. Write file and update tqdm progress bar
        with open(filepath, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(block_size):
                size = file.write(data)
                bar.update(size)
                
        print(f"[SUCCESS] Successfully saved {filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {filename}: {e}")
        # Clean up partial or corrupted files in case of failure
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"[CLEANUP] Removed partial file {filepath}")

def main():
    print(f"--- NYC Taxi Dataset Downloader ---")
    print(f"Target Directory: {os.path.abspath(DATASET_DIR)}")
    
    # Iterate through all configured URLs
    for url in URLS:
        download_file(url, DATASET_DIR)
        
    print("\n--- All Downloads Completed ---")

if __name__ == "__main__":
    main()
