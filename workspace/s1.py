import requests
import datetime
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import timedelta
import time
from cross_field import build_mongodb_query
from check import MongoQueryValidator

# Define the request model
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str

app = FastAPI()

# --- MongoDB Connection Setup ---
from pymongo import MongoClient

mongo_uri = "mongodb://eventdb-0.eventdb.userland/kafkaData"
db_name = "kafkaData"
collection_name = "event-stream"
mongo_client = None
db = None
collection = None

try:
    print(f"Attempting to connect to MongoDB at {mongo_uri}...")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    db = mongo_client[db_name]
    collection = db[collection_name]
    print(f"Successfully connected to MongoDB. Database: '{db_name}', Collection: '{collection_name}'.")
    print(f"Total Documents in the DB collection '{collection_name}': {collection.count_documents({})}")
except Exception as e:
    print(f"FATAL: Failed to connect to MongoDB on startup: {e}")

# Caching dictionaries
mindb = {}
listdone = {}

# Example task ID from original script, used in 'desc' queries
queue_management_task_id = '66d188490fe484f60a379c47'

# Date and time setup
dt = datetime.datetime.now()
t = datetime.time(0)
dt_0 = dt.combine(dt, t)
formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
formatted_dt_0 = dt_0.strftime('%Y-%m-%dT%H:%M:%SZ')
dt_minus_one_day = dt_0 - timedelta(days=1)
dt_plus_7_day_ago = dt_0 - timedelta(days=7)
formatted_dt_plus_7_ago = dt_plus_7_day_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
formatted_dt_minus_one_0 = dt_minus_one_day.strftime('%Y-%m-%dT%H:%M:%SZ')
dt_plus_one_day_0 = dt_0 + timedelta(days=1)
formatted_dt_plus_one_0 = dt_plus_one_day_0.strftime('%Y-%m-%dT%H:%M:%SZ')

prefix = " The current date and time is " + str(formatted_dt_0)
print(f"Formatted dt_0 (midnight today): {formatted_dt_0}")
valid =True
# Add validation mappings

VEHICLE_ATTRIBUTE_MAPPINGS = {
    "vehicle_type": ["sedan", "suv", "micro", "hatchback", "wagon", "pick_up", "convertible"],
    # "vehicle_color": ["khakhi", "silver", "yellow", "pink", "purple", "green", "blue", "brown", "maroon", "red", "orange", "violet", "white", "black", "grey"],
    "brand_name": ["tvs", "maruti_suzuki", "eicher", "ashok_leyland", "mercedes_benz", "royal_enfield", "chevrolet", "fiat", "jaguar", "audi", "toyota", "sml", "bajaj", "jbm", "bharat_benz", "hero_motor", "volvo", "nissan", "renault", "volkswagen", "mazda", "hero_honda", "hyundai", "mg", "skoda", "land_rover", "yamaha", "kia", "mahindra", "mitsubishi", "ford", "jeep", "tata_motors", "honda", "bmw", "coupe", "force"],
    "vehicle_i_type": ["hmv", "lmv", "lgv", "3_axle", "5_axle", "mcwg", "6_axle", "2_axle", "4_axle", "heavy_vehicle"],
    "special_type": ["army_vehicle", "ambulance", "graminseva_4wheeler", "graminseva_3wheeler", "campervan"],
    "label": ["bus", "car", "truck", "motorbike", "bicycle", "e_rikshaw", "cycle_rikshaw", "tractor", "cement_mixer", "mini_truck", "mini_bus", "mini_van", "van"]
}

PERSON_ATTRIBUTE_MAPPINGS = {
    "upper_type": ["stride", "splice", "casual", "formal", "jacket", "logo", "plaid", "thin_stripes", "tshirt", "other", "v_neck", "suit", "thick_stripes", "shirt", "sweater", "vest", "cotton", "suit_up", "tight"],
    "lower_type": ["stripe", "pattern", "long_coat", "trousers", "shorts", "skirt_and_dress", "boots", "long_trousers", "skirt", "short_skirt", "dress", "jeans", "tight_trousers", "capri", "hot_pants", "long_skirt", "plaid", "thin_stripes", "suits", "casual", "formal", "jeans", "shorts", "trousers"],
    "footwear": ["leather", "sport", "boots", "cloth", "casual", "sandals", "boots", "stocking", "leather_shoes", "shoes", "sneaker"],
    "gender": ["female", "male"],
    "age": ["child", "adult", "older_adult"],
    "body_type": ["fat", "normal", "thin"],
    "hair_type": ["bald_head", "long_hair", "short_hair"],
    "accessories": ["glasses", "muffler", "hat", "muffler", "nothing", "headphone", "hair_band", "kerchief"],
    "sleeve_type": ["short_sleeve", "long_sleeve"],
    "orientation": ["front", "side", "back"],
    "actions": ["calling", "talking", "gathering", "holding", "pushing", "pulling", "carry_arm", "carry_hand"]
}
def convert_llm_output_to_list(llm_output_str):
    import json
    parsed_output = json.loads(llm_output_str)
    field_value_pairs = []
    for key, value in parsed_output.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str):
                    field_value_pairs.append((sub_value, sub_key))
    return field_value_pairs

