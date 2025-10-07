def validate_and_map_attribute(predicted_value, predicted_field=None):
    """
    Validates if a predicted value exists in the attribute dictionaries
    and returns the corresponding MongoDB key path. Includes field validation
    and cross-field correction when predicted_field is wrong for the given value.
    
    Args:
        predicted_value (str): The value predicted by the LLM
        predicted_field (str, optional): The field name predicted by the LLM
    
    Returns:
        dict: Contains validation result, mapped key, attribute type, category, field validation info
    """
    
    personattribute = {
        "footwear_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
        "carrying_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
        "lower_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
        "upper_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
        "gender": ["female", "male"],
        "age": ["child", "adult", "older_adult"],
        "body_type": ["fat", "normal", "thin"],
        "hair_type": ["bald_head", "long_hair", "short_hair"],
        "hair_color": ["black", "blue", "brown", "green", "grey", "orange", "pink", "purple", "red", "white", "yellow"],
        "accessories": ["glasses", "muffler", "hat", "muffler", "nothing", "headphone", "hair_band", "kerchief"],
        "sleeve_type": ["short_sleeve", "long_sleeve"],
        "orientation": ["front", "side", "back"],
        "actions": ["calling", "talking", "gathering", "holding", "pushing", "pulling", "carry_arm", "carry_hand"],
        "upper_type": ["stride", "splice", "casual", "formal", "jacket", "logo", "plaid", "thin_stripes", "tshirt", "other", "v_neck", "suit", "thick_stripes", "shirt", "sweater", "vest", "cotton", "suit_up", "tight"],
        "footwear": ["leather", "sport", "boots", "cloth", "casual", "sandals", "boots", "stocking", "leather_shoes", "shoes", "sneaker"],
        "carrying": ["hand_bag", "shoulder_bag", "hold_objects_in_front", "backpack", "messenger_bag", "nothing", "plastic_bags", "baby_buggy", "shopping_trolley", "umbrella", "folder", "luggage_case", "suitcase", "box", "plastic_bag", "paper_bag", "hand_trunk", "other"],
        "lower_type": ["stripe", "pattern", "long_coat", "trousers", "shorts", "skirt_and_dress", "boots", "long_trousers", "skirt", "short_skirt", "dress", "jeans", "tight_trousers", "capri", "hot_pants", "long_skirt", "plaid", "thin_stripes", "suits", "casual", "formal", "jeans", "shorts", "trousers"],
        "erratic_crowd":["yes","no"],
        "violation":["yes","no"],
        "stop_line_violation":["yes","no"],
        "red_light_violation":["yes","no"]
    }
    
    vehicleattribute = {
        "brand_name": ["tvs", "maruti_suzuki", "eicher", "ashok_leyland", "mercedes_benz", "royal_enfield", "chevrolet", "fiat", "jaguar", "audi", "toyota", "sml", "bajaj", "jbm", "bharat_benz", "hero_motor", "volvo", "nissan", "renault", "volkswagen", "mazda", "hero_honda", "hyundai", "mg", "skoda", "land_rover", "yamaha", "kia", "mahindra", "mitsubishi", "ford", "jeep", "tata_motors", "honda", "bmw", "coupe", "force"],
        "vehicle_color": ["khakhi", "silver", "yellow", "pink", "purple", "green", "blue", "brown", "maroon", "red", "orange", "violet", "white", "black", "grey"],
        "orientation": ["front", "back", "side"],
        "vehicle_label": ["bus", "car", "truck", "motorbike", "bicycle", "e_rikshaw", "cycle_rikshaw", "tractor", "cement_mixer", "mini_truck", "mini_bus", "mini_van", "van"],
        "vehicle_itype": ["hmv", "lmv", "lgv", "3_axle", "5_axle", "mcwg", "6_axle", "2_axle", "4_axle", "heavy_vehicle"],
        "vehicle_type": ["sedan", "suv", "micro", "hatchback", "wagon", "pick_up", "convertible"],
        "special_type": ["army_vehicle", "ambulance", "graminseva_4wheeler", "graminseva_3wheeler", "campervan"],
        "plate_layout":["one_raw", "two_raw"],
        "registration_type": ["commercial", "non-commercial"],


    }
    
    # Combine all attributes for field validation
    all_attributes = {**personattribute, **vehicleattribute}
    
    # Normalize the predicted value for case-insensitive matching
    predicted_value_lower = predicted_value.lower().strip()
    
    def find_correct_field_for_value(value_lower):
        """
        Find which field(s) the value actually belongs to
        Returns: list of (field_name, category, matched_values, match_type)
        """
        matches = []
        
        # Check person attributes
        for attr_key, attr_values in personattribute.items():
            # Check for exact matches
            exact_matches = [v for v in attr_values if v.lower() == value_lower]
            if exact_matches:
                matches.append((attr_key, "person", exact_matches, "exact"))
                continue
            
        
        # Check vehicle attributes
        for attr_key, attr_values in vehicleattribute.items():
            # Check for exact matches
            exact_matches = [v for v in attr_values if v.lower() == value_lower]
            if exact_matches:
                matches.append((attr_key, "vehicle", exact_matches, "exact"))
              

        for attr_key, attr_values in vehicleattribute.items():
            # Check for partial matches
            partial_matches = []
            for attr_value in attr_values:
                if (value_lower in attr_value.lower() or 
                    attr_value.lower() in value_lower):
                    partial_matches.append(attr_value)
            
            if partial_matches:
                matches.append((attr_key, "vehicle", partial_matches, "partial"))

        for attr_key, attr_values in personattribute.items():
            # Check for partial matches
            partial_matches = []
            for attr_value in attr_values:
                if (value_lower in attr_value.lower() or 
                    attr_value.lower() in value_lower):
                    partial_matches.append(attr_value)
            
            if partial_matches:
                matches.append((attr_key, "person", partial_matches, "partial"))

        
        return matches
    
    def normalize_field_name(field_name):
        """Normalize field name for comparison"""
        if not field_name:
            return ""
        return field_name.lower().strip().replace(" ", "_")
    
    def find_similar_field_names(field_name):
        """Find similar field names for suggestions"""
        if not field_name:
            return []
        
        field_lower = normalize_field_name(field_name)
        suggestions = []
        
        for attr_key in all_attributes.keys():
            attr_lower = attr_key.lower()
            # Check for partial matches
            if (field_lower in attr_lower or 
                attr_lower in field_lower or
                any(part in attr_lower for part in field_lower.split('_'))):
                suggestions.append(attr_key)
        
        return suggestions
    
    def validate_exact_value_in_specific_field(value_lower, field_name, attributes, category):
        """Validate if value exists in a specific field"""
        if field_name not in attributes:
            return None
            
        attr_values = attributes[field_name]
        
        # Check for exact match first
        exact_matches = [v for v in attr_values if v.lower() == value_lower]
        if exact_matches:
            return {
                "is_valid": True,
                "mongodb_key": f"{field_name}",
                "category": category,
                "attribute_name": field_name,
                "matched_values": exact_matches,
                "input_value": predicted_value,
                "match_type": "exact",
                "valid_values": attr_values
            }
        
        return None
    
    def validate_partial_value_in_specific_field(value_lower, field_name, attributes, category):
        # Check for partial matches
        if field_name not in attributes:
            return None
            
        attr_values = attributes[field_name]

        partial_matches = []
        for attr_value in attr_values:
            if (value_lower in attr_value.lower() or 
                attr_value.lower() in value_lower):
                partial_matches.append(attr_value)
        
        if partial_matches:
            return {
                "is_valid": True,
                "mongodb_key": f"{field_name}",
                "category": category,
                "attribute_name": field_name,
                "matched_values": partial_matches,
                "input_value": predicted_value,
                "match_type": "partial",
                "valid_values": attr_values
            }
        return None
    
    # Main logic starts here
    if predicted_field:
        # Normalize predicted field
        normalized_field = normalize_field_name(predicted_field)
        
        # Find exact field match
        exact_field_match = None
        for attr_key in all_attributes.keys():
            if normalize_field_name(attr_key) == normalized_field:
                exact_field_match = attr_key
                break
        
        # If exact field match found, validate value in that field
        if exact_field_match:
            category = "person" if exact_field_match in personattribute else "vehicle"
            attributes = personattribute if category == "person" else vehicleattribute
            
            field_validation_result = validate_exact_value_in_specific_field(
                predicted_value_lower, exact_field_match, attributes, category
            )
            # print("Field validation result---:", field_validation_result)
            if field_validation_result:
                # print(f"Exact match found in field '{exact_field_match}' for value '{predicted_value}'")
                # Value found in the predicted field - field is correct
                field_validation_result["field_validation"] = {
                    "field_correct": True,
                    "predicted_field": predicted_field,
                    "corrected_field": exact_field_match
                    # "field_match_type": "exact"
                }
                return field_validation_result
            else:
                # Field exists but value not found in it
                # Check if value exists in other fields
                correct_fields = find_correct_field_for_value(predicted_value_lower)
                # print("Correct fields found---:", correct_fields)
                if correct_fields:
                    # Value found in different field(s)
                    best_match = correct_fields[0]  # Take first match (prioritize exact over partial)
                    field_name, category, matched_values, match_type = best_match
                    
                    return {
                        "is_valid": True,
                        "mongodb_key": f"{field_name}",
                        "category": category,
                        "attribute_name": field_name,
                        "matched_values": matched_values,
                        "input_value": predicted_value,
                        "match_type": match_type,
                        "valid_values": all_attributes[field_name],
                        "field_validation": {
                            "field_correct": False,
                            "predicted_field": predicted_field,
                            "corrected_field": field_name,
                            "field_match_type": "cross_field_correction",
                            "reason": f"Value '{predicted_value}' not found in '{predicted_field}' but found in '{field_name}'"
                        }
                    }
                else:
                    # Value not found anywhere
                    return {
                        "is_valid": False,
                        "mongodb_key": None,
                        "category": category,
                        "attribute_name": exact_field_match,
                        "matched_values": [],
                        "input_value": predicted_value,
                        "match_type": None,
                        "valid_values": all_attributes[exact_field_match],
                        "field_validation": {
                            "field_correct": True,
                            "predicted_field": predicted_field,
                            "corrected_field": exact_field_match,
                            "field_match_type": "exact"
                        },
                        "error": f"Value '{predicted_value}' not found in field '{exact_field_match}' or any other field"
                    }
        
        else:
            # Field name not found, try to suggest similar fields
            similar_fields = find_similar_field_names(predicted_field)
            
            # Check if value exists in any field
            correct_fields = find_correct_field_for_value(predicted_value_lower)
            
            if correct_fields:
                # Value found in some field(s), return the best match
                best_match = correct_fields[0]
                field_name, category, matched_values, match_type = best_match
                
                return {
                    "is_valid": True,
                    "mongodb_key": f"{field_name}",
                    "category": category,
                    "attribute_name": field_name,
                    "matched_values": matched_values,
                    "input_value": predicted_value,
                    "match_type": match_type,
                    "valid_values": all_attributes[field_name],
                    "field_validation": {
                        "field_correct": False,
                        "predicted_field": predicted_field,
                        "corrected_field": field_name,
                        "field_match_type": "cross_field_correction",
                        "similar_field_suggestions": similar_fields,
                        "reason": f"Field '{predicted_field}' not found. Value '{predicted_value}' found in '{field_name}'"
                    }
                }
            else:
                # Neither field nor value found
                return {
                    "is_valid": False,
                    "mongodb_key": None,
                    "category": None,
                    "attribute_name": None,
                    "matched_values": [],
                    "input_value": predicted_value,
                    "match_type": None,
                    "field_validation": {
                        "field_correct": False,
                        "predicted_field": predicted_field,
                        "corrected_field": None,
                        "field_match_type": "not_found",
                        "similar_field_suggestions": similar_fields
                    },
                    "error": f"Neither field '{predicted_field}' nor value '{predicted_value}' found in any attribute"
                }
    
    # If no predicted_field provided, use original logic
    correct_fields = find_correct_field_for_value(predicted_value_lower)
    
    if correct_fields:
        # Return the best match (exact matches first, then partial)
        exact_matches = [match for match in correct_fields if match[3] == "exact"]
        best_match = exact_matches[0] if exact_matches else correct_fields[0]
        
        field_name, category, matched_values, match_type = best_match
        
        return {
            "is_valid": True,
            "mongodb_key": f"{field_name}",
            "category": category,
            "attribute_name": field_name,
            "matched_values": matched_values,
            "input_value": predicted_value,
            "match_type": match_type,
            "valid_values": all_attributes[field_name],
            "field_validation": {
                "field_correct": None,
                "predicted_field": predicted_field,
                "corrected_field": field_name,
                "field_match_type": "auto_detected"
            }
        }
    
    # No matches found anywhere
    return {
        "is_valid": False,
        "mongodb_key": None,
        "category": None,
        "attribute_name": None,
        "matched_values": [],
        "input_value": predicted_value,
        "match_type": None,
        "field_validation": {
            "field_correct": False if predicted_field else None,
            "predicted_field": predicted_field,
            "corrected_field": None,
            "field_match_type": "not_found"
        },
        "error": "Value not found in any attribute dictionary"
    }

