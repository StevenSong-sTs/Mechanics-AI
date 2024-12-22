import json

# Read the data file
print("Reading data file...")
with open("jeep_wrangler_data_with_embedding.json", "r") as f:
    data = json.load(f)

total_records = len(data)
print(f"Processing {total_records} records...")

# Process each record
for i, record in enumerate(data):
    # Print progress
    progress = (i + 1) / total_records * 100
    bar_length = 20
    filled_length = int(bar_length * progress / 100)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    print(f"\rProgress: [{bar}] {progress:.1f}%", end="")
    
    # Add id field
    record["id"] = str(i)
    
    # Move type and description to metadata
    record["metadata"]["type"] = record.pop("type")
    record["metadata"]["description"] = record.pop("description")
    
    # Rename embedding field to values
    record["values"] = record.pop("embedding")

print("\nSaving processed data...")

# Save the processed data
with open("jeep_wrangler_data_with_embedding.json", "w") as f:
    json.dump(data, f, indent=4)

print("Done!")