def validate_and_correct_attributes(query_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and corrects hallucinated attribute mappings in the query by ensuring
    each value is mapped to its correct key based on the attribute dictionaries.
    Returns the corrected query dictionary.
    """
    if not isinstance(query_dict, dict):
        return query_dict

    # Handle nested attribs structure
    if "response.event.blobs.attribs" in query_dict:
        #print("query_dict46",query_dict)
        attribs = query_dict["response.event.blobs.attribs"]
        if not isinstance(attribs, dict):
            return query_dict
        #print("query_dict50",query_dict)
        corrected_attribs = {}
        processed_values = set()  # Track which values we've already processed

        # First pass: Find the correct key for each value
        for key, value in attribs.items():
            if not isinstance(value, str):
                corrected_attribs[key] = value
                #print("query_value",value)
                continue

            value_lower = value.lower()
            
            # Skip if we've already processed this value
            if value_lower in processed_values:
                continue

            # Check if the current key is correct for this value
            key_is_correct = False
            
            # Check vehicle attributes
            for vehicle_key, vehicle_values in VEHICLE_ATTRIBUTE_MAPPINGS.items():
                if value_lower in vehicle_values:
                    if key == vehicle_key:
                        #print("query_key_value_correct   ",key,value_lower)
                        key_is_correct = True
                        corrected_attribs[vehicle_key] = value
                    else:
                        corrected_attribs[vehicle_key] = value
                        #print("query_key_value_incorrect  ",key,value_lower)
                    processed_values.add(value_lower)
                    break

            # If not found in vehicle attributes, check person attributes
            if not key_is_correct and value_lower not in processed_values:
                for person_key, person_values in PERSON_ATTRIBUTE_MAPPINGS.items():
                    if value_lower in person_values:
                        
                        if key == person_key:
                            #nprint("kkkkk",key)
                            key_is_correct = True
                            corrected_attribs[person_key] = value
                        else:
                            #print("kkk92kk",key)
                            corrected_attribs[person_key] = value
                        processed_values.add(value_lower)
                        break
            #print("corrected_attribs",corrected_attribs)
            # If the key was correct and we haven't processed this value yet, keep it
            if key_is_correct and value_lower not in processed_values:
                #print("99",key_is_correct)
                corrected_attribs[key] = value
                processed_values.add(value_lower)
        
        # Second pass: Handle any remaining attributes that weren't processed
        for key, value in attribs.items():
            if isinstance(value, str) and value.lower() not in processed_values:
                # If we couldn't find a matching attribute, keep the original
                corrected_attribs[key] = value
        query_dict["response.event.blobs.attribs"] = corrected_attribs
    print("query_key_value_correct   ",query_dict)
    return query_dict

main_message_part_1 = """You are an expert AI assistant that translates natural language queries into precise MongoDB query JSON objects.
Your sole output MUST be the MongoDB query in a valid JSON format. Do NOT include any introductory phrases, explanations, apologies, markdown code blocks (like ```json ... ```), or any text outside the JSON object.

Adhere strictly to the following guidelines when generating the MongoDB query:

1.  **Output Format:**
    * Your response MUST be ONLY the MongoDB query in a valid JSON format.
    * No extra text, explanations, or markdown.

2.  **MongoDB Schema:**
    * Utilize this MongoDB schema for constructing queries:
      ```json
      {
        "collections": [
          {
            "name": "events",
            "document": {
              "properties": {
                "identifier": {
                  "bsonType": "object",
                  "properties": {
                    "camgroup_id": { "description": "Filter by group (e.g., 'office')" },
                    "task_id": { "description": "Filter by task (use short_name from Task ID Mapping below). This is preferred for specific event types like 'Abandoned Bag Alert'." },
                    "camera_id": { "description": "Filter by camera (e.g., 'Raj Ghat', 'south_fr')" }
                  }
                },
                "response": {
                  "bsonType": "object",
                  "properties": {
                    "event": {
                      "bsonType": "object",
                      "properties": {
                        "severity": { "description": "Event severity: Low, Medium, Critical" },
                        "type": { "description": "Event type (e.g., 'person', 'vehicle')" },
                        "blobs": {
                          "bsonType": "array",
                          "items": {
                            "bsonType": "object",
                            "properties": {
                              "url": {},
                              "attribs": {
                                "description": "Key-value pairs for attributes. For People: use keys from Person Attributes. For Vehicles: use keys from Vehicle Attributes. For number plates, use 'ocr_result'. For vehicle type (e.g. car, truck) use 'label' within 'attribs'."
                              },
                              
                              "score": { "description": "Confidence score (e.g., 'score greater than 70 percent' means 'score': {'$gt': 0.7})" } For number plate text, 'attribs.ocr_result' is preferred. For general vehicle type (car, truck etc.), use 'label' WITHIN 'attribs'." } ,
                              "match_id": { "description": "Name of the person (e.g., 'Yash', 'Pravar')" },
                              "severity": {},
                              "subclass": { "description": "Subclass for the blob" }
                            }
                          }
                        },
                        "c_timestamp": { "description": "Timestamp of the event. Format: 'YYYY-MM-DDTHH:MM:SSZ'." }
                      }
                    }
                  }
                }
              }
            }
          }
        ],
        "version": 1
      }
      ```

3.  **Attribute-Based Queries:**
    * **Person Attributes:** For person-related queries, use exact attribute names and permissible values from the 'personattribute' dictionary.
      ```json
      "personattribute": { "footwear_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"], "carrying_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"], "lower_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"], "upper_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"], "gender": ["female", "male"], "age": ["child", "adult", "older_adult"], "body_type": ["fat", "normal", "thin"], "hair_type": ["bald_head", "long_hair", "short_hair"], "hair_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"], "accessories": ["glasses", "muffler", "hat", "muffler", "nothing", "headphone", "hair_band", "kerchief"], "sleeve_type": ["short_sleeve", "long_sleeve"], "orientation": ["front", "side", "back"], "actions": ["calling", "talking", "gathering", "holding", "pushing", "pulling", "carry_arm", "carry_hand"], "upper_type": ["stride", "splice", "casual", "formal", "jacket", "logo", "plaid", "thin_stripes", "tshirt", "other", "v_neck", "suit", "thick_stripes", "shirt", "sweater", "vest", "cotton", "suit_up", "tight"], "footwear": ["leather", "sport", "boots", "cloth", "casual", "sandals", "boots", "stocking", "leather_shoes", "shoes", "sneaker"], "carrying": ["hand_bag", "shoulder_bag", "hold_objects_in_front", "backpack", "messenger_bag", "nothing", "plastic_bags", "baby_buggy", "shopping_trolley", "umbrella", "folder", "luggage_case", "suitcase", "box", "plastic_bag", "paper_bag", "hand_trunk", "other"], "lower_type": ["stripe", "pattern", "long_coat", "trousers", "shorts", "skirt_and_dress", "boots", "long_trousers", "skirt", "short_skirt", "dress", "jeans", "tight_trousers", "capri", "hot_pants", "long_skirt", "plaid", "thin_stripes", "suits", "casual", "formal", "jeans", "shorts", "trousers"]}
      ```
    * **Vehicle Attributes:** For vehicle-related queries, use exact attribute names and permissible values from the 'vehicle_attribute' dictionary.
        * For vehicle type (e.g., car, truck, bus): Use `attribs.label`.
        * For number plate text/characters: Use `attribs.ocr_result`.
      ```json
      "vehicle_attribute": { "brand_name": ["tvs", "maruti_suzuki", "eicher", "ashok_leyland", "mercedes_benz", "royal_enfield", "chevrolet", "fiat", "jaguar", "audi", "toyota", "sml", "bajaj", "jbm", "bharat_benz", "hero_motor", "volvo", "nissan", "renault", "volkswagen", "mazda", "hero_honda", "hyundai", "mg", "skoda", "land_rover", "yamaha", "kia", "mahindra", "mitsubishi", "ford", "jeep", "tata_motors", "honda", "bmw", "coupe", "force"], "vehicle_color": ["khakhi", "silver", "yellow", "pink", "purple", "green", "blue", "brown", "maroon", "red", "orange", "violet", "white", "black", "grey"], "orientation": ["front", "back", "side"], "label": ["bus", "car", "truck", "motorbike", "bicycle", "e_rikshaw", "cycle_rikshaw", "tractor", "cement_mixer", "mini_truck", "mini_bus", "mini_van", "van"], "vehicle_i_type": ["hmv", "lmv", "lgv", "3_axle", "5_axle", "mcwg", "6_axle", "2_axle", "4_axle", "heavy_vehicle"], "vehicle_type": ["sedan", "suv", "micro", "hatchback", "wagon", "pick_up", "convertible"], "special_type": ["army_vehicle", "ambulance", "graminseva_4wheeler", "graminseva_3wheeler", "campervan"]}
      ```

4.  **Task ID Mapping:**
    * For queries specifying application alerts (e.g., "License Plate Recognition alerts", "Abandoned Objects"), use `identifier.task_id`. Map the full application label to its `short_name` from this list:
      ```json

    [{"label": "License Plate Recognition", "short_name": "ANPR"}, {"label": "Crowd Estimation", "short_name": "CROWD_EST"}, {"label": "Crowd Count", "short_name": "CROWD_COUNT"}, {"label": "Facial Recognition", "short_name": "FR"}, {"label": "Abandoned Bag Alert", "short_name": "ABANDONED_BAG"}, {"label": "Intruder Alert", "short_name": "INTRUDER_DETECT"}, {"label": "Camera Tampering", "short_name": "CAM_TAMPERING"}, {"label": "Person Slip Detection", "short_name": "SLIP_DETECT"}, {"label": "PPE Violation", "short_name": "PPE_VOILATION"}, {"label": "Wrong Way", "short_name": "wrong_way"}, {"label": "Helmet Violation", "short_name": "helmet_violation"}, {"label": "Triple Riding", "short_name": "triple_riding"}, {"label": "Speed Violation", "short_name": "speed_violation"}, {"label": "Red Light Violation", "short_name": "red_light_violation"}, {"label": "Violence Detection", "short_name": "violence_detection"}, {"label": "Loitering", "short_name": "dwell"}, {"label": "Woman In Isolation", "short_name": "wii"}, {"label": "Woman Hailing Help", "short_name": "whh"}, {"label": "Queue Management", "short_name": "qm"}, {"label": "Tailgating", "short_name": "tg"}, {"label": "Lane violation", "short_name": "lane_violation"}, {"label": "Seat belt", "short_name": "seatbelt"}, {"label": "Parking violation", "short_name": "parking_violation"}, {"label": "Person Attribute", "short_name": "pat"}, {"label": "Vehicle Attribute", "short_name": "vat"} ,{"label": "Fire and Smoke Detection", "short_name": "fns"} ,  {"label": "VIDES","short_name": "parking_violation"} ]
      ```
    * **Crucial:** When a query clearly maps to one of these tasks (e.g., "find abandoned objects" should map to "ABANDONED_BAG", "find helmet violations" should map to "helmet_violation"), prioritize using `identifier.task_id`. Only use `task_id` if the query explicitly or implicitly (based on examples like `q32`, or general terms like "helmet violations") refers to a task.

5.  **Date and Time Handling (IMPORTANT RULES):**
    * A prefix like "The current date and time is [timestamp]" is added to every user query you receive. This prefix is SOLELY for your contextual awareness if the user asks for relative dates (e.g., "today", "yesterday").
    * **VERY CRUCIAL RULE:** This prefix MUST NOT cause you to add a `c_timestamp` filter UNLESS the user's *actual query text* (the part after the prefix) contains explicit date or time keywords (e.g., "today", "yesterday", "last week", "on Sept 10", "between X and Y", "from March to April").
    * **Default Behavior:** If the user's query (e.g., "find helmet violations", "find abandoned objects", "find Yash") does NOT contain any words indicating a date, time, or time period, then your generated MongoDB query MUST NOT include the `c_timestamp` field. Refer to examples like `a1`, `a5`, `a7`, `a10`, `a12`, `a33`, `a41` which correctly omit time filters.
    * **When to Add Time Filters:** Only apply a `c_timestamp` filter if the user's specific query text explicitly mentions a date, a time, or a relative time period.
        * If a query specifies a date but no specific time (e.g., "today", "yesterday", "on 10th Sept"), the time range should cover the entire specified day(s).
            * Example for "today": `{"c_timestamp": { "$gte": "${formatted_dt_0}", "$lte": "${formatted_dt_plus_one_0}" }}`
            * Example for "yesterday": `{"c_timestamp": { "$gte": "${formatted_dt_minus_one_0}", "$lte": "${formatted_dt_0}" }}`
            * Example for a specific date "10th sept": `{"c_timestamp": {"$gte": "YYYY-09-10T00:00:00Z", "$lte": "YYYY-09-11T00:00:00.000Z"}}`
        * If a query specifies a date range (e.g., "from 10 aug to 15 aug"), ensure the range is inclusive as per the examples.
        * Always use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS.sssZ`) for timestamps.

6.  **Confidence Score:**
    * For queries involving confidence (e.g., "score greater than 70 percent"), use `score` with operators like `$gt`, `$lt` (e.g., `{"$gt": 0.7}`).

7.  **Regular Expressions for Partial String Matches:**
    * When searching for number plates (`attribs.ocr_result`) that contain, start with, or end with specific characters or sequences, MUST use the `$regex` operator.
        * For a query like "starts with 'XYZ'": use `{"$regex": "^XYZ"}`
        * For a query like "ends with 'XYZ'": use `{"$regex": "XYZ$"}`
        * For a query like "contains 'XYZ'" or "has 'XYZ'": use `{"$regex": "XYZ"}`
        * For a query like "with 'XYZ' in the plate": use `{"$regex": "XYZ"}`
        * For a query like "starts with 'ABC' and ends with 'Z' ": use `{"$regex": "^ABC.*Z$"}`
        * For a query like "starts with 'B1' and ends with '22' ": use `{"$regex": "^B1.*22$"}`


        * For instance, if the query is "find number plates having 04", the MongoDB query part for the number plate should be `{"attribs.ocr_result": {"$regex": "04"}}`.
    * Ensure the regex pattern directly reflects the sequence of characters mentioned in the query for "contains" or "having" scenarios.
"""
# --- End of Re-engineered Prompt ---

from pymongo import MongoClient
# MongoDB connection URI
MONGO_URI  = "mongodb://admin:password@platform-db-0.platform-db.userland/cctv_db"  # Replace with your MongoDB URI
DB_NAME = "cctv_db"  # Your database name
try: 
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=500)
    def get_data_from_mongo(db_name, collection_name):
        db = client.get_database(db_name)
        collection = db[collection_name]
        return collection
    cam_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='camera')
    Camera_list=[] #str ( cam_collection)
    for cam in cam_collection.find():
        Camera_list.append(cam['label'])
    Camera_list =str(Camera_list)

    cam_group_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='cameragroup')
    cam_group_collection_list = []
    for cam in cam_group_collection.find():
        cam_group_collection_list = cam['camgroupname']
    cam_group_collection_list=str(cam_group_collection_list)

    site_list=[]
    site_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='sites')
    for site in site_collection.find():
        site_list.append(  site["name"])
    site_list=str(site_list)
    main_message_part_1 += f"""THE LIST OF ALL POSSIBLE CAMERAS IS {Camera_list}. THE LIST OF ALL POSSIBLE CAMERA GROUPS IS {cam_group_collection}. THE LIST OF ALL POSSIBLE SITES IS {site_list} .
    The following are examples of user queries and the desired MongoDB query output. Pay close attention to how attributes, dates, task IDs, and other conditions are translated.
    --- EXAMPLES START ---
    """
except:

    main_message_part_1 += f""" The following are examples of user queries and the desired MongoDB query output. Pay close attention to how attributes, dates, task IDs, and other conditions are translated.
    --- EXAMPLES START ---
    """

#print(main_message_part_1)
system_message_obj = {
    "role": "system",
    "content": "You are a helpful AI assistant."
}
prompt_history = [system_message_obj]

# --- Example Queries and Answers ---
q1 = str(prefix + "  Find yash")
a1 = '{"match_id": "Yash"}'
q2 = str(prefix + " . was Pravar present today")
a2 = '{ "match_id": "Pravar", "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
q3 = str(prefix+ " was Nikhil seen in last 7 days")
a3 = '{ "match_id": "Nikhil", "c_timestamp": { "$gte": "' + str(formatted_dt_plus_7_ago) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
q4= prefix + " Find all events from 10 aug to 15 aug"
a4= '{"c_timestamp": {"$gte": "2025-08-10T00:00:00Z", "$lte": "2025-08-16T00:00:00.000Z"}}'
q5= prefix + " Find all events of vehicle with number plate GJ10SS1010"
a5= '{"attribs.ocr_result": "GJ10SS1010"}'
q6= prefix + " Find all alerts of Rajat from 10 jan 2025 to 12 jan 2025 "
a6= '{ "match_id": "Rajat", "c_timestamp": {"$gte": "2025-01-10T00:00:00Z", "$lte": "2025-01-13T00:00:00.000Z"} }'
q7= prefix + " Find all events of person wearing glasses"
a7= '{"attribs.accessories": "glasses"}'
q8=prefix + " Find events of yash on 10th sept"
a8='{"match_id": "Yash", "c_timestamp": {"$gte": "2025-09-10T00:00:00Z", "$lte": "2025-09-11T00:00:00.000Z"}}'
q9=prefix + " Find events of athul on 1st sept with score greater than 70 percent"
a9='{"match_id": "Athul", "c_timestamp": {"$gte": "2025-09-01T00:00:00Z", "$lte": "2025-09-02T00:00:00.000Z"}, "score": {"$gt": 0.7}}'
q10= prefix + " Find vehicle with number plate starting with GJ"
a10='{"attribs.ocr_result": {"$regex": "^GJ"}}'
q11= prefix + "  Retrieve all events for vehicles with number plates ending in '1010'."
a11= '{"attribs.ocr_result": {"$regex": "1010$"}}'
q12= prefix + " List all alerts of license plate task"
a12= '{"task_id": "ANPR"}'
q13= prefix + " find Person Slip Detection results in 'south_fr' camera"
a13= '{"camera_id": "south_fr" , "task_id": "SLIP_DETECT"} '
q14= prefix + " Find all events on raj ghat camera"
a14= '{"camera_id": "Raj Ghat"}'
q15= prefix + " Find all events on office group"
a15= '{"camgroup_id": "office"}'
q16= prefix + " provide alerts when someone wore a vneck and capri"
a16= '{ "attribs":{ "upper_type": "v_neck","lower_type": "capri" }}'
q17= prefix + " Find all events of Helmet Violation of today " # This example correctly includes time due to "of today"
a17= '{ "task_id": "helmet_violation", "c_timestamp": {"$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
q18=  prefix + " Find alerts of man wearing shirt today "
a18=  '{ "attribs":{ "upper_type": "shirt", "gender": "male"}, "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
q19=   prefix + " find events of children who wore hat and boots"
a19=    '{ "attribs":{"age":"child", "accessories": "hat","footwear": "boots" }}'
q20=   prefix + " find events of kids with a box and wearing long trousers"
a20=    '{ "attribs":{"age":"child", "carrying": "box","lower_type": "long_trousers" }}'
q21=   prefix + " give alerts of fat people wearing blue tshirt and sport shoes yesterday"
a21=    '{ "attribs":{"upper_type": "tshirt","footwear":"sport", "upper_color":"blue" , "body_type":"fat"}, "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"} }'
q22=  prefix + " find woman wearing hat and wearing black casual shoes"
a22=   '{ "attribs":{"gender":"female", "accessories": "hat","footwear": "casual", "footwear_color":"black" }}'
q23= prefix + " find woman"
a23= '{ "attribs":{"gender":"female"}}'
q24=   prefix + " find woman wearing glasses and sport shoes today "
a24=    '{ "attribs":{"gender":"female", "accessories": "glasses","footwear": "sport" } , "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
q25=  prefix + " give alerts of fat young adult men wearing vest , tight_trousers and sport shoes"
a25=  '{ "attribs":{ "age":"adult", "upper_type": "vest", "lower_type": "tight_trousers", "footwear":"sport", "gender":"male", "body_type":"fat"}}'
q26= prefix + " give alerts of normal bald elderly man wearing suit, tight_trousers and casual shoes"
a26=  '{ "attribs":{ "age":"older_adult", "upper_type": "suit_up", "lower_type": "tight_trousers", "footwear":"casual", "gender":"male", "body_type":"normal", "hair_type": "bald_head" }}'
q27=prefix + " filter out events of thin woman with long hair wearing sunglasses, skirt and short sleeve"
a27='{ "attribs":{ "body_type":"thin", "sleeve_type": "short_sleeve", "lower_type": "skirt", "hair_type":"long_hair", "gender":"female", "accessories":"glasses" }}'
q28= prefix + " Find yesterdays events of Ishaan "
a28= '{"match_id": "Ishaan", "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"}}'
q29=prefix + " send alerts of young adult woman with black hair wearing sweater , dress and carrying a pink paper bag"
a29= '{ "attribs":{ "age":"adult", "upper_type": "sweater", "lower_type": "dress", "carrying":"paper_bag", "carrying_color":"pink", "gender":"female", "hair_color":"black" }}'
q30= prefix + " Find all Red cars"
a30= '{ "attribs":{ "vehicle_color": "red", "label":"car" }}'
q31= prefix + " Find all blue TVS Ambulances "
a31= '{ "attribs":{ "brand_name":"tvs", "special_type": "ambulance", "vehicle_color":"blue", "label": "ambulance" }}'
q32= prefix + " Find all Abandoned Objects found from 10th march to 20th march "
a32= '{ "task_id": "ABANDONED_BAG", "c_timestamp": {"$gte": "2025-03-10T00:00:00Z", "$lte": "2025-03-21T00:00:00.000Z"} }'
q33=   prefix + " List all alerts of Loitering task"
a33=   '{"task_id": "dwell"}'
q34= prefix + " Find all events of a side view person carrying hand bag from 3rd april to today "
a34= '{"attribs": {"carrying":"hand_bag", "orientation":"side" }, "c_timestamp": {"$gte": "2025-04-03T00:00:00Z", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
q35= prefix + " Find all events of person calling while wearing short sleeve from jan 10 to yesterday "
a35= '{"attribs": {"actions":"calling", "sleeve_type":"short_sleeve" }, "c_timestamp": {"$gte": "2025-01-10T00:00:00Z", "$lte": "' + str(formatted_dt_0) + '"} }'
q36 = prefix + "find men alerts from yesterday"
a36 = '{ "attribs":{ "gender":"male"}, "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"}}'
q37= prefix + " Find  mini bus that are khakhi and 3 axle "
a37= '{ "attribs":{ "vehicle_i_type":"3_axle", "vehicle_color": "khakhi", "label":"mini_bus" }}'
q38= prefix + " Find all motorbikes that are  mcwg by kia "
a38= '{ "attribs":{ "vehicle_i_type":"mcwg", "brand_name": "kia", "label":"motorbike" }}'
q39= prefix + " Find all white cars"
a39= '{ "attribs":{"vehicle_color": "white", "label":"car" }}'
q40= prefix + " Find all ambulances"
a40= '{ "attribs":{ "special_type": "ambulance", "label": "ambulance"} }'
q41= prefix + " Find all alerts of collapsed person"
a41= '{ "task_id": "SLIP_DETECT" }'
q42= prefix + " Find all vehicles with speed more than 20"
a42= '{"attribs.speed": {"$gte": 20 } }'
q43 = prefix + "find all  plates which are one row"
a43 = '{ "attribs.plate_layout":"one_row" }'
q44= prefix + " give all alerts of violation" # General violation query
a44= '{"attribs.violation":"true" }' # No time filter unless specified
q45= prefix + " give all alerts of violation of two row number plates"
a45= '{"attribs": {"violation":"true", "plate_layout":"two_row"} }'
q46 = prefix + "find all Non Commercial Plates "
a46 = '{ "attribs.registration_type": "non_commercial_plate" }'
q47 = prefix + "find all rlvd alerts " # Red light violation
a47 = '{ "task_id": "red_light_violation" }' # Assuming general RLVD alerts, not specific to a 'true' attribute here unless query implies it
                                                       # And no time filter unless specified.
q48= prefix + " Find all LMVs that are black and made  by honda "
a48= '{ "attribs":{ "vehicle_i_type":"lmv", "brand_name": "honda", "vehicle_color":"black" }}'
q49= prefix + " Find vehicle with number plate containing L1"
a49='{"attribs.ocr_result": {"$regex": "L1"}}'
q50= prefix + " Find vehicle with number plate starting with JH and ending with 1"
a50='{"attribs.ocr_result": {"$regex": "^JH.*1$"}}'
q51= prefix + " Find blue Maruti cars having 223 in their license plate "
a51='{"attribs":{"ocr_result": {"$regex": "L1"},"vehicle_color":"blue",  "brand_name": "maruti_suzuki"}}'

examples_string = ""
examples_data = [
    (q1, a1), (q2, a2), (q3, a3), (q4, a4), (q5, a5), (q6, a6), (q7, a7), (q8, a8), (q9, a9), (q10, a10),
    (q11, a11), (q12, a12), (q13, a13), (q14, a14), (q15, a15), (q16, a16), (q17, a17), (q18, a18), (q19, a19), (q20, a20),
    (q21, a21), (q22, a22), (q23, a23), (q24, a24), (q25, a25), (q26, a26), (q27, a27), (q28, a28), (q29, a29), (q30, a30),
    (q31, a31), (q32, a32), (q33, a33), (q34, a34), (q35, a35), (q36, a36), (q37, a37), (q38, a38), (q39, a39), (q40, a40),
    (q41, a41), (q42, a42), (q43, a43), (q44, a44), (q45, a45), (q46, a46), (q47, a47), (q48, a48),  (q49, a49),(q50,a50)
]
for q_text, a_text in examples_data:
    examples_string += f"Query : {q_text} assistant : {a_text} , "
if examples_string.endswith(" , "):
    examples_string = examples_string[:-3]

trailing_instructions_content = ". --- EXAMPLES END --- \nIMPORTANT: Your final output must be ONLY the MongoDB query in valid JSON format. No other text, explanations, or markdown are permitted."
full_initial_prompt_content = main_message_part_1 + examples_string + trailing_instructions_content
prompt_history.append({"role": "user", "content": full_initial_prompt_content})


last_updated = datetime.date.today()


def replace_in_dict_keys_and_values(data, old_string, new_string):
    """
    Recursively replaces occurrences of old_string with new_string in
    both keys and string values of a dictionary or list.
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # Replace in key
            new_key = key.replace(old_string, new_string) if isinstance(key, str) else key
            # Recursively replace in value
            new_value = replace_in_dict_keys_and_values(value, old_string, new_string)
            new_dict[new_key] = new_value
        return new_dict
    elif isinstance(data, list):
        return [replace_in_dict_keys_and_values(elem, old_string, new_string) for elem in data]
    elif isinstance(data, str):
        # Replace in string value
        return data.replace(old_string, new_string)
    else:
        # Return other types (int, float, bool, None) as is
        return data


# cache_value
cache_value  = True
def check_and_reset_dict():
    global listdone, last_updated
    today = datetime.date.today()
    print("today  ",today)
    if last_updated  != today:
        print("Resetting dictionary.")
        listdone = {}  # Reset the dictionary
        last_updated = datetime.datetime.now()


def remove_string_null_values(obj):
    """
    Recursively removes keys from dictionaries if their value is the string "null".
    Also handles lists containing dictionaries or the string "null".
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if not (isinstance(v, str) and v == "null"):
                processed_value = remove_string_null_values(v)
                if processed_value is not None and not (isinstance(processed_value, dict) and not processed_value):
                    new_dict[k] = processed_value
        return new_dict
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            if not (isinstance(item, str) and item == "null"):
                processed_item = remove_string_null_values(item)
                if processed_item is not None and not (isinstance(processed_item, dict) and not processed_item):
                    new_list.append(processed_item)
        return new_list
    elif isinstance(obj, str) and obj == "null":
        return None 
    else:
        return obj


# --- FastAPI Endpoint ---
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    print(f"Request received for query: {request.query}")
    text = request.query.strip()
    text.replace("search","find")
    text.replace("show","find")
    text.replace("vides","VIDES")
    text.replace("look","find")
    text.replace("give","find")
    text.replace("return","find")
    
    current_prompt_messages = list(prompt_history)

    if not text.startswith("desc"):
        print("nondesc")
        text.replace("search","find")
        text.replace("show","find")
        text.replace("vides","VIDES")
        text.replace("look","find")
        text.replace("give","find")
        text.replace("return","find")
        check_and_reset_dict()
        last_updated = datetime.datetime.today().date()

        if text in listdone:
            time.sleep(1.5)
            print("cached  ",listdone[text])
            return  {"query": listdone[text]}
        print(f"Processing standard query: {text}")
        current_dt = datetime.datetime.now()
        current_formatted_dt = current_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        user_query_with_time = f"The current date and time is {current_formatted_dt}. Write the correct JSON query for and remember to STRICTLY use attribs whenever ATTRIBUTES OF VEHICLE OR PERSON and DO NOT add c_timestamp unless date/time is mentioned in the following text: {text} /no_think"
        print(user_query_with_time)
        current_prompt_messages.append({"role": "user", "content": user_query_with_time})

        global cache_value
        if(cache_value):
            print ("@@@@@@@@@@@@@@@")
        payload = {
                "slot_id": 0, "temperature": 0.0, "n_keep": -1,"sampling-seq":1, "top-k":1,
            "cache_prompt": cache_value, "messages": current_prompt_messages,
            "chat_template_kwargs": {"enable_thinking": "false"},"top_p": 0.0
        }
        cache_value = False
        headers = {'Content-Type': 'application/json'}
        print("Sending request to LLM for standard query...")
        try:
            r = requests.post("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(payload), headers=headers, timeout=30)
            r.raise_for_status()
            response_json = r.json()
            raw_llm_output = response_json["choices"][0]["message"]["content"]
            json_content = raw_llm_output.replace("```json\n", "").replace("\n```", "").replace("```", "").strip()
            json_content =json_content.replace("</think>","")
            json_content =json_content.replace("<think>","").strip()
            print(f"LLM Raw Output--: {json_content}")
            out_list = convert_llm_output_to_list(json_content)
            json_content = json_content.replace("match_id", "response.event.blobs.match_id").replace("task_id", "identifier.task_id").replace("attribs", "response.event.blobs.attribs").replace("c_timestamp", "response.event.c_timestamp").replace("camera_id", "identifier.camera_id").replace("camgroup_id", "identifier.camgroup_id").strip()
            parsed_json_obj = json.loads(json_content)
            parsed_json_obj=  remove_string_null_values(parsed_json_obj)
            print(f"Parsed JSON Object: {parsed_json_obj}")
            attribs = parsed_json_obj.get('response.event.blobs.attribs')
            if attribs:
    # Create a list of keys to avoid modifying dict during iteration
                keys_to_process = list(attribs.keys())
    
                for key in keys_to_process:
                    value = attribs[key]
                    print(f"{key}: {value}")
                    res = build_mongodb_query(value, key)
                    if res['query']:
                        print("check1 done")
                        del attribs[key]
                        for fkey, fval in res['query'].items():
                            attribs[fkey] = fval
                    else:
                         valid = False
            validated_json_obj = validate_and_correct_attributes(parsed_json_obj)
            validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.vehicle_color","vehicle_color")
            validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.upper_color","upper_color")
            validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.lower_color","lower_color")
            validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.footwear_color","footwear_color")
            final_query_str = json.dumps(validated_json_obj)
            
        except requests.exceptions.RequestException as e:
            print(f"LLM Request failed: {e}")
            final_query_str = json.dumps({"error": "LLM request failed", "details": str(e)})
#        except json.JSONDecodeError as e:
#            print(f"Failed to parse LLM JSON output: {e}. Output was: {json_content}")
#            print("Retrying due to query difficulty (original fallback logic path)")
#            current_prompt_messages_for_retry = list(current_prompt_messages) 
#            current_prompt_messages_for_retry.append({"role": "user", "content": f"The previous attempt resulted in a JSON error. Please provide only the valid MongoDB query. Original request: {text} /no_think" })
#            retry_payload = {
#                "slot_id":0, "temperature": 0.05, "n_keep": -1,
#                "cache_prompt": True, "messages": current_prompt_messages_for_retry 
#            }
#            try:
#                r_retry = requests.post("[http://127.0.0.1:8080/v1/chat/completions](http://127.0.0.1:8080/v1/chat/completions)", data=json.dumps(retry_payload), headers=headers, timeout=30)
#                r_retry.raise_for_status()
#                retry_response_json = r_retry.json()
#                raw_llm_output = response_json["choices"][0]["message"]["content"]
#                json_content = raw_llm_output.replace("```json\n", "").replace("\n```", "").replace("```", "").strip()
#                json_content =json_content.replace("</think>","")
#                json_content =json_content.replace("<think>","").strip()
#                print(f"LLM Raw Output: {json_content}")
#                json_content = json_content.replace("match_id", "response.event.blobs.match_id").replace("task_id", "identifier.task_id").replace("attribs", "response.event.blobs.attribs").replace("c_timestamp", "response.event.c_timestamp").replace("camera_id", "identifier.camera_id").replace("camgroup_id", "identifier.camgroup_id").strip()
#                parsed_json_obj = json.loads(json_content)
#                # Add validation step here
#                validated_json_obj = validate_and_correct_attributes(parsed_json_obj)
#                final_query_str = json.dumps(validated_json_obj)
#
#            except Exception as retry_e:
#                print(f"LLM Retry also failed: {retry_e}")
#        except (KeyError, IndexError) as e:
#            print(f"Unexpected LLM response structure: {e}. Response: {response_json if 'response_json' in locals() else 'N/A'}")
#            final_query_str = json.dumps({"error": "Unexpected LLM response structure", "details": str(e)})
#
        print(f"Final MongoDB Query String: {final_query_str}")
        listdone[text] = final_query_str
        print(final_query_str,"FINAL")
        validator = MongoQueryValidator()
        result_json =validator.validate_and_filter_query(request.query,final_query_str)
        print("check2 done")
        print(result_json)

        return {"query": final_query_str}
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
#############################################################
    elif text.startswith("desc"):
        desc_query_text = text.strip()[4:]
        print(f"Processing description query: {desc_query_text}")

        if not collection:
            print("MongoDB collection not available for 'desc' query.")
            return {"query": json.dumps({"error": "MongoDB connection not available."})}

        if desc_query_text in mindb:
            print(f"Cache hit for desc query: {desc_query_text}")
            return mindb[desc_query_text]

        matching_event_ids = []
        try:
            events_cursor = collection.find({"identifier.task_id": queue_management_task_id})
            
            for event_doc in events_cursor:
                try:
                    description = event_doc['response']['event']['blobs'][0]['attribs']['description']
                except (KeyError, IndexError, TypeError):
                    print(f"Could not fetch description for event_id: {event_doc.get('response', {}).get('event', {}).get('event_id', 'Unknown')}")
                    description = "" 

                if not description:
                    continue

                desc_check_messages = [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": f"Question: {desc_query_text}. Does the following text description contain exact info to the Question? (answer in yes or no only) Closely look at all attributes or colours mentioned in the text. Answer 'Yes' if the detail is stated in the text, 'No' if contradicted, and 'Not Given' if neither supported nor contradicted. Text description: {description}"}
                ]
                desc_payload = {
                    "slot_id": 0, "temperature": 0.0, "n_keep": -1,
                    "cache_prompt": True, "top_k": 1, "messages": desc_check_messages
                }
                headers = {'Content-Type': 'application/json'}
                
                print(f"Sending request to LLM for description check (event_id: {event_doc.get('response', {}).get('event', {}).get('event_id', 'Unknown')})...")
                r_desc = requests.post("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(desc_payload), headers=headers, timeout=20)
                r_desc.raise_for_status()
                
                desc_response_json = r_desc.json()
                desc_llm_answer = desc_response_json["choices"][0]["message"]["content"].strip().lower()
                print(f"LLM relevance answer for description: {desc_llm_answer}")

                if "yes" in desc_llm_answer:
                    event_id = event_doc.get('response', {}).get('event', {}).get('event_id')
                    if event_id:
                        matching_event_ids.append(event_id)
            
            print(f"Found matching event_ids for '{desc_query_text}': {matching_event_ids}")

            final_query_dict = {"response.event.event_id": {"$in": matching_event_ids}}
            final_query_json_str = json.dumps(final_query_dict)
            result_json = {"query": final_query_json_str}
            mindb[desc_query_text] = result_json
            validator = MongoQueryValidator()
            result_json=validator.validate_and_filter_query(request,result_json) 
            print("check2 done")
            return result_json

        except requests.exceptions.RequestException as e:
            print(f"LLM Request failed during 'desc' processing: {e}")
            return {"query": json.dumps({"error": "LLM request failed during description processing", "details": str(e)})}
        except Exception as e:
            print(f"Error during 'desc' query processing: {e}")
            return {"query": json.dumps({"error": "General error during description processing", "details": str(e)})}


if __name__ == "__main__":
    import uvicorn
    if not collection:
        print("WARNING: MongoDB collection is not initialized. 'desc' queries will not function reliably.")
    uvicorn.run(app, host="0.0.0.0", port=6769)
