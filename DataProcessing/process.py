import json
import os
import glob

def process_recall(recall):
    """Process a single recall record"""
    # Combine text fields into description
    description = " ".join([
        recall.get("Summary", ""),
        recall.get("Consequence", "") or "",
        recall.get("Remedy", ""),
        recall.get("Notes", "")
    ]).strip()
    
    # Remove text fields that were combined
    metadata = recall.copy()
    del metadata["Summary"]
    del metadata["Consequence"] 
    del metadata["Remedy"]
    del metadata["Notes"]
    
    return {
        "type": "recall",
        "description": description,
        "metadata": metadata
    }

def process_complaint(complaint):
    """Process a single complaint record"""
    # Use summary as description
    description = complaint.get("summary", "")
    
    # Remove summary field and process metadata
    metadata = complaint.copy()
    del metadata["summary"]
    
    # Keep only first product and rename fields
    if "products" in metadata and len(metadata["products"]) > 0:
        first_product = metadata["products"][0]
        metadata["ModelYear"] = first_product.get("productYear")
        metadata["Make"] = first_product.get("productMake") 
        metadata["Model"] = first_product.get("productModel")
    
    # Delete products field
    del metadata["products"]

    # Rename the `components` field to `Component`
    metadata["Component"] = metadata["components"]
    del metadata["components"]

    return {
        "type": "complaint", 
        "description": description,
        "metadata": metadata
    }

def process_data():
    """Process all recall and complaint data"""
    processed_data = []

    # Process recalls
    recall_files = glob.glob("../DataCollection/jeep_wrangler/recalls/jeep_wrangler_*.json")
    for i, file_path in enumerate(recall_files):
        # Print the progress in a single line with a progress bar
        progress = (i + 1) / len(recall_files) * 100
        bar_length = 20
        filled_length = int(bar_length * progress / 100)
        bar = '=' * filled_length + '-' * (bar_length - filled_length) 
        print(f"\rProcessing recalls... [{bar}] {progress:.1f}%", end="")
        
        with open(file_path) as f:
            recalls = json.load(f)
            for recall in recalls:
                processed_data.append(process_recall(recall))
                
    # Process complaints
    complaint_files = glob.glob("../DataCollection/jeep_wrangler/complaints/jeep_wrangler_*.json") 
    for i, file_path in enumerate(complaint_files):
        # Print the progress in a single line with a progress bar
        progress = (i + 1) / len(complaint_files) * 100
        bar_length = 20
        filled_length = int(bar_length * progress / 100)
        bar = '=' * filled_length + '-' * (bar_length - filled_length) 
        print(f"\rProcessing complaints... [{bar}] {progress:.1f}%", end="")
        
        with open(file_path) as f:
            complaints = json.load(f)
            for complaint in complaints:
                processed_data.append(process_complaint(complaint))
                
    # Save combined data
    with open("jeep_wrangler_data.json", "w") as f:
        json.dump(processed_data, f, indent=4)

if __name__ == "__main__":
    process_data()
