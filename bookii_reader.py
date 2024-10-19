import os
import re
import requests
import signal
import atexit
from tqdm import tqdm

# Global variable to keep track of the current file being downloaded
current_download_file = None

def process_tbd_file(file_path, folder_path):
    with open(file_path, 'r') as file:
        contents = file.read()

    # Extract all numeric values from the file (e.g., "05054", "MID=5126", etc.)
    numbers = re.findall(r'\b\d+\b', contents)
    
    # Track processed numbers to avoid duplicates
    processed_numbers = set()

    for number in numbers:
        if number not in processed_numbers:
            processed_numbers.add(number)
            description_success = fetch_and_save_description(number, folder_path)
            kii_file_success = fetch_and_save_kii(number, folder_path)

            # If both description and kii file are successfully downloaded, remove all occurrences of the number from the file
            if description_success and kii_file_success:
                remove_number_from_file(file_path, number)

def fetch_and_save_description(number, folder_path):
    global current_download_file
    number_stripped = str(int(number))  # Remove leading zeros for the URL
    padded_number = number.zfill(5)     # Ensure the number is zero-padded up to 5 digits for the filename
    
    description_url = f"http://13.80.138.170/book-files/get-description/id/{number_stripped}/area/en/sn/5497559973888/"
    
    # Fetch description with streaming enabled
    response = requests.get(description_url, stream=True)
    
    if response.status_code == 404:
        print(f"Work not found for number {number}")
        return False
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    description_file_path = os.path.join(folder_path, f"{padded_number}_en.txt")
    current_download_file = description_file_path  # Track the current file for cleanup

    # Total size is unknown for text responses, so we use a dummy value for the progress bar
    total_size = len(response.content) if response.content else 0
    
    # Write the file in chunks while updating the progress bar
    with open(description_file_path, 'w', encoding='utf-8') as file, tqdm(
        desc=f"Downloading description {number}",
        total=total_size, unit='B', unit_scale=True, ncols=80, leave=False
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                file.write(chunk)
                bar.update(len(chunk))  # Update the progress bar based on chunk size
    
    print(f"Description for number {number} saved to {description_file_path}")
    current_download_file = None  # Reset after successful download
    return True

def fetch_and_save_kii(number, folder_path):
    global current_download_file
    number_stripped = str(int(number))
    padded_number = number.zfill(5)

    kii_file_url = f"http://13.80.138.170/book-files/get/id/{number_stripped}/area/en/type/archive/sn/5497559973888/"
    
    response = requests.get(kii_file_url, stream=True)
    
    if response.status_code == 404:
        print(f"File not found for number {number}")
        return False
    
    kii_file_path = os.path.join(folder_path, f"{padded_number}_en.kii")
    current_download_file = kii_file_path  # Track the current file for cleanup

    total_size = int(response.headers.get('content-length', 0))  # Get content length from headers
    with open(kii_file_path, 'wb') as file, tqdm(
        desc=f"Downloading kii file {number}",
        total=total_size, unit='B', unit_scale=True, ncols=80, leave=False
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                bar.update(len(chunk))  # Update the progress bar based on chunk size
    
    print(f"Kii file for number {number} saved to {kii_file_path}")
    current_download_file = None  # Reset after successful download
    return True

def remove_number_from_file(file_path, number):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if number not in line:
                file.write(line)
    
    print(f"Removed all occurrences of number {number} from {file_path}")

def search_for_usb_drives():
    for drive_letter in range(ord('E'), ord('Z') + 1):
        drive = f"{chr(drive_letter)}:\\"
        
        if os.path.exists(drive):
            folder_books = os.path.join(drive, 'book')
            folder_configure = os.path.join(drive, 'configure')
            
            if os.path.isdir(folder_books) and os.path.isdir(folder_configure):
                print(f"Valid USB drive found: {drive}")
                
                tbd_file = os.path.join(folder_configure, 'tbd.txt')
                TDB_file = os.path.join(folder_configure, 'TDB.txt')
                
                if os.path.isfile(tbd_file):
                    print(f"tbd.txt found on {drive}")
                    process_tbd_file(tbd_file, folder_books)
                elif os.path.isfile(TDB_file):
                    print(f"TDB.txt found on {drive}")
                    process_tbd_file(TDB_file, folder_books)

def cleanup():
    global current_download_file
    if current_download_file and os.path.exists(current_download_file):
        print(f"Cleaning up incomplete download: {current_download_file}")
        os.remove(current_download_file)

def handle_exit_signal(signum, frame):
    print("\nCaught exit signal (Ctrl+C). Cleaning up...")
    cleanup()
    exit(0)

if __name__ == "__main__":
    # Register cleanup function for when the script exits
    atexit.register(cleanup)

    # Capture Ctrl + C (SIGINT) and SIGTERM for proper cleanup
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    # Run the USB search process
    try:
        search_for_usb_drives()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        cleanup()

    input("Press Enter to exit...")
