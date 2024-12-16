Data Processing and Cleaning

Process two types of data: 
1. Recalls
2. Complaints

For Recalls data, here is an exmaple of the Recalls data:

```json
{
    "Manufacturer": "FEDERAL-MOGUL CORPORATION",
    "NHTSACampaignNumber": "07E064000",
    "ReportReceivedDate": "27/08/2007",
    "Component": "FUEL SYSTEM, GASOLINE:DELIVERY:FUEL PUMP",
    "Summary": "CERTAIN FEDERAL-MOGUL AFTERMARKET FUEL PUMPS SOLD UNDER THE BRAND NAMES OF CARTER, ACCUFLOW, NAPA, TRUFLOW, PARTS DEPO, AND PARTS MASTER, SHIPPED BETWEEN AUGUST 2006 AND JULY 2007 FOR USE ON THE VEHICLES LISTED ABOVE.  THE FUEL PUMP DIAPHRAGM IN CERTAIN PRODUCTION RUNS MAY HAVE BEEN IMPROPERLY INSTALLED OR INADEQUATELY TESTED WHICH MAY CAUSE THE FUEL PUMP TO LEAK.",
    "Consequence": "A LEAKING FUEL PUMP COULD CREATE A VEHICLE FIRE HAZARD.",
    "Remedy": "FEDERAL-MOGUL WILL NOTIFY OWNERS AND REPLACE THE DEFECTIVE FUEL PUMPS FREE OF CHARGE.  THE RECALL BEGAN ON OCTOBER 15, 2007.  OWNERS CAN CONTACT FEDERAL-MOGUL AT 248-354-7700.",
    "Notes": "THIS RECALL ONLY PERTAINS TO AFTERMARKET CARTER, NAPA, ACCUFLOW, TRU FLOW, PARTS MASTER, AND PARTS DEPOT BRAND FUEL PUMPS AND HAS NO RELATION TO ANY ORIGINAL EQUIPMENT INSTALLED ON THE LISTED MOTOR VEHICLES.  CUSTOMERS MAY CONTACT THE NATIONAL HIGHWAY TRAFFIC SAFETY ADMINISTRATION'S VEHICLE SAFETY HOTLINE AT 1-888-327-4236 (TTY: 1-800-424-9153); OR GO TO HTTP://WWW.SAFERCAR.GOV.",
    "ModelYear": "1987",
    "Make": "JEEP",
    "Model": "WRANGLER"
}
```

Recalls data are stored under the path: `DataCollection/jeep_wrangler/recalls/jeep_wrangler_1987.json`. There are multiple files for different years ranging from 1987 to 2024.
Each file contains a list of dictionaries, where each dictionary represents a recall.
Process the data by combining `Summary`, `Consequence`, `Remedy`, and `Notes` into a single field called `description`. The rest of the fields add to a field called `metadata`.
Add a field called `type` with the value `recall`.


For Complaints data, here is an exmaple of the Complaints data:

```json
{
        "odiNumber": 11055305,
        "manufacturer": "Chrysler (FCA US, LLC)",
        "crash": false,
        "fire": false,
        "numberOfInjuries": 0,
        "numberOfDeaths": 0,
        "dateOfIncident": "12/01/2017",
        "dateComplaintFiled": "12/18/2017",
        "vin": "1JCMT7544HT",
        "components": "SERVICE BRAKES",
        "summary": "I ORDERED PRONTO BRAKE DRUM PART NUMBER BD80003. THE PART NUMBERS ARE CASTED INTO THE PART. THE DRUMS WERE DIFFERENT AND ONE OF THEM CAUSES THE WHEEL TO FREEZE. THE SOURCE OF THE PARTS FOR THE RETAILER SAID IT WAS DEFECTIVE. THE RETAILER RESHIPPED THE PARTS 3 TIMES, EACH TIME THE DRUMS RECEIVED WERE DEFECTIVE. I WAS FORCED TO SWITCH TO ANOTHER BRAND.",
        "products": [
            {
                "type": "Vehicle",
                "productYear": "1987",
                "productMake": "JEEP",
                "productModel": "WRANGLER",
                "manufacturer": "Chrysler (FCA US, LLC)"
            }
        ]
    },
```

Complaints data are stored under the path: `DataCollection/jeep_wrangler/complaints/jeep_wrangler_1987.json`. There are multiple files for different years ranging from 1987 to 2024.
Each file contains a list of dictionaries, where each dictionary represents a complaint.
Process the data by combining `summary` into a single field called `description`. The rest of the fields add to a field called `metadata`.
Add a field called `type` with the value `complaint`.

Process all the data and store them in a single file called `jeep_wrangler_data.json`.
