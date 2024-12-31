import json

# Read the JSON file
with open('jeep_wrangler_data_with_embedding.json', 'r') as f:
    data = json.load(f)

# Remove null fields from metadata for each record
total = len(data)
for i, record in enumerate(data):
    if i % 1000 == 0:
        print(f"Processing record {i}/{total} ({(i/total)*100:.1f}%)")
    metadata = record['metadata']
    # Create new dict with non-null values
    cleaned_metadata = {k: v for k, v in metadata.items() if v is not None}
    record['metadata'] = cleaned_metadata
print(f"Finished processing all {total} records")

# Write back to file
with open('jeep_wrangler_data_with_embedding.json', 'w') as f:
    json.dump(data, f, indent=4)
