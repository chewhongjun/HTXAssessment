# elastic-backend/cv-index.py

import pandas as pd
from elasticsearch import Elasticsearch, helpers
import os
import time


TRANSCRIPTION_CSV_PATH = "../cv-valid-dev/cv-valid-dev_transcribed.csv" # Adjust if path is different

# Elasticsearch Configuration
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX_NAME = "cv-transcriptions"

def create_es_client():
    """Establishes connection to Elasticsearch."""
    try:
        # Simplified connection
        es_client = Elasticsearch([f"http://localhost:9200"])
        
        # Test the connection
        info = es_client.info()
        print(f"fuck")
        print(f"Successfully connected to Elasticsearch: {info['cluster_name']}")
        return es_client
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return None

def create_index_mapping(es_client, index_name):
    """Creates the Elasticsearch index with a specific mapping."""
    if es_client.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting and recreating.")
        es_client.indices.delete(index=index_name, ignore=[400, 404])
        time.sleep(1) # Give ES a moment to delete

    # Define the mapping for your fields
    # generated_text should be 'text' for full-text search
    # Other fields can be 'keyword' for exact matching/filtering or 'float'/'long' for numbers
    mapping = {
        "mappings": {
            "properties": {
                "generated_text": {"type": "text"}, # For full-text search
                "duration": {"type": "float"},      # For numeric range queries
                "age": {"type": "keyword"},         # For exact age values
                "gender": {"type": "keyword"},      # For exact gender values
                "accent": {"type": "keyword"},      # For exact accent values
                # You might want to include other original fields from CSV if needed
                "path": {"type": "keyword"},
                "sentence": {"type": "text"},
                "up_votes": {"type": "long"},
                "down_votes": {"type": "long"},
                "locale": {"type": "keyword"},
                "segment": {"type": "text"},
            }
        }
    }
    es_client.indices.create(index=index_name, body=mapping)
    print(f"Index '{index_name}' created with mapping.")

def generate_actions(df, index_name):
    """Generates documents for bulk indexing."""
    for i, row in df.iterrows():
        doc = row.to_dict()
        # Clean up NaN values, which Elasticsearch might not like depending on type
        for key, value in doc.items():
            if pd.isna(value):
                doc[key] = None # Or remove the key if that's preferred
        # Ensure 'duration' is a float (it should be from cv-decode.py output)
        if 'duration' in doc and doc['duration'] is not None:
             try:
                 # Remove 's' if present and convert to float
                 doc['duration'] = float(str(doc['duration']).replace('s', ''))
             except ValueError:
                 doc['duration'] = None # Set to None if conversion fails

        yield {
            "_index": index_name,
            "_id": f"{row['filename'].replace('.mp3', '')}", # Use filename (without extension) as ID
            "_source": doc,
        }

def index_data(es_client, df, index_name):
    """Indexes DataFrame records into Elasticsearch."""
    print(f"Indexing {len(df)} documents into '{index_name}'...")
    success, failed = helpers.bulk(es_client, generate_actions(df, index_name), chunk_size=1000, request_timeout=200)
    print(f"Indexed {success} documents successfully. {len(failed)} documents failed.")
    if failed:
        print("Some documents failed to index. First 5 errors:")
        for item in failed[:5]:
            print(item)

def main():
    if not os.path.exists(TRANSCRIPTION_CSV_PATH):
        print(f"Error: Transcribed CSV file not found at {TRANSCRIPTION_CSV_PATH}.")
        print("Please ensure you have run cv-decode.py and the output CSV is at the specified path.")
        return

    print(f"Loading data from {TRANSCRIPTION_CSV_PATH}...")
    try:
        df = pd.read_csv(TRANSCRIPTION_CSV_PATH)
        # Ensure 'generated_text' and 'duration' columns exist
        if 'generated_text' not in df.columns or 'duration' not in df.columns:
            print("Error: 'generated_text' or 'duration' columns not found in the CSV.")
            print("Please ensure you are using the output CSV from cv-decode.py.")
            return
        print(f"Loaded {len(df)} records.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    es_client = create_es_client()
    if es_client:
        create_index_mapping(es_client, ES_INDEX_NAME)
        index_data(es_client, df, ES_INDEX_NAME)
        print("Indexing process completed.")

if __name__ == "__main__":
    main()