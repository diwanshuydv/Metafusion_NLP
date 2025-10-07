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
from query_validator import MongoQueryValidator
import time
import aiohttp
import asyncio
from data_v3.data_utils.line_based_parsing import (
    parse_line_based_query
)
from data_v3.data_utils.base_conversion_utils import (
    build_schema_maps,
    convert_modified_to_actual_code_string
)
from recons_query import (schema_mapping,construct_mongo_query_string,convert_simple_to_mongo_query)
from ner import add_person_to_mongo_query

# Define the request model
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str

app = FastAPI()

async def get_results_async(query, top_k=6):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:6080/query",
            json={"query": query, "top_k": top_k}
        ) as resp:
            return (await resp.json())["results"]

def extract_attribs_from_llm_output(llm_output, schema_mapping):
    """
    Extract only the keys from LLM output that belong under response.event.blobs.attribs
    """
    attribs = {}
    
    for key, value in llm_output.items():
        # Check if this key maps to a path under response.event.blobs.attribs
        if key in schema_mapping:
            full_path = schema_mapping[key]
            if full_path.startswith("response.event.blobs.attribs."):
                attribs[key] = value
    
    return attribs

# --- MongoDB Connection Setup ---
# from pymongo import MongoClient

# mongo_uri = "mongodb://eventdb-0.eventdb.userland/kafkaData"
# db_name = "kafkaData"
# collection_name = "event-stream"
# mongo_client = None
# db = None
# collection = None

# try:
#     print(f"Attempting to connect to MongoDB at {mongo_uri}...")
#     mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
#     mongo_client.server_info()  # Test connection
#     db = mongo_client[db_name]
#     collection = db[collection_name]
#     print(f"Successfully connected to MongoDB. Database: '{db_name}', Collection: '{collection_name}'.")
#     print(f"Total Documents in the DB collection '{collection_name}': {collection.count_documents({})}")
# except Exception as e:
#     print(f"FATAL: Failed to connect to MongoDB on startup: {e}")

# Caching dictionaries
# mindb = {}
listdone = {}

# Example task ID from original script, used in 'desc' queries
# queue_management_task_id = '66d188490fe484f60a379c47'

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

# prefix = " The current date and time is " + str(formatted_dt_0)
# print(f"Formatted dt_0 (midnight today): {formatted_dt_0}")
valid =True
# Add validation mappings

