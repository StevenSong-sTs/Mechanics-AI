from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

print("Reading data file...")
with open("../DataProcessing/jeep_wrangler_data_with_embedding.json", "r") as f:
    data = json.load(f)

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Wait for the index to be ready
while not pc.describe_index(os.getenv('PINECONE_INDEX_NAME')).status['ready']:
    time.sleep(1)

index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))

print("Upserting data...")
total_records = len(data)

for i, record in enumerate(data):
    try:
        index.upsert(
            vectors=[record]
        )
        print(f"\rProcessed {i+1}/{total_records} records", end="")
    except Exception as e:
        print(f"\nError processing record {i}:")
        print(f"Record ID: {record.get('id', 'unknown')}")
        print(f"Error message: {str(e)}")
        print("Continuing with next record...\n")

print("Done!")
