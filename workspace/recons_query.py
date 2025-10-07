import json

def build_schema_mapping_from_schema(schema):
    mapping = {}
    
    def traverse_properties(properties, current_path=""):
        for key, value in properties.items():
            full_path = f"{current_path}.{key}" if current_path else key
            
            # Add the mapping for this field
            mapping[key] = full_path
            
            # If this field has nested properties, traverse them
            if isinstance(value, dict) and "properties" in value:
                traverse_properties(value["properties"], full_path)
            # THIS IS THE KEY FIX - Handle array items with properties
            elif isinstance(value, dict) and value.get("bsonType") == "array" and "items" in value:
                items = value["items"]
                if isinstance(items, dict) and "properties" in items:
                    traverse_properties(items["properties"], full_path)
    
    # Start traversal from the document properties
    if "collections" in schema:
        for collection in schema["collections"]:
            if collection["name"] == "events":
                document_properties = collection["document"]["properties"]
                traverse_properties(document_properties)
    
    return mapping


def convert_simple_to_mongo_query(simple_query, schema_mapping):
    """Convert simplified query to full MongoDB field paths"""
    result = {}
    for key, value in simple_query.items():
        if key in schema_mapping:
            full_path = schema_mapping[key]
            result[full_path] = value
        else:
            # If key not found in mapping, keep as is
            result[key] = value
    return result

def construct_mongo_query_string(mapped_query):
    """Construct the MongoDB query string from the mapped full field paths"""
    query_json = json.dumps(mapped_query, indent=2)
    mongo_query_string = f"db.events.find({query_json})"
    return mongo_query_string

