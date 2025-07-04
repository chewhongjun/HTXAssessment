import os
import csv
import requests
import pandas as pd

API_URL = "http://localhost:8001/asr"
MP3_FOLDER = "cv-valid-dev"
CSV_FILE = os.path.join(MP3_FOLDER, "cv-valid-dev.csv")
OUTPUT_CSV_FILE = os.path.join(MP3_FOLDER, "cv-valid-dev-updated.csv")


def transcribe_audio(file_path: str) -> str:
    """Send audio file to ASR API and return transcription text."""
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
        response = requests.post(API_URL, files=files)
        response.raise_for_status()
        result = response.json()
        return result.get("transcription", "")


def main():
    # Load CSV
    df = pd.read_csv(CSV_FILE)

    # Prepare list to hold generated texts
    generated_texts = []

    # Iterate over each row and transcribe corresponding mp3 file
    for idx, row in df.iterrows():
        mp3_filename = row.get("path") or row.get("filename") or row.get("file")
        if not mp3_filename:
            generated_texts.append("")
            continue

        mp3_path = os.path.join(MP3_FOLDER, mp3_filename)
        if not os.path.isfile(mp3_path):
            generated_texts.append("")
            continue

        try:
            transcription = transcribe_audio(mp3_path)
        except Exception as e:
            transcription = ""
        generated_texts.append(transcription)

    # Add new column
    df["generated_text"] = generated_texts

    # Save updated CSV
    df.to_csv(OUTPUT_CSV_FILE, index=False)


if __name__ == "__main__":
    main()