from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def encode_descriptions():
    """Read data, encode descriptions, and save with embeddings"""
    # Read the input data
    with open("jeep_wrangler_data.json", "r") as f:
        data = json.load(f)
    
    # Process each record
    for i, record in enumerate(data):
        # Print progress
        progress = (i + 1) / len(data) * 100
        bar_length = 20
        filled_length = int(bar_length * progress / 100)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)
        print(f"\rEncoding descriptions... [{bar}] {progress:.1f}%", end="")
        
        # Get description and encode it
        description = record["description"]
        embedding = model.encode(description).tolist()
        
        # Add embedding to record
        record["embedding"] = embedding
    
    # Save processed data
    with open("jeep_wrangler_data_with_embedding.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print("\nDone!")

if __name__ == "__main__":
    encode_descriptions()

