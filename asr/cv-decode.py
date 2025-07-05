# cv-decode.py

import pandas as pd
import os
import requests

# --- Configuration ---
# Base directory where the common_voice dataset was unzipped.
DATASET_BASE_DIR = "/Users/chewhongjun/Downloads/common_voice"

# Path to the CSV file relative to DATASET_BASE_DIR
CSV_FILE_RELATIVE_PATH = "cv-valid-dev.csv"

# CORRECTED: Path to the audio files folder relative to DATASET_BASE_DIR.
# Based on your working curl command, the audio files are in a nested 'cv-valid-dev' folder.
AUDIO_FOLDER_RELATIVE_PATH = "cv-valid-dev" # <-- CORRECTED PATH HERE

# Name for the output CSV file with transcriptions (will be created in current working directory)
OUTPUT_CSV_FILE_NAME = "asr/cv-valid-dev_transcribed.csv"

# CORRECTED: ASR API Endpoint (ensure your asr_api.py is running on this address/port)
ASR_API_URL = "http://127.0.0.1:8001/asr" # <-- CORRECTED PORT HERE
# -------------------

def transcribe_audio_with_api(audio_file_full_path, api_url):
    """
    Calls the ASR API to transcribe the given audio file from local disk.

    Args:
        audio_file_full_path (str): The full path to the MP3 audio file on disk.
        api_url (str): The URL of the ASR API.

    Returns:
        str: The transcribed text, or an error message if transcription fails.
    """
    try:
        with open(audio_file_full_path, 'rb') as audio_file:
            files = {'file': (os.path.basename(audio_file_full_path), audio_file, 'audio/mpeg')}
            response = requests.post(api_url, files=files, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            transcription_result = response.json()
            return transcription_result.get('transcription', 'Transcription Error: Missing "transcription" field in API response.')
    except requests.exceptions.ConnectionError:
        return f"Transcription Error: Could not connect to ASR API at {api_url}. Is the FastAPI service running?"
    except requests.exceptions.Timeout:
        return f"Transcription Error: API request timed out after 30 seconds for {os.path.basename(audio_file_full_path)}."
    except requests.exceptions.RequestException as e:
        return f"Transcription Error: API request failed - {e}. Response: {response.text if 'response' in locals() else 'N/A'}"
    except Exception as e:
        return f"Transcription Error: An unexpected error occurred - {e}"

def main():
    """
    Main function to orchestrate reading from unzipped files, transcription, and CSV update.
    """
    # Construct full paths to CSV and audio folder on disk
    csv_full_path = os.path.join(DATASET_BASE_DIR, CSV_FILE_RELATIVE_PATH)
    audio_base_path = os.path.join(DATASET_BASE_DIR, AUDIO_FOLDER_RELATIVE_PATH)

    # Validate paths exist
    if not os.path.exists(DATASET_BASE_DIR):
        print(f"Error: Dataset base directory not found at {DATASET_BASE_DIR}.")
        print("Please ensure your 'common_voice' unzipped folder exists at this path.")
        return
    if not os.path.exists(csv_full_path):
        print(f"Error: CSV file not found at {csv_full_path}. Check DATASET_BASE_DIR and CSV_FILE_RELATIVE_PATH.")
        return
    if not os.path.isdir(audio_base_path):
        print(f"Error: Audio folder not found at {audio_base_path}. Check DATASET_BASE_DIR and AUDIO_FOLDER_RELATIVE_PATH.")
        return

    # Step 1: Read the CSV file directly from disk
    print(f"Reading CSV file from: {csv_full_path}")
    try:
        df = pd.read_csv(csv_full_path)
        print("CSV Columns:", df.columns.tolist())

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Initialize a new column for generated text
    df['generated_text'] = ''

    # Step 2: Transcribe each MP3 file and update the DataFrame
    print(f"Starting transcription of {len(df)} audio files...")
    for index, row in df.iterrows():
        print(index)
        # if index == 5:
        #     break
        audio_filename_from_csv = row['filename'] # Assuming 'filename' column exists and has the MP3 filename

        # Construct the full path to the audio file on disk
        full_audio_path_on_disk = os.path.join(audio_base_path, audio_filename_from_csv)

        if os.path.exists(full_audio_path_on_disk):
            transcribed_text = transcribe_audio_with_api(full_audio_path_on_disk, ASR_API_URL)
            df.at[index, 'generated_text'] = transcribed_text
        else:
            print(f"Warning: Audio file not found: {full_audio_path_on_disk}. Skipping transcription for this row.")
            df.at[index, 'generated_text'] = 'FILE_NOT_FOUND_ON_DISK'

        if (index + 1) % 10 == 0 or (index + 1) == len(df):
            print(f"Processed {index + 1}/{len(df)} files.")

    # Step 3: Save the updated DataFrame to a new CSV file
    try:
        df.to_csv(OUTPUT_CSV_FILE_NAME, index=False)
        print(f"Transcription complete. Updated CSV saved to: {os.path.abspath(OUTPUT_CSV_FILE_NAME)}")
    except Exception as e:
        print(f"Error saving updated CSV: {e}")
    return

if __name__ == "__main__":
    main()