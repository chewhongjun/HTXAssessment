import os
import requests
import zipfile
import io
import pandas as pd

# Constants
DATASET_URL = "https://www.dropbox.com/scl/fi/i9yvfqpf7p8uye5o8k1sj/common_voice.zip?rlkey=lz3dtjuhekc3xw4jnoeoqy5yu&dl=1"
DATASET_ZIP_PATH = "common_voice.zip"
EXTRACT_FOLDER = "cv-valid-dev"
CSV_FILE = os.path.join(EXTRACT_FOLDER, "cv-valid-dev.csv")
OUTPUT_CSV_FILE = os.path.join(EXTRACT_FOLDER, "cv-valid-dev-updated.csv")
API_URL = "http://localhost:8001/asr"


def download_and_extract_dataset():
    print("Downloading dataset...")
    response = requests.get(DATASET_URL)
    response.raise_for_status()

    with open(DATASET_ZIP_PATH, "wb") as f:
        f.write(response.content)

    print("Extracting dataset...")
    with zipfile.ZipFile(DATASET_ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(EXTRACT_FOLDER)

    os.remove(DATASET_ZIP_PATH)
    print("Dataset downloaded and extracted.")


def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
        response = requests.post(API_URL, files=files)
        response.raise_for_status()
        result = response.json()
        return result.get("transcription", "")


def main():
    if not os.path.exists(EXTRACT_FOLDER) or not os.path.exists(CSV_FILE):
        download_and_extract_dataset()

    df = pd.read_csv(CSV_FILE)
    generated_texts = []

    for idx, row in df.iterrows():
        mp3_filename = row.get("path") or row.get("filename") or row.get("file")
        if not mp3_filename:
            generated_texts.append("")
            continue

        mp3_path = os.path.join(EXTRACT_FOLDER, mp3_filename)
        if not os.path.isfile(mp3_path):
            generated_texts.append("")
            continue

        try:
            transcription = transcribe_audio(mp3_path)
        except Exception as e:
            transcription = ""
        generated_texts.append(transcription)

    df["generated_text"] = generated_texts
    df.to_csv(OUTPUT_CSV_FILE, index=False)
    print(f"Transcriptions saved to {OUTPUT_CSV_FILE}")


if __name__ == "__main__":
    main()