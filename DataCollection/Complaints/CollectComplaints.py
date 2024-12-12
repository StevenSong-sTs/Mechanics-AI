import requests
import json

def collect_recalls(make, model, start_year, end_year):
    for year in range(start_year, end_year + 1):
        # Print the progress in a single line with a progress bar
        progress = (year - start_year + 1) / (end_year - start_year + 1) * 100
        bar_length = 20
        filled_length = int(bar_length * progress / 100)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)
        print(f"\rCollecting recalls for {make} {model} {year}... [{bar}] {progress:.1f}%", end="")
        
        # Make the request to the API
        url = f"https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}"
        response = requests.get(url)
        data = response.json()

        # Save the file in pretty format 
        with open(f"{make}_{model}_{year}.json", "w") as f:
            json.dump(data["results"], f, indent=4)

collect_recalls("jeep", "wrangler", 1987, 2024)