def build_mongodb_query(predicted_value, predicted_field=None):
    """
    Build a MongoDB query using the validated attribute with cross-field validation support
    """
    do_not_care =["crowd_estimate","crowd_flow_percentage","vehicle_speed_limit","vehicle_speed","ocr_result","occupation",""]
    if predicted_field in do_not_care:
        return {
            "query": {predicted_field: predicted_value}
        }
    result = validate_and_map_attribute(predicted_value, predicted_field)
    
    if result["is_valid"]:
        matched_values = result["matched_values"]
        mongodb_key = result["mongodb_key"]
        
        if len(matched_values) == 1:
            query = {mongodb_key: matched_values[0]}
        else:
            query = {mongodb_key: {"$in": matched_values}}
        
        return {
            "query": query,
            "details": {
                "input": result["input_value"],
                "matched_values": matched_values,
                "match_type": result["match_type"],
                "count": len(matched_values),
                "field_validation": result["field_validation"]
            }
        }
    
    return {
        "query": None,
        "error": result.get("error", "Invalid value"),
        "field_validation": result.get("field_validation", {})
    }

# Test function for cross-field validation
def test_cross_field_validation():
    """Test the cross-field validation and correction functionality"""
    
    test_cases = [
        # # Case: value in wrong field - should correct field
        # ("maruti", "vehicle_type"),      # Should correct to "brand_name"
        # ("sedan", "brand_name"),         # Should correct to "vehicle_type" 
        # ("male", "age"),                 # Should correct to "gender"
        
        # # Case: correct field and value
        # ("maruti", "brand_name"),        # Should be correct (partial match)
        # ("sedan", "vehicle_type"),       # Should be correct
        
        # # Case: field name similar but not exact
        # ("black", "vehicle color"),      # Should correct to "vehicle_color"
        ("hatchback", "upper_type"),        # Should correct to "accessories"
        
        # Case: completely wrong field and value
        # ("wii", "task_id"),      # Should not match anything
        
        # # Case: no field provided
        # ("maruti", None),
        # ("hero", None),
    ]
    
    print("=== Cross-Field Validation and Correction Tests ===")
    for value, field in test_cases:
        result = validate_and_map_attribute(value, field)
        print(f"Input: value='{value}', field='{field}'")
        print(f"Valid: {result['is_valid']}")
        
        if result['is_valid']:
            print(f"MongoDB Key: {result['mongodb_key']}")
            print(f"Matched Values: {result['matched_values']}")
            print(f"Match Type: {result['match_type']}")
        
        field_val = result.get('field_validation', {})
        if field_val:
            print(f"Field Correct: {field_val.get('field_correct')}")
            print(f"Predicted Field: '{field_val.get('predicted_field')}'")
            print(f"Corrected Field: '{field_val.get('corrected_field')}'")
            print(f"Field Match Type: {field_val.get('field_match_type')}")
            
            if field_val.get('reason'):
                print(f"Reason: {field_val.get('reason')}")
            
            if field_val.get('similar_field_suggestions'):
                print(f"Similar Field Suggestions: {field_val.get('similar_field_suggestions')}")
        
        if not result['is_valid']:
            print(f"Error: {result.get('error')}")
        
        print("-" * 80)

        res= build_mongodb_query(value, field)
        if res["query"]:
            print(f"MongoDB Query: {res['query']}")
            print(f"Details: {res['details']}")
        else:
            print(f"Query Error: {res['error']}")
        print("=" * 80)



if __name__ == "__main__":
    test_cross_field_validation()