VEHICLE_ATTRIBUTE_MAPPINGS = {
    "vehicle_type": ["sedan", "suv", "micro", "hatchback", "wagon", "pick_up", "convertible"],
    "vehicle_color": ["khakhi", "silver", "yellow", "pink", "purple", "green", "blue", "brown", "maroon", "red", "orange", "violet", "white", "black", "grey"],
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

def convert_line_parsed_to_mongo(line_parsed: str, schema: Dict[str, Any]) -> str:
    try:
        modified_query = parse_line_based_query(line_parsed)
        collection_name = schema["collections"][0]["name"]
        in2out, _ = build_schema_maps(schema)
        reconstructed_query = convert_modified_to_actual_code_string(modified_query, in2out, collection_name)
        return reconstructed_query
    except Exception as e:
        print(f"Error converting line parsed to MongoDB query: {e}")
        return ""
    

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

main_message_part_1 = """
schema: {"collections":[{"name":"events","document":{"bsonType":"object","properties":{"identifier":{"bsonType":"object","properties":{"camgroup_id":{"bsonType":"string","description":"Usethistofiltereventsbygroup-canbeanynamebasedonsite,location,deployment,custom,orvideoname"},"task_id":{"bsonType":"string","description":"Mapnaturallanguageapplicationnamestotheircorrespondingshort_namevalues","enum":["ANPR","CROWD_EST","CROWD_COUNT","FR","ABANDONED_BAG","INTRUDER_DETECT","CAM_TAMPERING","SLIP_DETECT","PPE_VOILATION","wrong_way","helmet_violation","triple_riding","speed_violation","red_light_violation","violence_detection","dwell","wii","whh","qm","tg","lane_violation","seatbelt","parking_violation","pat","vat","fns"],"mappings":[{"application_name":"LicensePlateRecognition","task_id_value":"ANPR"},{"application_name":"CrowdEstimation","task_id_value":"CROWD_EST"},{"application_name":"CrowdCount","task_id_value":"CROWD_COUNT"},{"application_name":"FacialRecognition","task_id_value":"FR"},{"application_name":"AbandonedBagAlert","task_id_value":"ABANDONED_BAG"},{"application_name":"IntruderAlert","task_id_value":"INTRUDER_DETECT"},{"application_name":"CameraTampering","task_id_value":"CAM_TAMPERING"},{"application_name":"PersonSlipDetection","task_id_value":"SLIP_DETECT"},{"application_name":"PPEViolation","task_id_value":"PPE_VOILATION"},{"application_name":"WrongWay","task_id_value":"wrong_way"},{"application_name":"HelmetViolation","task_id_value":"helmet_violation"},{"application_name":"TripleRiding","task_id_value":"triple_riding"},{"application_name":"SpeedViolation","task_id_value":"speed_violation"},{"application_name":"RedLightViolation","task_id_value":"red_light_violation"},{"application_name":"ViolenceDetection","task_id_value":"violence_detection"},{"application_name":"Loitering","task_id_value":"dwell"},{"application_name":"WomanInIsolation","task_id_value":"wii"},{"application_name":"WomanHailingHelp","task_id_value":"whh"},{"application_name":"QueueManagement","task_id_value":"qm"},{"application_name":"Tailgating","task_id_value":"tg"},{"application_name":"Laneviolation","task_id_value":"lane_violation"},{"application_name":"Seatbelt","task_id_value":"seatbelt"},{"application_name":"Parkingviolation","task_id_value":"parking_violation"},{"application_name":"PersonAttribute","task_id_value":"pat"},{"application_name":"VehicleAttribute","task_id_value":"vat"},{"application_name":"FireandSmokeDetection","task_id_value":"fns"},{"application_name":"VIDES","task_id_value":"parking_violation"}]},"camera_id":{"bsonType":"string","description":"Individualcameraidentifier-canbeanynamebasedonsite,location,deployment,custom,orvideoname"}}},"response":{"bsonType":"object","properties":{"event":{"bsonType":"object","properties":{"event_priority":{"bsonType":"string","enum":["p1","p2","p3","p4"],"description":"Priorityleveloftheeventp1beinghighestandp4lowest"},"event_id":{"bsonType":"string","description":"Uniqueidentifierfortheevent"},"c_timestamp":{"bsonType":"date","description":"Timestampoftheeventinformat\'2025-06-23T00:00:00Z\'"},"blobs":{"bsonType":"array","items":{"bsonType":"object","properties":{"url":{"bsonType":"string"},"blob_priority":{"bsonType":"string","enum":["p1","p2","p3","p4"],"description":"Priorityleveloftheblob"},"attribs":{"bsonType":"object","description":"Attributesforpersonorvehicledetection","properties":{"crowd_estimate":{"bsonType":"int","description":"Integernumbergeneratedbycrowdestimationapp"},"erratic_crowd":{"bsonType":"string","enum":["yes","no"],"description":"Whethercrowdbehavioriserratic"},"crowd_flow_percentage":{"bsonType":"number","minimum":0,"maximum":100,"description":"Crowdflowpercentage"},"special_type":{"bsonType":"string","enum":["army_vehicle","ambulance","graminseva_4wheeler","graminseva_3wheeler","campervan"],"description":"Specialvehicletype"},"brand_name":{"bsonType":"string","enum":["tvs","maruti_suzuki","eicher","ashok_leyland","mercedes_benz","royal_enfield","chevrolet","fiat","jaguar","audi","toyota","sml","bajaj","jbm","bharat_benz","hero_motor","volvo","nissan","renault","volkswagen","mazda","hero_honda","hyundai","mg","skoda","land_rover","yamaha","kia","mahindra","mitsubishi","ford","jeep","tata_motors","honda","bmw","coupe","force"],"description":"Brandnameofthevehicle"},"vehicle_color":{"bsonType":"string","enum":["khakhi","silver","yellow","pink","purple","green","blue","brown","maroon","red","orange","violet","white","black","grey"],"description":"Colorofthevehicle"},"vehicle_type":{"bsonType":"string","enum":["sedan","suv","micro","hatchback","wagon","pick_up","convertible"],"description":"Typeofvehicle"},"vehicle_itype":{"bsonType":"string","enum":["hmv","lmv","lgv","3_axle","5_axle","mcwg","6_axle","2_axle","4_axle","heavy_vehicle"],"description":"Vehicleclassificationtype"},"vehicle_speed":{"bsonType":"number","description":"Speedofthevehicle"},"vehicle_speed_limit":{"bsonType":"number","description":"Speedlimitforthevehicle"},"vehicle_label":{"bsonType":"string","enum":["bus","car","truck","motorbike","bicycle","e_rikshaw","cycle_rikshaw","tractor","cement_mixer","mini_truck","mini_bus","mini_van","van"],"description":"Vehiclelabel-typeofvehicledetected"},"plate_layout":{"bsonType":"string","enum":["one_raw","two_raw"],"description":"Layoutofvehiclelicenseplate"},"ocr_result":{"bsonType":"string","description":"OCRresultfromlicense/numberplateofvehicleusethisforregexnumberplatequery"},"registration_type":{"bsonType":"string","enum":["commercial","non-commercial"],"description":"Vehicleregistrationtype"},"actions":{"bsonType":"string","enum":["calling","talking","gathering","holding","pushing","pulling","carry_arm","carry_hand"],"description":"Actionsbeingperformedbytheperson"},"age":{"bsonType":"string","enum":["child","adult","older_adult"],"description":"Agecategoryoftheperson"},"body_type":{"bsonType":"string","enum":["fat","normal","thin"],"description":"Bodytypeoftheperson"},"carrying":{"bsonType":"string","enum":["hand_bag","shoulder_bag","hold_objects_in_front","backpack","messenger_bag","nothing","plastic_bags","baby_buggy","shopping_trolley","umbrella","folder","luggage_case","suitcase","box","plastic_bag","paper_bag","hand_trunk","other"],"description":"Itemsbeingcarriedbytheperson"},"footwear":{"bsonType":"string","enum":["leather","sport","boots","cloth","casual","sandals","stocking","leather_shoes","shoes","sneaker"],"description":"Typeoffootwear"},"gender":{"bsonType":"string","enum":["female","male"],"description":"Genderoftheperson"},"hair_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Haircoloroftheperson"},"hair_type":{"bsonType":"string","enum":["bald_head","long_hair","short_hair"],"description":"Hairtypeoftheperson"},"lower_type":{"bsonType":"string","enum":["stripe","pattern","long_coat","trousers","shorts","skirt_and_dress","boots","long_trousers","skirt","short_skirt","dress","jeans","tight_trousers","capri","hot_pants","long_skirt","plaid","thin_stripes","suits","casual","formal"],"description":"Typeoflowerbodyclothing"},"upper_type":{"bsonType":"string","enum":["stride","splice","casual","formal","jacket","logo","plaid","thin_stripes","tshirt","other","v_neck","suit","thick_stripes","shirt","sweater","vest","cotton","suit_up","tight"],"description":"Typeofupperbodyclothing"},"upper_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Colorofupperbodyclothing"},"lower_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Coloroflowerbodyclothing"},"occupation":{"bsonType":"string","description":"Occupationoftheperson"},"sleeve_type":{"bsonType":"string","enum":["short_sleeve","long_sleeve"],"description":"Typeofsleevesonupperclothing"},"carrying_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Colorofitemsbeingcarried"},"footwear_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Coloroffootwearforperson"},"accessories":{"bsonType":"string","enum":["glasses","muffler","hat","nothing","headphone","hair_band","kerchief"],"description":"Accessorieswornbytheperson"},"orientation":{"bsonType":"string","enum":["front","back","side"],"description":"Orientationofpersonorvehicle"},"violation":{"bsonType":"string","enum":["yes","no"],"description":"Whetheraviolationoccurred"},"red_light_violation":{"bsonType":"string","enum":["yes","no"],"description":"Whetheraredlightviolationoccurred"},"stop_line_violation":{"bsonType":"string","enum":["yes","no"],"description":"Whetherastoplineviolationoccurred"}}},"score":{"bsonType":"number","minimum":0,"maximum":1,"description":"Confidencescoreforthedetection"},"match_id":{"bsonType":"string","description":"MatchIDforpersonidentification"}}}}}}}}}}}],"version":1}'
Always use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`) for timestamps.
For queries involving confidence (e.g., "score greater than 70 percent"), use `score` with operators like `$gt`, `$lt` (e.g., `"$gt": 0.7`).
    * When searching for number plates (`ocr_result`) that contain, start with, or end with specific characters or sequences, MUST use the `$regex` operator.
        * For a query like "starts with 'XYZ'": use `{"$regex": "^XYZ"}`
        * For a query like "ends with 'XYZ'": use `{"$regex": "XYZ$"}`
        * For a query like "contains 'XYZ'" or "has 'XYZ'": use `{"$regex": "XYZ"}`
        * For a query like "with 'XYZ' in the plate": use `{"$regex": "XYZ"}`
        * For a query like "starts with 'ABC' and ends with 'Z' ": use `{"$regex": "^ABC.*Z$"}`
        * For a query like "starts with 'B1' and ends with '22' ": use `{"$regex": "^B1.*22$"}`


        * For instance, if the query is "find number plates having 04", the MongoDB query part for the number plate should be `{"ocr_result": {"$regex": "04"}}`.
"""
schema ="""{"collections":[{"name":"events","document":{"bsonType":"object","properties":{"identifier":{"bsonType":"object","properties":{"camgroup_id":{"bsonType":"string","description":"Usethistofiltereventsbygroup"},"task_id":{"bsonType":"string","description":"Mapnaturallanguageapplicationnamestotheircorrespondingshort_namevalues","mappings":[{"application_name":"LicensePlateRecognition","task_id_value":"ANPR"},{"application_name":"CrowdEstimation","task_id_value":"CROWD_EST"},{"application_name":"CrowdCount","task_id_value":"CROWD_COUNT"},{"application_name":"FacialRecognition","task_id_value":"FR"},{"application_name":"AbandonedBagAlert","task_id_value":"ABANDONED_BAG"},{"application_name":"IntruderAlert","task_id_value":"INTRUDER_DETECT"},{"application_name":"CameraTampering","task_id_value":"CAM_TAMPERING"},{"application_name":"PersonSlipDetection","task_id_value":"SLIP_DETECT"},{"application_name":"PPEViolation","task_id_value":"PPE_VOILATION"},{"application_name":"WrongWay","task_id_value":"wrong_way"},{"application_name":"HelmetViolation","task_id_value":"helmet_violation"},{"application_name":"TripleRiding","task_id_value":"triple_riding"},{"application_name":"SpeedViolation","task_id_value":"speed_violation"},{"application_name":"RedLightViolation","task_id_value":"red_light_violation"},{"application_name":"ViolenceDetection","task_id_value":"violence_detection"},{"application_name":"Loitering","task_id_value":"dwell"},{"application_name":"WomanInIsolation","task_id_value":"wii"},{"application_name":"WomanHailingHelp","task_id_value":"whh"},{"application_name":"QueueManagement","task_id_value":"qm"},{"application_name":"Tailgating","task_id_value":"tg"},{"application_name":"Laneviolation","task_id_value":"lane_violation"},{"application_name":"Seatbelt","task_id_value":"seatbelt"},{"application_name":"Parkingviolation","task_id_value":"parking_violation"},{"application_name":"PersonAttribute","task_id_value":"pat"},{"application_name":"VehicleAttribute","task_id_value":"vat"},{"application_name":"FireandSmokeDetection","task_id_value":"fns"},{"application_name":"Parkingviolation","task_id_value":"parking_violation"}]},"camera_id":{"bsonType":"string","description":"Individualcameraidentifier-usethisfieldtofiltereventsfromspecificcameras"}}},"response":{"bsonType":"object","properties":{"event":{"bsonType":"object","properties":{"severity":{"bsonType":"string","description":"CanbeLow,Medium,Critical"},"blobs":{"bsonType":"array","items":{"bsonType":"object","properties":{"url":{"bsonType":"string"},"attribs":{"bsonType":"object","description":"Attributesforpersonorvehicledetection","properties":{"footwear_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Coloroffootwearforperson"},"carrying_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Colorofitemsbeingcarried"},"lower_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Coloroflowerbodyclothing"},"upper_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Colorofupperbodyclothing"},"gender":{"bsonType":"string","enum":["female","male"],"description":"Genderoftheperson"},"age":{"bsonType":"string","enum":["child","adult","older_adult"],"description":"Agecategoryoftheperson"},"body_type":{"bsonType":"string","enum":["fat","normal","thin"],"description":"Bodytypeoftheperson"},"hair_type":{"bsonType":"string","enum":["bald_head","long_hair","short_hair"],"description":"Hairtypeoftheperson"},"hair_color":{"bsonType":"string","enum":["black","blue","brown","green","grey","orange","pink","purple","red","white","yellow"],"description":"Haircoloroftheperson"},"accessories":{"bsonType":"string","enum":["glasses","muffler","hat","nothing","headphone","hair_band","kerchief"],"description":"Accessorieswornbytheperson"},"sleeve_type":{"bsonType":"string","enum":["short_sleeve","long_sleeve"],"description":"Typeofsleevesonupperclothing"},"orientation":{"bsonType":"string","enum":["front","side","back"],"description":"Orientationofpersonorvehicle"},"actions":{"bsonType":"string","enum":["calling","talking","gathering","holding","pushing","pulling","carry_arm","carry_hand"],"description":"Actionsbeingperformedbytheperson"},"upper_type":{"bsonType":"string","enum":["stride","splice","casual","formal","jacket","logo","plaid","thin_stripes","tshirt","other","v_neck","suit","thick_stripes","shirt","sweater","vest","cotton","suit_up","tight"],"description":"Typeofupperbodyclothing"},"footwear":{"bsonType":"string","enum":["leather","sport","boots","cloth","casual","sandals","stocking","leather_shoes","shoes","sneaker"],"description":"Typeoffootwear"},"carrying":{"bsonType":"string","enum":["hand_bag","shoulder_bag","hold_objects_in_front","backpack","messenger_bag","nothing","plastic_bags","baby_buggy","shopping_trolley","umbrella","folder","luggage_case","suitcase","box","plastic_bag","paper_bag","hand_trunk","other"],"description":"Itemsbeingcarriedbytheperson"},"lower_type":{"bsonType":"string","enum":["stripe","pattern","long_coat","trousers","shorts","skirt_and_dress","boots","long_trousers","skirt","short_skirt","dress","jeans","tight_trousers","capri","hot_pants","long_skirt","plaid","thin_stripes","suits","casual","formal"],"description":"Typeoflowerbodyclothing"},"brand_name":{"bsonType":"string","enum":["tvs","maruti_suzuki","eicher","ashok_leyland","mercedes_benz","royal_enfield","chevrolet","fiat","jaguar","audi","toyota","sml","bajaj","jbm","bharat_benz","hero_motor","volvo","nissan","renault","volkswagen","mazda","hero_honda","hyundai","mg","skoda","land_rover","yamaha","kia","mahindra","mitsubishi","ford","jeep","tata_motors","honda","bmw","coupe","force"],"description":"Brandnameofthevehicle"},"vehicle_color":{"bsonType":"string","enum":["khakhi","silver","yellow","pink","purple","green","blue","brown","maroon","red","orange","violet","white","black","grey"],"description":"Colorofthevehicle"},"vehicle_i_type":{"bsonType":"string","enum":["hmv","lmv","lgv","3_axle","5_axle","mcwg","6_axle","2_axle","4_axle","heavy_vehicle"],"description":"Vehicleclassificationtype"},"vehicle_type":{"bsonType":"string","enum":["sedan","suv","micro","hatchback","wagon","pick_up","convertible"],"description":"Typeofvehicle"},"special_type":{"bsonType":"string","enum":["army_vehicle","ambulance","graminseva_4wheeler","graminseva_3wheeler","campervan"],"description":"Specialvehicletype"}}},"label":{"bsonType":"string","enum":["bus","car","truck","motorbike","bicycle","e_rikshaw","cycle_rikshaw","tractor","cement_mixer","mini_truck","mini_bus","mini_van","van"],"description":"Vehicletypewhattypeofvehicleisdetected"},"score":{"bsonType":"number","description":"Confidencescoreforthedetection"},"match_id":{"bsonType":"string","description":"MatchIDforpersonidentification"},"severity":{"bsonType":"string"},"subclass":{"bsonType":"string","description":"Subclassforthedetectedobject"}}}},"c_timestamp":{"bsonType":"date","description":"Timestampoftheevent"}}}}}}}}],"version":1}"""
# from pymongo import MongoClient
# MongoDB connection URI
MONGO_URI  = "mongodb://admin:password@platform-db-0.platform-db.userland/cctv_db"  # Replace with your MongoDB URI
DB_NAME = "cctv_db"  # Your database name
# try: 
#     client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=500)
#     def get_data_from_mongo(db_name, collection_name):
#         db = client.get_database(db_name)
#         collection = db[collection_name]
#         return collection
#     cam_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='camera')
#     Camera_list=[] #str ( cam_collection)
#     for cam in cam_collection.find():
#         Camera_list.append(cam['label'])
#     Camera_list =str(Camera_list)

#     cam_group_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='cameragroup')
#     cam_group_collection_list = []
#     for cam in cam_group_collection.find():
#         cam_group_collection_list = cam['camgroupname']
#     cam_group_collection_list=str(cam_group_collection_list)

#     site_list=[]
#     site_collection = get_data_from_mongo(db_name=DB_NAME, collection_name='sites')
#     for site in site_collection.find():
#         site_list.append(  site["name"])
#     site_list=str(site_list)
#     main_message_part_1 += f"""THE LIST OF ALL POSSIBLE CAMERAS IS {Camera_list}. THE LIST OF ALL POSSIBLE CAMERA GROUPS IS {cam_group_collection}. THE LIST OF ALL POSSIBLE SITES IS {site_list} .
#     The following are examples of user queries and the desired MongoDB query output. Pay close attention to how attributes, dates, task IDs, and other conditions are translated.
#     --- EXAMPLES START ---
#     """
# except:

main_message_part_1 += f""" The following are examples of user queries and the desired MongoDB query output. Pay close attention to how attributes, dates, task IDs, and other conditions are translated.
    --- EXAMPLES START ---
    """

#print(main_message_part_1)
system_message_obj = {
    "role": "system",
    "content": """You are a MongoDB query parsing assistant. Your task is to convert a natural language query into a structured, line-by-line parsed format suitable for building MongoDB queries.

You will receive:
- schema: <MongoDB schema fields and their descriptions>
- natural_language_query: <A plain English query describing the  intent of user.>
- additional_info: <optional context or constraints>

Your job is to extract the relevant conditions and represent them in the following parsed format:
- Each filter is on a separate line
- Use operators like:
    =      - equality  
    $gt    - greater than  
    $lt    - less than  
    $gte   - greater than or equal to  
    $lte   - less than or equal to  
    $in    - inclusion list (comma-separated values)  
    $regex - regular expression for matching  

Follow the schema strictly. Do not hallucinate field names. Output only the parsed query format with no explanations."""
}
prompt_history = [system_message_obj]

# # --- Example Queries and Answers ---
# q1 = str(prefix + "  Find yash")
# a1 = '{"match_id": "Yash"}'
# q2 = str(prefix + " . was Pravar present today")
# a2 = '{ "match_id": "Pravar", "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
# q3 = str(prefix+ " was Nikhil seen in last 7 days")
# a3 = '{ "match_id": "Nikhil", "c_timestamp": { "$gte": "' + str(formatted_dt_plus_7_ago) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
# q4= prefix + " Find all events from 10 aug to 15 aug"
# a4= '{"c_timestamp": {"$gte": "2025-08-10T00:00:00Z", "$lte": "2025-08-16T00:00:00.000Z"}}'
# q5= prefix + " Find all events of vehicle with number plate GJ10SS1010"
# a5= '{"attribs.ocr_result": "GJ10SS1010"}'
# q6= prefix + " Find all alerts of Rajat from 10 jan 2025 to 12 jan 2025 "
# a6= '{ "match_id": "Rajat", "c_timestamp": {"$gte": "2025-01-10T00:00:00Z", "$lte": "2025-01-13T00:00:00.000Z"} }'
# q7= prefix + " Find all events of person wearing glasses"
# a7= '{"attribs.accessories": "glasses"}'
# q8=prefix + " Find events of yash on 10th sept"
# a8='{"match_id": "Yash", "c_timestamp": {"$gte": "2025-09-10T00:00:00Z", "$lte": "2025-09-11T00:00:00.000Z"}}'
# q9=prefix + " Find events of athul on 1st sept with score greater than 70 percent"
# a9='{"match_id": "Athul", "c_timestamp": {"$gte": "2025-09-01T00:00:00Z", "$lte": "2025-09-02T00:00:00.000Z"}, "score": {"$gt": 0.7}}'
# q10= prefix + " Find vehicle with number plate starting with GJ"
# a10='{"attribs.ocr_result": {"$regex": "^GJ"}}'
# q11= prefix + "  Retrieve all events for vehicles with number plates ending in '1010'."
# a11= '{"attribs.ocr_result": {"$regex": "1010$"}}'
# q12= prefix + " List all alerts of license plate task"
# a12= '{"task_id": "ANPR"}'
# q13= prefix + " find Person Slip Detection results in 'south_fr' camera"
# a13= '{"camera_id": "south_fr" , "task_id": "SLIP_DETECT"} '
# q14= prefix + " Find all events on raj ghat camera"
# a14= '{"camera_id": "Raj Ghat"}'
# q15= prefix + " Find all events on office group"
# a15= '{"camgroup_id": "office"}'
# q16= prefix + " provide alerts when someone wore a vneck and capri"
# a16= '{ "attribs":{ "upper_type": "v_neck","lower_type": "capri" }}'
# q17= prefix + " Find all events of Helmet Violation of today " # This example correctly includes time due to "of today"
# a17= '{ "task_id": "helmet_violation", "c_timestamp": {"$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
# q18=  prefix + " Find alerts of man wearing shirt today "
# a18=  '{ "attribs":{ "upper_type": "shirt", "gender": "male"}, "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '" } }'
# q19=   prefix + " find events of children who wore hat and boots"
# a19=    '{ "attribs":{"age":"child", "accessories": "hat","footwear": "boots" }}'
# q20=   prefix + " find events of kids with a box and wearing long trousers"
# a20=    '{ "attribs":{"age":"child", "carrying": "box","lower_type": "long_trousers" }}'
# q21=   prefix + " give alerts of fat people wearing blue tshirt and sport shoes yesterday"
# a21=    '{ "attribs":{"upper_type": "tshirt","footwear":"sport", "upper_color":"blue" , "body_type":"fat"}, "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"} }'
# q22=  prefix + " find woman wearing hat and wearing black casual shoes"
# a22=   '{ "attribs":{"gender":"female", "accessories": "hat","footwear": "casual", "footwear_color":"black" }}'
# q23= prefix + " find woman"
# a23= '{ "attribs":{"gender":"female"}}'
# q24=   prefix + " find woman wearing glasses and sport shoes today "
# a24=    '{ "attribs":{"gender":"female", "accessories": "glasses","footwear": "sport" } , "c_timestamp": { "$gte": "' + str(formatted_dt_0) + '", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
# q25=  prefix + " give alerts of fat young adult men wearing vest , tight_trousers and sport shoes"
# a25=  '{ "attribs":{ "age":"adult", "upper_type": "vest", "lower_type": "tight_trousers", "footwear":"sport", "gender":"male", "body_type":"fat"}}'
# q26= prefix + " give alerts of normal bald elderly man wearing suit, tight_trousers and casual shoes"
# a26=  '{ "attribs":{ "age":"older_adult", "upper_type": "suit_up", "lower_type": "tight_trousers", "footwear":"casual", "gender":"male", "body_type":"normal", "hair_type": "bald_head" }}'
# q27=prefix + " filter out events of thin woman with long hair wearing sunglasses, skirt and short sleeve"
# a27='{ "attribs":{ "body_type":"thin", "sleeve_type": "short_sleeve", "lower_type": "skirt", "hair_type":"long_hair", "gender":"female", "accessories":"glasses" }}'
# q28= prefix + " Find yesterdays events of Ishaan "
# a28= '{"match_id": "Ishaan", "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"}}'
# q29=prefix + " send alerts of young adult woman with black hair wearing sweater , dress and carrying a pink paper bag"
# a29= '{ "attribs":{ "age":"adult", "upper_type": "sweater", "lower_type": "dress", "carrying":"paper_bag", "carrying_color":"pink", "gender":"female", "hair_color":"black" }}'
# q30= prefix + " Find all Red cars"
# a30= '{ "attribs":{ "vehicle_color": "red", "label":"car" }}'
# q31= prefix + " Find all blue TVS Ambulances "
# a31= '{ "attribs":{ "brand_name":"tvs", "special_type": "ambulance", "vehicle_color":"blue", "label": "ambulance" }}'
# q32= prefix + " Find all Abandoned Objects found from 10th march to 20th march "
# a32= '{ "task_id": "ABANDONED_BAG", "c_timestamp": {"$gte": "2025-03-10T00:00:00Z", "$lte": "2025-03-21T00:00:00.000Z"} }'
# q33=   prefix + " List all alerts of Loitering task"
# a33=   '{"task_id": "dwell"}'
# q34= prefix + " Find all events of a side view person carrying hand bag from 3rd april to today "
# a34= '{"attribs": {"carrying":"hand_bag", "orientation":"side" }, "c_timestamp": {"$gte": "2025-04-03T00:00:00Z", "$lte": "' + str(formatted_dt_plus_one_0) + '"} }'
# q35= prefix + " Find all events of person calling while wearing short sleeve from jan 10 to yesterday "
# a35= '{"attribs": {"actions":"calling", "sleeve_type":"short_sleeve" }, "c_timestamp": {"$gte": "2025-01-10T00:00:00Z", "$lte": "' + str(formatted_dt_0) + '"} }'
# q36 = prefix + "find men alerts from yesterday"
# a36 = '{ "attribs":{ "gender":"male"}, "c_timestamp": {"$gte": "' + str(formatted_dt_minus_one_0) +  '" , "$lte": "' + str(formatted_dt_0) + '"}}'
# q37= prefix + " Find  mini bus that are khakhi and 3 axle "
# a37= '{ "attribs":{ "vehicle_i_type":"3_axle", "vehicle_color": "khakhi", "label":"mini_bus" }}'
# q38= prefix + " Find all motorbikes that are  mcwg by kia "
# a38= '{ "attribs":{ "vehicle_i_type":"mcwg", "brand_name": "kia", "label":"motorbike" }}'
# q39= prefix + " Find all white cars"
# a39= '{ "attribs":{"vehicle_color": "white", "label":"car" }}'
# q40= prefix + " Find all ambulances"
# a40= '{ "attribs":{ "special_type": "ambulance", "label": "ambulance"} }'
# q41= prefix + " Find all alerts of collapsed person"
# a41= '{ "task_id": "SLIP_DETECT" }'
# q42= prefix + " Find all vehicles with speed more than 20"
# a42= '{"attribs.speed": {"$gte": 20 } }'
# q43 = prefix + "find all  plates which are one row"
# a43 = '{ "attribs.plate_layout":"one_row" }'
# q44= prefix + " give all alerts of violation" # General violation query
# a44= '{"attribs.violation":"true" }' # No time filter unless specified
# q45= prefix + " give all alerts of violation of two row number plates"
# a45= '{"attribs": {"violation":"true", "plate_layout":"two_row"} }'
# q46 = prefix + "find all Non Commercial Plates "
# a46 = '{ "attribs.registration_type": "non_commercial_plate" }'
# q47 = prefix + "find all rlvd alerts " # Red light violation
# a47 = '{ "task_id": "red_light_violation" }' # Assuming general RLVD alerts, not specific to a 'true' attribute here unless query implies it
#                                                        # And no time filter unless specified.
# q48= prefix + " Find all LMVs that are black and made  by honda "
# a48= '{ "attribs":{ "vehicle_i_type":"lmv", "brand_name": "honda", "vehicle_color":"black" }}'
# q49= prefix + " Find vehicle with number plate containing L1"
# a49='{"attribs.ocr_result": {"$regex": "L1"}}'
# q50= prefix + " Find vehicle with number plate starting with JH and ending with 1"
# a50='{"attribs.ocr_result": {"$regex": "^JH.*1$"}}'
# q51= prefix + " Find blue Maruti cars having 223 in their license plate "
# a51='{"attribs":{"ocr_result": {"$regex": "L1"},"vehicle_color":"blue",  "brand_name": "maruti_suzuki"}}'

# examples_string = ""
# examples_data = [
#     (q1, a1), (q2, a2), (q3, a3), (q4, a4), (q5, a5), (q6, a6), (q7, a7), (q8, a8), (q9, a9), (q10, a10),
#     (q11, a11), (q12, a12), (q13, a13), (q14, a14), (q15, a15), (q16, a16), (q17, a17), (q18, a18), (q19, a19), (q20, a20),
#     (q21, a21), (q22, a22), (q23, a23), (q24, a24), (q25, a25), (q26, a26), (q27, a27), (q28, a28), (q29, a29), (q30, a30),
#     (q31, a31), (q32, a32), (q33, a33), (q34, a34), (q35, a35), (q36, a36), (q37, a37), (q38, a38), (q39, a39), (q40, a40),
#     (q41, a41), (q42, a42), (q43, a43), (q44, a44), (q45, a45), (q46, a46), (q47, a47), (q48, a48),  (q49, a49),(q50,a50)
# ]
# for q_text, a_text in examples_data:
#     examples_string += f"Query : {q_text} assistant : {a_text} , "
# if examples_string.endswith(" , "):
#     examples_string = examples_string[:-3]

trailing_instructions_content = ". --- EXAMPLES END --- \nIMPORTANT: Your final output must be ONLY the MongoDB query in valid JSON format. No other text, explanations, or markdown are permitted."
# full_initial_prompt_content = main_message_part_1 + examples_string + trailing_instructions_content
# prompt_history.append({"role": "user", "content": full_initial_prompt_content})


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
    st=time.time()
    print(f"Request received for query: {request.query}")
    results_ret = await get_results_async(request.query)
    examples_ret = "\n".join(
        f"- {item['doc']}" 
        for item in results_ret)
    #print(examples_ret)
    full_initial_prompt_content = main_message_part_1 + examples_ret+trailing_instructions_content
    prompt_history.append({"role": "user", "content": full_initial_prompt_content})
    print("Time taken to prepare prompt:-------", time.time() - st)
    text = request.query.strip()
    text= text.replace("search","find")
    text= text.replace("show","find")
    # text= text.replace("vides","VIDES")
    text= text.replace("look","find")
    text= text.replace("give","find")
    text= text.replace("return","find")
    
    current_prompt_messages = list(prompt_history)

    if not text.startswith("desc"):
        print("nondesc")
        check_and_reset_dict()
        last_updated = datetime.datetime.today().date()

        if text in listdone:
            print("cached  ",listdone[text])
            return  {"query": listdone[text]}
        # print(f"Processing standard query: {text}")
        current_dt = datetime.datetime.now()
        current_formatted_dt = current_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        user_query_with_time = f"The current date and time is {current_formatted_dt}. Write the correct JSON query for and remember to STRICTLY use attribs whenever ATTRIBUTES OF VEHICLE OR PERSON and DO NOT add c_timestamp unless date/time is mentioned in the following text. natural_language_query: {text} parsed_mongo_query:"
        print(user_query_with_time)
        current_prompt_messages.append({"role": "user", "content": user_query_with_time})

        global cache_value
        cache_value = True
        # if(cache_value):
        #     print ("@@@@@@@@@@@@@@@")
        payload = {
                "slot_id": 0, "temperature": 0.0, "n_keep": -1, "top-k":1,
            "cache_prompt": cache_value, "messages": current_prompt_messages,
            "chat_template_kwargs": {"enable_thinking": "false"},"top_p": 0.0
        }
        #print("Payload for LLM request:", payload)
        headers = {'Content-Type': 'application/json'}
        print("Sending request to LLM for standard query...")
        try:
            r = requests.post("http://127.0.0.1:8080/v1/chat/completions", data=json.dumps(payload), headers=headers, timeout=30)
            print("LLM response received in time",time.time() - st)
            r.raise_for_status()
            response_json = r.json()
            print("response_json--",response_json)
            raw_llm_output = response_json["choices"][0]["message"]["content"]
            json_content = raw_llm_output.replace("```json\n", "").replace("\n```", "").replace("```", "").replace("</think>", "").replace("<think>", "").replace("vehicle_itype","vehicle_i_type").strip()
            print(f"LLM Raw Output--: {json_content}")
            # json_content="""{
            #                     "task_id": "wrong_way",
            #                     "camera_id": "office_entry",
            #                     "ocr_result": "$26",
            #                     "upper_color":"hatchback'
            #                 }"""
            dict_response=json.loads(json_content.replace("'",'"'))
           
            #reconstuct the query
            #json_content = 
            # expanded_json_content = json_content.replace("match_id", "response.event.blobs.match_id").replace("task_id", "identifier.task_id").replace("attribs", "response.event.blobs.attribs").replace("c_timestamp", "response.event.c_timestamp").replace("camera_id", "identifier.camera_id").replace("camgroup_id", "identifier.camgroup_id").strip()
            # parsed_json_obj = json.loads(json_content)
            # list_parsed_json_obj = [parsed_json_obj]

            # parsed_json_obj=  remove_string_null_values(parsed_json_obj)
            # print(f"Parsed JSON Object: {parsed_json_obj}")
            attribs = extract_attribs_from_llm_output(dict_response, schema_mapping)
            for key in attribs.keys():
                if key in dict_response:
                    del dict_response[key]
            if attribs:
    # Create a list of keys to avoid modifying dict during iteration
                keys_to_process = list(attribs.keys())
    
                for key in keys_to_process:
                    value = attribs[key]
                    print(f"{key}: {value}")
                    res = build_mongodb_query(str(value), str(key))
                    if res['query']:
                        print("check1 done")
                        del attribs[key]
                        for fkey, fval in res['query'].items():
                            attribs[fkey] = fval
                            print(fkey,fval)
                    else:
                         valid = False
                
    #         # validated_json_obj = validate_and_correct_attributes(parsed_json_obj)
    #         # validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.vehicle_color","vehicle_color")
    #         # validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.upper_color","upper_color")
    #         # validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.lower_color","lower_color")
    #         # validated_json_obj  = replace_in_dict_keys_and_values(validated_json_obj, "attribs.footwear_color","footwear_color")
    #         final_query_str = json.dumps(parsed_json_obj)

            print("check 1 done by", time.time() - st)
            for key, value in attribs.items():
                  dict_response[key] = value

            reconstructed_dict= convert_simple_to_mongo_query(dict_response,schema_mapping=schema_mapping)
            reconstructed_dict= add_person_to_mongo_query(reconstructed_dict,request.query)
            reconstructed_query =construct_mongo_query_string(reconstructed_dict)
            print("--recons--",reconstructed_query)
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
            final_query_str = str(reconstructed_query)
            print(f"Final MongoDB Query String: {final_query_str}")
            validator = MongoQueryValidator()
            result_json =validator.validate_and_filter_query(request.query,reconstructed_dict)
            print("check2 done")
            print(result_json)
            print(f"---Query processing completed in {time.time() - st:.2f} seconds---")
            listdone[text] = str(reconstructed_query)
            return {"query": str(reconstructed_query)}
        except json.JSONDecodeError as e:
           print(f"Failed to parse LLM JSON output: {e}. Output was: {json_content}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6769)

