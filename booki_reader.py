import os
import re
import requests

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
            archive_success = fetch_and_save_kii(number, folder_path)

            # If both description and archive are successfully downloaded, remove all occurrences of the number from the file
            if description_success and archive_success:
                remove_number_from_file(file_path, number)

def fetch_and_save_description(number, folder_path):
    # Strip leading zeros for the URL, but save the file with leading zeros
    number_stripped = str(int(number))  # Remove leading zeros for the URL
    padded_number = number.zfill(5)     # Ensure the number is zero-padded up to 5 digits for the filename
    
    # URL to fetch description
    description_url = f"http://13.80.138.170/book-files/get-description/id/{number_stripped}/area/en/sn/5497559973888/"
    
    # Fetch description
    response = requests.get(description_url)
    
    # Check if the work is found
    if response.text.strip() == "work not found":
        print(f"Work not found for number {number}")
        return False
    
    # Create books folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Save description to file with leading zeros
    description_file_path = os.path.join(folder_path, f"{padded_number}_en.txt")
    with open(description_file_path, 'w') as file:
        file.write(response.text)
    
    print(f"Description for number {number} saved to {description_file_path}")
    return True

def fetch_and_save_kii(number, folder_path):
    # Strip leading zeros for the URL, but save the file with leading zeros
    number_stripped = str(int(number))  # Remove leading zeros for the URL
    padded_number = number.zfill(5)     # Ensure the number is zero-padded up to 5 digits for the filename
    
    # URL to fetch archive
    archive_url = f"http://13.80.138.170/book-files/get/id/{number_stripped}/area/en/type/archive/sn/5497559973888/"
    
    # Fetch archive file
    response = requests.get(archive_url)
    
    # Check if the file is found
    if response.text.strip() == "file not found":
        print(f"File not found for number {number}")
        return False
    
    # Save archive to file with leading zeros
    archive_file_path = os.path.join(folder_path, f"{padded_number}_en.kii")
    with open(archive_file_path, 'wb') as file:
        file.write(response.content)
    
    print(f"Archive for number {number} saved to {archive_file_path}")
    return True

def remove_number_from_file(file_path, number):
    # Remove all occurrences of the line that contains the number from the tbd.txt or TDB.txt file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Rewrite the file without the lines containing the number
    with open(file_path, 'w') as file:
        for line in lines:
            if number not in line:
                file.write(line)
    
    print(f"Removed all occurrences of number {number} from {file_path}")

def search_for_usb_drives():
    # Start searching from drive E onwards
    for drive_letter in range(ord('E'), ord('Z') + 1):
        drive = f"{chr(drive_letter)}:\\"
        
        if os.path.exists(drive):
            folder_books = os.path.join(drive, 'book')
            folder_configure = os.path.join(drive, 'configure')
            
            # Check if both 'book' and 'configure' folders exist
            if os.path.isdir(folder_books) and os.path.isdir(folder_configure):
                print(f"Valid USB drive found: {drive}")
                
                # Check for tbd.txt or TDB.txt
                tbd_file = os.path.join(folder_configure, 'tbd.txt')
                TDB_file = os.path.join(folder_configure, 'TDB.txt')
                
                if os.path.isfile(tbd_file):
                    print(f"tbd.txt found on {drive}")
                    process_tbd_file(tbd_file, folder_books)
                elif os.path.isfile(TDB_file):
                    print(f"TDB.txt found on {drive}")
                    process_tbd_file(TDB_file, folder_books)

if __name__ == "__main__":
    search_for_usb_drives()
    input("Press Enter to exit...")
