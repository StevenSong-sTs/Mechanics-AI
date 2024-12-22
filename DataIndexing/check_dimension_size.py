import json

# Read the data file
with open("../DataProcessing/jeep_wrangler_data_with_embedding.json", "r") as f:
    data = json.load(f)

# Get first record's embedding length
embedding_size = len(data[0]["embedding"])
print(f"Embedding dimension size: {embedding_size}")