# Your schema (as provided)
schema = {
  "collections": [
    {
      "name": "events",
      "document": {
        "bsonType": "object",
        "properties": {

          "identifier": {
            "bsonType": "object",
            "properties": {
              "camgroup_id": {
                "bsonType": "string",
                "description": "Use this to filter events by group - can be any name based on site, location, deployment, custom, or video name"
              },
              "task_id": {
                "bsonType": "string",
                "description": "Map natural language application names to their corresponding short_name values",
                "enum": ["ANPR", "CROWD_EST", "CROWD_COUNT", "FR", "ABANDONED_BAG", "INTRUDER_DETECT", "CAM_TAMPERING", "SLIP_DETECT", "PPE_VOILATION", "wrong_way", "helmet_violation", "triple_riding", "speed_violation", "red_light_violation", "violence_detection", "dwell", "wii", "whh", "qm", "tg", "lane_violation", "seatbelt", "parking_violation", "pat", "vat", "fns"],
                "mappings": [
                  {"application_name": "License Plate Recognition", "task_id_value": "ANPR"},
                  {"application_name": "Crowd Estimation", "task_id_value": "CROWD_EST"},
                  {"application_name": "Crowd Count", "task_id_value": "CROWD_COUNT"},
                  {"application_name": "Facial Recognition", "task_id_value": "FR"},
                  {"application_name": "Abandoned Bag Alert", "task_id_value": "ABANDONED_BAG"},
                  {"application_name": "Intruder Alert", "task_id_value": "INTRUDER_DETECT"},
                  {"application_name": "Camera Tampering", "task_id_value": "CAM_TAMPERING"},
                  {"application_name": "Person Slip Detection", "task_id_value": "SLIP_DETECT"},
                  {"application_name": "PPE Violation", "task_id_value": "PPE_VOILATION"},
                  {"application_name": "Wrong Way", "task_id_value": "wrong_way"},
                  {"application_name": "Helmet Violation", "task_id_value": "helmet_violation"},
                  {"application_name": "Triple Riding", "task_id_value": "triple_riding"},
                  {"application_name": "Speed Violation", "task_id_value": "speed_violation"},
                  {"application_name": "Red Light Violation", "task_id_value": "red_light_violation"},
                  {"application_name": "Violence Detection", "task_id_value": "violence_detection"},
                  {"application_name": "Loitering", "task_id_value": "dwell"},
                  {"application_name": "Woman In Isolation", "task_id_value": "wii"},
                  {"application_name": "Woman Hailing Help", "task_id_value": "whh"},
                  {"application_name": "Queue Management", "task_id_value": "qm"},
                  {"application_name": "Tailgating", "task_id_value": "tg"},
                  {"application_name": "Lane violation", "task_id_value": "lane_violation"},
                  {"application_name": "Seat belt", "task_id_value": "seatbelt"},
                  {"application_name": "Parking violation", "task_id_value": "parking_violation"},
                  {"application_name": "Person Attribute", "task_id_value": "pat"},
                  {"application_name": "Vehicle Attribute", "task_id_value": "vat"},
                  {"application_name": "Fire and Smoke Detection", "task_id_value": "fns"},
                  {"application_name": "VIDES", "task_id_value": "parking_violation"}
                ]
              },
              "camera_id": {
                "bsonType": "string",
                "description": "Individual camera identifier - can be any name based on site, location, deployment, custom, or video name"
              }
            }
          },
          "response": {
            "bsonType": "object",
            "properties": {
              "event": {
                "bsonType": "object",
                "properties": {
                  "event_priority": {
                      "bsonType": "string",
                       "enum": ["p1", "p2", "p3", "p4"],
                       "description": "Priority level of the event p1 being highest and p4 lowest"
                        },
                    "event_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the event"
                    },
                  "c_timestamp": {
                    "bsonType": "date",
                    "description": "Timestamp of the event in format '2025-06-23T00:00:00Z'"
                  },
                  "blobs": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "object",
                      "properties": {
                        "url": {
                          "bsonType": "string"
                        },
                        "blob_priority": {
                          "bsonType": "string",
                          "enum": ["p1", "p2", "p3", "p4"],
                          "description": "Priority level of the blob"
                        },
                        "attribs": {
                          "bsonType": "object",
                          "description": "Attributes for person or vehicle detection",
                          "properties": {
                            "crowd_estimate": {
                              "bsonType": "int",
                              "description": "Integer number generated by crowd estimation app"
                            },
                            "erratic_crowd": {
                              "bsonType": "string",
                              "enum": ["yes", "no"],
                              "description": "Whether crowd behavior is erratic"
                            },
                            "crowd_flow_percentage": {
                              "bsonType": "number",
                              "minimum": 0,
                              "maximum": 100,
                              "description": "Crowd flow percentage"
                            },
                            "special_type": {
                              "bsonType": "string",
                              "enum": ["army_vehicle", "ambulance", "graminseva_4wheeler", "graminseva_3wheeler", "campervan"],
                              "description": "Special vehicle type"
                            },
                            "brand_name": {
                              "bsonType": "string",
                              "enum": ["tvs", "maruti_suzuki", "eicher", "ashok_leyland", "mercedes_benz", "royal_enfield", "chevrolet", "fiat", "jaguar", "audi", "toyota", "sml", "bajaj", "jbm", "bharat_benz", "hero_motor", "volvo", "nissan", "renault", "volkswagen", "mazda", "hero_honda", "hyundai", "mg", "skoda", "land_rover", "yamaha", "kia", "mahindra", "mitsubishi", "ford", "jeep", "tata_motors", "honda", "bmw", "coupe", "force"],
                              "description": "Brand name of the vehicle"
                            },
                            "vehicle_color": {
                              "bsonType": "string",
                              "enum": ["khakhi", "silver", "yellow", "pink", "purple", "green", "blue", "brown", "maroon", "red", "orange", "violet", "white", "black", "grey"],
                              "description": "Color of the vehicle"
                            },
                            "vehicle_type": {
                              "bsonType": "string",
                              "enum": ["sedan", "suv", "micro", "hatchback", "wagon", "pick_up", "convertible"],
                              "description": "Type of vehicle"
                            },
                            "vehicle_itype": {
                              "bsonType": "string",
                              "enum": ["hmv", "lmv", "lgv", "3_axle", "5_axle", "mcwg", "6_axle", "2_axle", "4_axle", "heavy_vehicle"],
                              "description": "Vehicle classification type"
                            },
                            "vehicle_speed": {
                              "bsonType": "number",
                              "description": "Speed of the vehicle"
                            },
                            "vehicle_speed_limit": {
                              "bsonType": "number",
                              "description": "Speed limit for the vehicle"
                            },
                            "vehicle_label": {
                              "bsonType": "string",
                              "enum": ["bus", "car", "truck", "motorbike", "bicycle", "e_rikshaw", "cycle_rikshaw", "tractor", "cement_mixer", "mini_truck", "mini_bus", "mini_van", "van"],
                              "description": "Vehicle label - type of vehicle detected"
                            },
                            "plate_layout": {
                              "bsonType": "string",
                              "enum": ["one_raw", "two_raw"],
                              "description": "Layout of vehicle license plate"
                            },
                            "ocr_result": {
                              "bsonType": "string",
                              "description": "OCR result from license/number plate of vehicle use this for regex number plate query"
                            },
                            "registration_type": {
                              "bsonType": "string",
                              "enum": ["commercial", "non-commercial"],
                              "description": "Vehicle registration type"
                            },
                            "actions": {
                              "bsonType": "string",
                              "enum": ["calling", "talking", "gathering", "holding", "pushing", "pulling", "carry_arm", "carry_hand"],
                              "description": "Actions being performed by the person"
                            },
                            "age": {
                              "bsonType": "string",
                              "enum": ["child", "adult", "older_adult"],
                              "description": "Age category of the person"
                            },
                            "body_type": {
                              "bsonType": "string",
                              "enum": ["fat", "normal", "thin"],
                              "description": "Body type of the person"
                            },
                            "carrying": {
                              "bsonType": "string",
                              "enum": ["hand_bag", "shoulder_bag", "hold_objects_in_front", "backpack", "messenger_bag", "nothing", "plastic_bags", "baby_buggy", "shopping_trolley", "umbrella", "folder", "luggage_case", "suitcase", "box", "plastic_bag", "paper_bag", "hand_trunk", "other"],
                              "description": "Items being carried by the person"
                            },
                            "footwear": {
                              "bsonType": "string",
                              "enum": ["leather", "sport", "boots", "cloth", "casual", "sandals", "stocking", "leather_shoes", "shoes", "sneaker"],
                              "description": "Type of footwear"
                            },
                            "gender": {
                              "bsonType": "string",
                              "enum": ["female", "male"],
                              "description": "Gender of the person"
                            },
                            "hair_color": {
                              "bsonType": "string",
                              "enum": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
                              "description": "Hair color of the person"
                            },
                            "hair_type": {
                              "bsonType": "string",
                              "enum": ["bald_head", "long_hair", "short_hair"],
                              "description": "Hair type of the person"
                            },
                            "lower_type": {
                              "bsonType": "string",
                              "enum": ["stripe", "pattern", "long_coat", "trousers", "shorts", "skirt_and_dress", "boots", "long_trousers", "skirt", "short_skirt", "dress", "jeans", "tight_trousers", "capri", "hot_pants", "long_skirt", "plaid", "thin_stripes", "suits", "casual", "formal"],
                              "description": "Type of lower body clothing"
                            },
                            "upper_type": {
                              "bsonType": "string",
                              "enum": ["stride", "splice", "casual", "formal", "jacket", "logo", "plaid", "thin_stripes", "tshirt", "other", "v_neck", "suit", "thick_stripes", "shirt", "sweater", "vest", "cotton", "suit_up", "tight"],
                              "description": "Type of upper body clothing"
                            },
                            "upper_color": {
                              "bsonType": "string",
                              "enum": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
                              "description": "Color of upper body clothing"
                            },
                            "lower_color": {
                              "bsonType": "string",
                              "enum": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
                              "description": "Color of lower body clothing"
                            },
                            "occupation": {
                              "bsonType": "string",
                              "description": "Occupation of the person"
                            },
                            "sleeve_type": {
                              "bsonType": "string",
                              "enum": ["short_sleeve", "long_sleeve"],
                              "description": "Type of sleeves on upper clothing"
                            },
                            "carrying_color": {
                              "bsonType": "string",
                              "enum": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
                              "description": "Color of items being carried"
                            },
                            "footwear_color": {
                              "bsonType": "string",
                              "enum": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
                              "description": "Color of footwear for person"
                            },
                            "accessories": {
                              "bsonType": "string",
                              "enum": ["glasses", "muffler", "hat", "nothing", "headphone", "hair_band", "kerchief"],
                              "description": "Accessories worn by the person"
                            },
                            "orientation": {
                              "bsonType": "string",
                              "enum": ["front", "back", "side"],
                              "description": "Orientation of person or vehicle"
                            },
                            "violation": {
                              "bsonType": "string",
                              "enum": ["yes", "no"],
                              "description": "Whether a violation occurred"
                            },
                            "red_light_violation": {
                              "bsonType": "string",
                              "enum": ["yes", "no"],
                              "description": "Whether a red light violation occurred"
                            },
                            "stop_line_violation": {
                              "bsonType": "string",
                              "enum": ["yes", "no"],
                              "description": "Whether a stop line violation occurred"
                            }
                          }
                        },
                        "score": {
                          "bsonType": "number",
                          "minimum": 0,
                          "maximum": 1,
                          "description": "Confidence score for the detection"
                        },
                        "match_id": {
                          "bsonType": "string",
                          "description": "Match ID for person identification"
                        }
                      }
                    }
                  }
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


# Pre-built mapping for common fields (based on your schema)
schema_mapping = {
    # Root level fields
    'identifier': 'identifier',
    'response': 'response',
    
    # Identifier fields
    'camgroup_id': 'identifier.camgroup_id',
    'task_id': 'identifier.task_id',
    'camera_id': 'identifier.camera_id',
    
    # Response.event fields
    'event': 'response.event',
    'event_priority': 'response.event.event_priority',
    'event_id': 'response.event.event_id',
    'c_timestamp': 'response.event.c_timestamp',
    
    # Blob level fields
    'blobs': 'response.event.blobs',
    'url': 'response.event.blobs.url',
    'blob_priority': 'response.event.blobs.blob_priority',
    'score': 'response.event.blobs.score',
    'match_id': 'response.event.blobs.match_id',
    
    # Attributes container
    'attribs': 'response.event.blobs.attribs',
    
    # All attribute fields
    'crowd_estimate': 'response.event.blobs.attribs.crowd_estimate',
    'erratic_crowd': 'response.event.blobs.attribs.erratic_crowd',
    'crowd_flow_percentage': 'response.event.blobs.attribs.crowd_flow_percentage',
    'special_type': 'response.event.blobs.attribs.special_type',
    'brand_name': 'response.event.blobs.attribs.brand_name',
    'vehicle_color': 'response.event.blobs.attribs.vehicle_color',
    'vehicle_type': 'response.event.blobs.attribs.vehicle_type',
    'vehicle_itype': 'response.event.blobs.attribs.vehicle_itype',
    'vehicle_speed': 'response.event.blobs.attribs.vehicle_speed',
    'vehicle_speed_limit': 'response.event.blobs.attribs.vehicle_speed_limit',
    'vehicle_label': 'response.event.blobs.attribs.vehicle_label',
    'plate_layout': 'response.event.blobs.attribs.plate_layout',
    'ocr_result': 'response.event.blobs.attribs.ocr_result',
    'registration_type': 'response.event.blobs.attribs.registration_type',
    'actions': 'response.event.blobs.attribs.actions',
    'age': 'response.event.blobs.attribs.age',
    'body_type': 'response.event.blobs.attribs.body_type',
    'carrying': 'response.event.blobs.attribs.carrying',
    'footwear': 'response.event.blobs.attribs.footwear',
    'gender': 'response.event.blobs.attribs.gender',
    'hair_color': 'response.event.blobs.attribs.hair_color',
    'hair_type': 'response.event.blobs.attribs.hair_type',
    'lower_type': 'response.event.blobs.attribs.lower_type',
    'upper_type': 'response.event.blobs.attribs.upper_type',
    'upper_color': 'response.event.blobs.attribs.upper_color',
    'lower_color': 'response.event.blobs.attribs.lower_color',
    'occupation': 'response.event.blobs.attribs.occupation',
    'sleeve_type': 'response.event.blobs.attribs.sleeve_type',
    'carrying_color': 'response.event.blobs.attribs.carrying_color',
    'footwear_color': 'response.event.blobs.attribs.footwear_color',
    'accessories': 'response.event.blobs.attribs.accessories',
    'orientation': 'response.event.blobs.attribs.orientation',
    'violation': 'response.event.blobs.attribs.violation',
    'red_light_violation': 'response.event.blobs.attribs.red_light_violation',
    'stop_line_violation': 'response.event.blobs.attribs.stop_line_violation'
}


# Your example input
simple_query = {
    "task_id": "wrong_way",
    "camera_id": "office_entry",
    "ocr_result": {"$regex": "KA"}
}

# print("--",build_schema_mapping_from_schema(schema=schema))
# Convert to full MongoDB query
# mapped_query = convert_simple_to_mongo_query(simple_query, schema_mapping)
# mongo_query_string = construct_mongo_query_string(mapped_query)

# print(mongo_query_string)
# Example with more fields
complex_query = "{'carrying': 'backpack'}"

# Convert to MongoDB query
mapped_complex = convert_simple_to_mongo_query(json.loads(complex_query.replace("'",'"')), schema_mapping)
complex_mongo_string = construct_mongo_query_string(mapped_complex)

print(complex_mongo_string)

