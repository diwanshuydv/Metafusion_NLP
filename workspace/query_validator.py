import re
import json
from typing import Dict, List, Set, Any, Union

class MongoQueryValidator:
    def __init__(self):
        # Define which fields should be filtered vs preserved
        self.filterable_field_patterns = [
            r'^attribs\.',  # All attributes fields (normalized path)
            r'^identifier\.task_id$',  # Task ID
            r'^label$',  # Vehicle label (can be mentioned in natural language, normalized path)
            r'^response\.event\.blobs\.attribs\.' # Specific for attribs within blobs (full path)
        ]
        
        # Fields that should always be preserved (not filtered)
        self.preserve_field_patterns = [
            r'^identifier\.camgroup_id$',
            r'^identifier\.camera_id$',
            r'^response\.event\.severity$',
            r'^response\.event\.c_timestamp$',
            r'^response\.event\.label$', # Full path for label at event level
            r'^response\.event\.blobs\.url$',
            r'^response\.event\.blobs\.score$',
            r'^response\.event\.blobs\.match_id$',
            r'^response\.event\.blobs\.severity$',
            r'^response\.event\.blobs\.subclass$',
            r'\.url$',  # Any URL field
            r'\.score$',  # Any score field
            r'^identifier\.match_id$',  # Any match_id field
            r'\.severity$',  
            r'\.subclass$',  # Any subclass field
            r'\.c_timestamp$',  # Any timestamp field
            r'^response\.event\.event_priority$', 
            r'^response\.event\.event_id$' 
        ]

        # Task ID mappings
        self.task_mappings = {
            'license plate recognition': 'ANPR',
            'anpr': 'ANPR',
            'number plate recognition': 'ANPR',
            'crowd estimation': 'CROWD_EST',
            'crowd count': 'CROWD_COUNT',
            'facial recognition': 'FR',
            'face recognition': 'FR',
            'abandoned bag alert': 'ABANDONED_BAG',
            'abandoned bag': 'ABANDONED_BAG',
            'abandoned object': 'ABANDONED_BAG',
            'abandoned objects': 'ABANDONED_BAG',
            'intruder alert': 'INTRUDER_DETECT',
            'intruder detection': 'INTRUDER_DETECT',
            'intruder': 'INTRUDER_DETECT',
            'camera tampering': 'CAM_TAMPERING',
            'tampering': 'CAM_TAMPERING',
            'person slip detection': 'SLIP_DETECT',
            'slip detection': 'SLIP_DETECT',
            'ppe violation': 'PPE_VOILATION',
            'ppe': 'PPE_VOILATION',
            'wrong way': 'wrong_way',
            'helmet violation': 'helmet_violation',
            'helmet': 'helmet_violation',
            'triple riding': 'triple_riding',
            'speed violation': 'speed_violation',
            'speeding': 'speed_violation',
            'red light violation': 'red_light_violation',
            'red light': 'red_light_violation',
            'violence detection': 'violence_detection',
            'violence': 'violence_detection',
            'loitering': 'dwell',
            'dwell': 'dwell',
            'woman in isolation': 'wii',
            'woman hailing help': 'whh',
            'queue management': 'qm',
            'queue': 'qm',
            'tailgating': 'tg',
            'lane violation': 'lane_violation',
            'lane': 'lane_violation',
            'seat belt': 'seatbelt',
            'seatbelt': 'seatbelt',
            'parking violation': 'parking_violation',
            'parking': 'parking_violation',
            'person attribute': 'pat',
            'vehicle attribute': 'vat',
            'fire and smoke detection': 'fns',
            'fire detection': 'fns',
            'smoke detection': 'fns',
            'fire': 'fns',
            'smoke': 'fns',
            'vides': 'parking_violation'
        }

        # Enhanced field mappings
        self.field_mappings = {
            # Task-related keywords
            'alerts': 'identifier.task_id',
            'alert': 'identifier.task_id',
            'detection': 'identifier.task_id',
            'violation': 'identifier.task_id',
            'violations': 'identifier.task_id',
            'recognition': 'identifier.task_id',
            
            # Gender mappings
            'male': 'attribs.gender',
            'female': 'attribs.gender',
            'man': 'attribs.gender',
            'woman': 'attribs.gender',
            'boy': 'attribs.gender',
            'girl': 'attribs.gender',
            
            # Clothing mappings
            'jacket': 'attribs.upper_type',
            'shirt': 'attribs.upper_type',
            'sweater': 'attribs.upper_type',
            'vest': 'attribs.upper_type',
            'tshirt': 'attribs.upper_type',
            't-shirt': 'attribs.upper_type',
            'suit': 'attribs.upper_type',
            'formal': 'attribs.upper_type',
            'casual': 'attribs.upper_type',
            
            # Lower clothing
            'trousers': 'attribs.lower_type',
            'jeans': 'attribs.lower_type',
            'shorts': 'attribs.lower_type',
            'skirt': 'attribs.lower_type',
            'dress': 'attribs.lower_type',
            'pants': 'attribs.lower_type',
            
            # Carrying items
            'bag': 'attribs.carrying',
            'backpack': 'attribs.carrying',
            'suitcase': 'attribs.carrying',
            'luggage': 'attribs.carrying',
            'handbag': 'attribs.carrying',
            'briefcase': 'attribs.carrying',
            'umbrella': 'attribs.carrying',
            'folder': 'attribs.carrying',
            
            # Accessories
            'glasses': 'attribs.accessories',
            'sunglasses': 'attribs.accessories',
            'hat': 'attribs.accessories',
            'cap': 'attribs.accessories',
            
            # Footwear
            'sport': 'attribs.footwear',
            'formal': 'attribs.footwear',
            'casual': 'attribs.footwear',
            'boots': 'attribs.footwear',
            'sandals': 'attribs.footwear',
            
            # Colors - These will be handled by smart_color_mapping
            'black': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'white': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'red': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'blue': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'green': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'yellow': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'grey': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'gray': ['attribs.upper_color', 'attribs.lower_color', 'attribs.footwear_color', 'attribs.vehicle_color'],
            'silver': 'attribs.vehicle_color', 
            'maroon': 'attribs.vehicle_color', 
            
            # Age
            'child': 'attribs.age',
            'adult': 'attribs.age',
            'elderly': 'attribs.age',
            'old': 'attribs.age',
            
            # Vehicle Types
            'sedan': 'attribs.vehicle_type',
            'suv': 'attribs.vehicle_type',
            'hatchback': 'attribs.vehicle_type',
            'pickup': 'attribs.vehicle_type',
            'convertible': 'attribs.vehicle_type',
            
            # Vehicle Labels
            'bus': 'label',
            'car': 'label',
            'truck': 'label',
            'motorbike': 'label',
            'motorcycle': 'label',
            'bike': 'label',
            'bicycle': 'label',
            'rickshaw': 'label',
            'tractor': 'label',
            'van': 'label',
            
            # Vehicle Brands
            'tata': 'attribs.brand_name',
            'maruti': 'attribs.brand_name',
            'honda': 'attribs.brand_name',
            'toyota': 'attribs.brand_name',
            'hyundai': 'attribs.brand_name',
            'mahindra': 'attribs.brand_name',
            'bajaj': 'attribs.brand_name',
            'hero': 'attribs.brand_name',
            'yamaha': 'attribs.brand_name',
            'bmw': 'attribs.brand_name',
            'mercedes': 'attribs.brand_name',
            'audi': 'attribs.brand_name',
            'ford': 'attribs.brand_name',
        }
        
        # Schema fields
        self.schema_fields = {
            'identifier.task_id': ['ANPR', 'CROWD_EST', 'CROWD_COUNT', 'FR', 'ABANDONED_BAG', 'INTRUDER_DETECT', 'CAM_TAMPERING', 'SLIP_DETECT', 'PPE_VOILATION', 'wrong_way', 'helmet_violation', 'triple_riding', 'speed_violation', 'red_light_violation', 'violence_detection', 'dwell', 'wii', 'whh', 'qm', 'tg', 'lane_violation', 'seatbelt', 'parking_violation', 'pat', 'vat', 'fns'],
            'attribs.gender': ['male', 'female'],
            'attribs.upper_type': ['jacket', 'shirt', 'sweater', 'vest', 'tshirt', 'suit', 'formal', 'casual', 'stride', 'splice', 'logo', 'plaid', 'thin_stripes', 'other', 'v_neck', 'thick_stripes', 'cotton', 'suit_up', 'tight'],
            'attribs.carrying': ['hand_bag', 'shoulder_bag', 'hold_objects_in_front', 'backpack', 'messenger_bag', 'nothing', 'plastic_bags', 'baby_buggy', 'shopping_trolley', 'umbrella', 'folder', 'luggage_case', 'suitcase', 'box', 'plastic_bag', 'paper_bag', 'hand_trunk', 'other'],
            'attribs.accessories': ['glasses', 'muffler', 'hat', 'nothing', 'headphone', 'hair_band', 'kerchief'],
            'attribs.footwear': ['leather', 'sport', 'boots', 'cloth', 'casual', 'sandals', 'stocking', 'leather_shoes', 'shoes', 'sneaker'],
            'attribs.age': ['child', 'adult', 'older_adult'],
            'attribs.vehicle_color': ['khakhi', 'silver', 'yellow', 'pink', 'purple', 'green', 'blue', 'brown', 'maroon', 'red', 'orange', 'violet', 'white', 'black', 'grey'],
            'attribs.brand_name': ['tvs', 'maruti_suzuki', 'eicher', 'ashok_leyland', 'mercedes_benz', 'royal_enfield', 'chevrolet', 'fiat', 'jaguar', 'audi', 'toyota', 'sml', 'bajaj', 'jbm', 'bharat_benz', 'hero_motor', 'volvo', 'nissan', 'renault', 'volkswagen', 'mazda', 'hero_honda', 'hyundai', 'mg', 'skoda', 'land_rover', 'yamaha', 'kia', 'mahindra', 'mitsubishi', 'ford', 'jeep', 'tata_motors', 'honda', 'bmw', 'coupe', 'force'],
            'label': ['bus', 'car', 'truck', 'motorbike', 'bicycle', 'e_rikshaw', 'cycle_rikshaw', 'tractor', 'cement_mixer', 'mini_truck', 'mini_bus', 'mini_van', 'van'],
            'attribs.lower_type': ['stripe', 'pattern', 'long_coat', 'trousers', 'shorts', 'skirt_and_dress', 'boots', 'long_trousers', 'skirt', 'short_skirt', 'dress', 'jeans', 'tight_trousers', 'capri', 'hot_pants', 'long_skirt', 'plaid', 'thin_stripes', 'suits', 'casual', 'formal'],
            'attribs.upper_color': ['black', 'blue', 'brown', 'green', 'grey', 'orange', 'pink', 'purple', 'red', 'white', 'yellow'],
            'attribs.lower_color': ['black', 'blue', 'brown', 'green', 'grey', 'orange', 'pink', 'purple', 'red', 'white', 'yellow'],
            'attribs.footwear_color': ['black', 'blue', 'brown', 'green', 'grey', 'orange', 'pink', 'purple', 'red', 'white', 'yellow'],
            'attribs.vehicle_type': ['sedan', 'suv', 'micro', 'hatchback', 'wagon', 'pick_up', 'convertible']
        }

        # Brand mappings
        self.brand_mappings = {
            'tata': 'tata_motors',
            'maruti': 'maruti_suzuki',
            'hero': 'hero_motor',
            'mercedes': 'mercedes_benz',
            'honda': 'honda', 
            'toyota': 'toyota', 
            'hyundai': 'hyundai', 
            'mahindra': 'mahindra', 
            'bajaj': 'bajaj', 
            'yamaha': 'yamaha', 
            'bmw': 'bmw', 
            'audi': 'audi', 
            'ford': 'ford', 
        }

    def is_filterable_field(self, field_path: str) -> bool:
        """Check if a field should be filtered based on natural language."""
        # Check both the full path and the normalized path (for attribs/label)
        for pattern in self.filterable_field_patterns:
            if re.match(pattern, field_path): # Check full path first
                return True
            # If the field_path starts with response.event.blobs. and the pattern is for normalized paths (like 'attribs.')
            if field_path.startswith("response.event.blobs.") and re.match(pattern, self.normalize_field_path(field_path)):
                return True
        return False

    def is_preserve_field(self, field_path: str) -> bool:
        """Check if a field should be preserved regardless of natural language."""
        for pattern in self.preserve_field_patterns:
            if re.match(pattern, field_path):
                return True
        return False

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        return text.lower().replace('_', ' ').replace('-', ' ').strip()

    def detect_task_mentions(self, natural_query: str) -> Dict[str, str]:
        """Detect task/application mentions."""
        task_matches = {}
        query_lower = natural_query.lower()
        
        sorted_tasks = sorted(self.task_mappings.items(), key=lambda x: len(x[0]), reverse=True)
        
        for task_term, short_name in sorted_tasks:
            if task_term in query_lower:
                task_matches['identifier.task_id'] = short_name
                break
        
        return task_matches

    def conservative_brand_match(self, natural_query: str) -> Dict[str, str]:
        """Conservative brand matching."""
        brand_matches = {}
        query_lower = natural_query.lower()
        
        for brand_term, schema_brand in self.brand_mappings.items():
            if brand_term in query_lower:
                brand_matches['attribs.brand_name'] = schema_brand
                break
        
        return brand_matches

    def extract_mentioned_attributes(self, natural_query: str) -> Set[str]:
        """Extract mentioned attributes conservatively."""
        mentioned_fields = set()
        query_lower = natural_query.lower()
        
        task_matches = self.detect_task_mentions(natural_query)
        for field in task_matches.keys():
            mentioned_fields.add(field)
        
        for term, field_path in self.field_mappings.items():
            if term in query_lower:
                if isinstance(field_path, list):
                    smart_field = self.smart_color_mapping(natural_query, term)
                    if smart_field:
                        mentioned_fields.add(smart_field)
                else:
                    mentioned_fields.add(field_path)
        
        brand_matches = self.conservative_brand_match(natural_query)
        for field in brand_matches.keys():
            mentioned_fields.add(field)
        
        return mentioned_fields

    def extract_mentioned_values(self, natural_query: str) -> Dict[str, str]:
        """Extract mentioned values conservatively."""
        mentioned_values = {}
        query_lower = natural_query.lower()
        
        task_matches = self.detect_task_mentions(natural_query)
        mentioned_values.update(task_matches)
        
        for term, field_path in self.field_mappings.items():
            if term in query_lower:
                if isinstance(field_path, list):
                    smart_field = self.smart_color_mapping(natural_query, term)
                    if smart_field:
                        mentioned_values[smart_field] = term 
                else:
                    if field_path != 'identifier.task_id':
                        mentioned_values[field_path] = term
        
        brand_matches = self.conservative_brand_match(natural_query)
        mentioned_values.update(brand_matches)
        
        return mentioned_values

    def smart_color_mapping(self, natural_query: str, color: str) -> str:
        """Smart color field mapping based on surrounding keywords."""
        query_lower = natural_query.lower()
        
        color_keywords = {
            'vehicle': 'attribs.vehicle_color',
            'car': 'attribs.vehicle_color',
            'truck': 'attribs.vehicle_color',
            'bus': 'attribs.vehicle_color',
            'bike': 'attribs.vehicle_color',
            'motorcycle': 'attribs.vehicle_color',
            'van': 'attribs.vehicle_color',
            'upper': 'attribs.upper_color',
            'shirt': 'attribs.upper_color',
            'jacket': 'attribs.upper_color',
            'top': 'attribs.upper_color',
            'lower': 'attribs.lower_color',
            'pants': 'attribs.lower_color',
            'jeans': 'attribs.lower_color',
            'footwear': 'attribs.footwear_color',
            'shoes': 'attribs.footwear_color',
            'boots': 'attribs.footwear_color'
        }
        
        for keyword, field in color_keywords.items():
            if f"{keyword} {color}" in query_lower or f"{color} {keyword}" in query_lower:
                return field
        
        if color in self.schema_fields['attribs.upper_color']:
            return 'attribs.upper_color'
        
        return ''

    def validate_with_conservative_match(self, field: str, natural_value: str, schema_value: Any) -> bool:
        """Conservative validation."""
        
        if isinstance(schema_value, dict) and any(op in schema_value for op in ["$gte", "$lte", "$eq"]):
            # For range queries or exact matches using operators, assume validation is handled upstream
            # or simply preserve them if they are in the natural query and schema allows.
            # Check if the full path or its normalized 'attribs.' equivalent is a preserve field
            # or if the base field (e.g. 'c_timestamp') is in schema_fields for general validation.
            if self.is_preserve_field(field) or self.is_preserve_field(f"response.event.{field}") or self.is_preserve_field(f"response.event.blobs.{field}"):
                return True
            # Also check if the normalized field is a known schema field and that value fits its type.
            # This logic might need to be more precise for specific operator types.
            if self.normalize_field_path(field) in self.schema_fields:
                return True # Assuming values for operators are correctly formed if the field is valid
            return False


        if field not in self.schema_fields:
            # If the field is not in schema_fields, we can't validate its enum values.
            # This might be for fields like 'url' which are preserved but don't have enums.
            return True # Assume valid if no schema defined for enum validation
        
        valid_schema_values = self.schema_fields[field]
        
        if field == 'identifier.task_id':
            return natural_value == schema_value and schema_value in valid_schema_values
        
        if field == 'attribs.brand_name':
            if natural_value in self.brand_mappings:
                return self.brand_mappings[natural_value] == schema_value and schema_value in valid_schema_values
            return natural_value in valid_schema_values and natural_value == schema_value
        
        natural_normalized = self.normalize_text(natural_value)
        schema_normalized = self.normalize_text(schema_value)

        return schema_value in valid_schema_values and (natural_normalized == schema_normalized or natural_normalized in schema_normalized)

    def extract_all_fields_recursive(self, query_dict: Dict, prefix: str = "") -> Dict[str, Any]:
        """Extract all fields recursively into a flattened dot-notation dictionary."""
        fields = {}
        
        for key, value in query_dict.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # If the value is a dictionary and contains MongoDB operators ($gte, $lte, etc.)
                # or if it's the 'attribs' dictionary itself, keep it as a nested dictionary.
                # Otherwise, continue flattening.
                if any(op.startswith("$") for op in value.keys()) or key == "attribs":
                    fields[current_path] = value
                else:
                    fields.update(self.extract_all_fields_recursive(value, current_path))
            elif isinstance(value, list):
                fields[current_path] = value
            else:
                fields[current_path] = value
                
        return fields

    def normalize_field_path(self, field_path: str) -> str:
        """Normalize field path for comparison with internal mappings (e.g., 'response.event.blobs.attribs.gender' -> 'attribs.gender')."""
        if field_path.startswith("response.event.blobs."):
            # Check for 'attribs.X' or 'label' directly under 'blobs'
            suffix = field_path.replace("response.event.blobs.", "")
            if suffix.startswith("attribs.") or suffix == "label":
                return suffix
        
        # Handle cases like "response.event.label" if it's not a blob label
        if field_path.startswith("response.event."):
            return field_path.replace("response.event.", "")
            
        return field_path

    def field_path_matches(self, mongo_field: str, mentioned_field: str) -> bool:
        """Check field path matching considering full paths and normalized paths."""
        # Direct full path match (e.g., 'response.event.c_timestamp' == 'response.event.c_timestamp')
        if mongo_field == mentioned_field:
            return True
        
        # Normalize the mongo_field path and compare (e.g., 'response.event.blobs.attribs.gender' vs 'attribs.gender')
        normalized_mongo_field = self.normalize_field_path(mongo_field)
        if normalized_mongo_field == mentioned_field:
            return True
        
        # Special handling for "label" which can be 'response.event.blobs.label' or 'label'
        if mongo_field == "response.event.blobs.label" and mentioned_field == "label":
            return True
        
        return False

    def parse_mongo_query_string(self, query_string: str) -> Dict:
        """Attempts to parse a string that might contain a MongoDB query structure."""
        try:
            return json.loads(query_string)
        except json.JSONDecodeError:
            print("Warning: Could not parse MongoDB query string as strict JSON.")
            return {}

    def validate_and_filter_query(self, natural_query: str, mongo_query_input: Union[str, Dict]) -> Dict:
        """Main validation function with field preservation."""
        
        mentioned_fields = self.extract_mentioned_attributes(natural_query)
        mentioned_values = self.extract_mentioned_values(natural_query)
        
        if isinstance(mongo_query_input, str):
            mongo_query_dict = self.parse_mongo_query_string(mongo_query_input)
        else:
            mongo_query_dict = mongo_query_input
        
        if not mongo_query_dict:
            return {}
        
        # This will flatten the input into the desired output format (dot notation)
        # while preserving original nested structures for operators or 'attribs' if needed.
        all_mongo_fields_flattened = self.extract_all_fields_recursive(mongo_query_dict)
        
        filtered_fields = {} # This will be our final output dictionary
        
        for mongo_full_path, mongo_value in all_mongo_fields_flattened.items():
            # If the value itself is a dictionary with operators or is the attribs object,
            # we need to handle its path and contents carefully.
            if isinstance(mongo_value, dict) and (any(op.startswith("$") for op in mongo_value.keys()) or mongo_full_path.endswith(".attribs")):
                # For objects like {"$gte": "...", "$lte": "..."} or {"accessories": "...", "footwear": "..."}
                # we need to decide if the *entire* object should be kept.
                # Its inclusion depends on whether its components (if 'attribs') or its path (if an operator field)
                # are mentioned or preserved.
                
                # Special handling for 'attribs' object itself
                if mongo_full_path.endswith(".attribs"):
                    kept_attribs = {}
                    # Iterate through the individual attributes within this 'attribs' dictionary
                    for attr_key, attr_value in mongo_value.items():
                        full_attr_path = f"{mongo_full_path}.{attr_key}" # e.g., "response.event.blobs.attribs.accessories"
                        normalized_attr_path = self.normalize_field_path(full_attr_path) # e.g., "attribs.accessories"
                        
                        if self.is_preserve_field(full_attr_path):
                            kept_attribs[attr_key] = attr_value
                            continue

                        if self.is_filterable_field(full_attr_path):
                            field_kept_in_attribs = False
                            for mentioned_field_path in mentioned_fields:
                                if self.field_path_matches(full_attr_path, mentioned_field_path):
                                    natural_value_for_attr = mentioned_values.get(mentioned_field_path)
                                    if natural_value_for_attr:
                                        if self.validate_with_conservative_match(normalized_attr_path, natural_value_for_attr, attr_value):
                                            kept_attribs[attr_key] = attr_value
                                            field_kept_in_attribs = True
                                            break
                                    else:
                                        if self.validate_field_value(normalized_attr_path, attr_value):
                                            kept_attribs[attr_key] = attr_value
                                            field_kept_in_attribs = True
                                            break
                            if field_kept_in_attribs:
                                continue # Move to next attribute in attribs
                            else:
                                pass # This attribute was filtered out
                        else: # Neither filterable nor explicitly preserved, keep it
                            kept_attribs[attr_key] = attr_value
                    
                    if kept_attribs:
                        filtered_fields[mongo_full_path] = kept_attribs
                    continue # Move to next top-level flattened field

                # Handling for fields with operators (like c_timestamp)
                elif self.is_preserve_field(mongo_full_path):
                    filtered_fields[mongo_full_path] = mongo_value
                    continue
                else: # Operators on filterable fields - check if the field itself is mentioned
                    field_kept_operator = False
                    normalized_mongo_field = self.normalize_field_path(mongo_full_path)
                    for mentioned_field_path in mentioned_fields:
                        if self.field_path_matches(mongo_full_path, mentioned_field_path):
                            # For operators, we just need the field path to be mentioned/preserved
                            filtered_fields[mongo_full_path] = mongo_value
                            field_kept_operator = True
                            break
                    if field_kept_operator:
                        continue
                    else:
                        pass # Filter out operator field if not mentioned/preserved
            else: # Simple key-value pair, not a dictionary with operators or 'attribs'
                if self.is_preserve_field(mongo_full_path):
                    filtered_fields[mongo_full_path] = mongo_value
                    continue

                if self.is_filterable_field(mongo_full_path):
                    field_kept_simple = False
                    normalized_mongo_field = self.normalize_field_path(mongo_full_path)

                    for mentioned_field_path in mentioned_fields:
                        if self.field_path_matches(mongo_full_path, mentioned_field_path):
                            natural_value_for_field = mentioned_values.get(mentioned_field_path)
                            if natural_value_for_field:
                                if self.validate_with_conservative_match(normalized_mongo_field, natural_value_for_field, mongo_value):
                                    filtered_fields[mongo_full_path] = mongo_value
                                    field_kept_simple = True
                                    break
                            else: # If natural language didn't explicitly provide a value for this simple field
                                if self.validate_field_value(normalized_mongo_field, mongo_value):
                                    filtered_fields[mongo_full_path] = mongo_value
                                    field_kept_simple = True
                                    break
                    if field_kept_simple:
                        continue
                    else:
                        pass # Filter out simple field if not mentioned/validated
                else:
                    # Neither filterable nor explicitly preserved, keep it
                    filtered_fields[mongo_full_path] = mongo_value
        
        return filtered_fields

    def validate_field_value(self, field: str, value: Any) -> bool:
        """Validate field value against schema enumerations."""
        if field in self.schema_fields:
            if field == 'attribs.brand_name':
                return value in self.schema_fields[field] or value in self.brand_mappings.values()
            return value in self.schema_fields[field]
        return True # If a field is not in schema_fields for enum validation, assume valid.


# Test the modified validator
validator = MongoQueryValidator()

# Test cases (adjusted for desired flattened output format)
test_cases = [
    {
        "name": "Accessories and Footwear with correct brand",
        "natural_query": "Show accessories glasses and footwear sport and car of maruti from 2025-06-16 to 2025-06-17",
        "mongo_query_input": {
            "response.event.blobs.attribs": {"accessories": "glasses", "footwear": "sport", "brand_name": "maruti_suzuki"},
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"},
            "response.event.blobs.label": "car"
        },
        "expected_output": {
            "response.event.blobs.attribs": {"accessories": "glasses", "footwear": "sport", "brand_name": "maruti_suzuki"},
            "response.event.blobs.label": "car",
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"}
        }
    },
    {
        "name": "Incorrect brand name, should be filtered",
        "natural_query": "Show car of xyz brand",
        "mongo_query_input": {
            "response.event.blobs.attribs": {"brand_name": "xyz_motors"},
            "response.event.blobs.label": "car"
        },
        "expected_output": {
            "response.event.blobs.label": "car" 
        }
    },
    {
        "name": "Unmentioned attribute, should be filtered",
        "natural_query": "Show cars",
        "mongo_query_input": {
            "response.event.blobs.attribs": {"accessories": "hat"},
            "response.event.blobs.label": "car"
        },
        "expected_output": {
            "response.event.blobs.label": "car" 
        }
    },
    {
        "name": "Timestamp only (preserved field)",
        "natural_query": "Events from yesterday",
        "mongo_query_input": {
            "response.event.c_timestamp": {"$gte": "2025-06-29T00:00:00Z", "$lte": "2025-06-30T00:00:00Z"}
        },
        "expected_output": {
            "response.event.c_timestamp": {"$gte": "2025-06-29T00:00:00Z", "$lte": "2025-06-30T00:00:00Z"}
        }
    },
    {
        "name": "Task ID query (filterable, but mentioned and mapped correctly)",
        "natural_query": "Show ANPR alerts",
        "mongo_query_input": {
            "identifier.task_id": "ANPR"
        },
        "expected_output": {
            "identifier.task_id": "ANPR"
        }
    },
    {
        "name": "Task ID with incorrect value in mongo query",
        "natural_query": "Show ANPR alerts",
        "mongo_query_input": {
            "identifier.task_id": "FR" 
        },
        "expected_output": {} 
    },
    {
        "name": "Vehicle color based on context",
        "natural_query": "show red cars",
        "mongo_query_input": {
            "response.event.blobs.attribs.vehicle_color": "red",
            "response.event.blobs.label": "car"
        },
        "expected_output": {
            "response.event.blobs.attribs.vehicle_color": "red",
            "response.event.blobs.label": "car"
        }
    },
    {
        "name": "Upper color based on context",
        "natural_query": "person with blue shirt",
        "mongo_query_input": {
            "response.event.blobs.attribs.upper_color": "blue",
            "response.event.blobs.attribs.upper_type": "shirt"
        },
        "expected_output": {
            "response.event.blobs.attribs.upper_color": "blue",
            "response.event.blobs.attribs.upper_type": "shirt"
        }
    },
    {
        "name": "Mixed query with preserved and filtered fields",
        "natural_query": "show red cars from camgroup_id-123",
        "mongo_query_input": {
            "response.event.blobs.attribs.vehicle_color": "red",
            "response.event.blobs.label": "car",
            "identifier.camgroup_id": "camgroup_id-123",
            "response.event.blobs.attribs.accessories": "hat" 
        },
        "expected_output": {
            "response.event.blobs.attribs.vehicle_color": "red",
            "response.event.blobs.label": "car",
            "identifier.camgroup_id": "camgroup_id-123"
        }
    },
     {
        "name": "Input with existing direct nested attribs (not $elemMatch) and correct values, output flattened",
        "natural_query": "Show accessories glasses and footwear sport and car of maruti from 2025-06-16 to 2025-06-17",
        "mongo_query_input": {
            "response.event.blobs": {
                "attribs": {"accessories": "glasses", "footwear": "sport", "brand_name": "maruti_suzuki"},
                "label": "car"
            },
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"}
        },
        "expected_output": {
            "response.event.blobs.attribs": {"accessories": "glasses", "footwear": "sport", "brand_name": "maruti_suzuki"},
            "response.event.blobs.label": "car",
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"}
        }
    },
    {
        "name": "Input with existing direct nested attribs, unmentioned attribute removed, output flattened",
        "natural_query": "Show accessories glasses from 2025-06-16 to 2025-06-17",
        "mongo_query_input": {
            "response.event.blobs": {
                "attribs": {"accessories": "glasses", "footwear": "sport"}, # footwear not mentioned
                "label": "person"
            },
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"}
        },
        "expected_output": {
            "response.event.blobs.attribs": {"accessories": "glasses"},
            "response.event.blobs.label": "person",
            "response.event.c_timestamp": {"$gte": "2025-06-16T00:00:00Z", "$lte": "2025-06-17T00:00:00Z"}
        }
    }
]

print("\n--- Running Test Cases ---")
for i, case in enumerate(test_cases):
    print(f"\nTest Case {i+1}: {case['name']}")
    filtered_query = validator.validate_and_filter_query(case['natural_query'], case['mongo_query_input'])
    
    print(f"Natural Query: {case['natural_query']}")
    print(f"Input Query: {json.dumps(case['mongo_query_input'], indent=4)}")
    print(f"Expected Output: {json.dumps(case['expected_output'], indent=4)}")
    print(f"Filtered Result: {json.dumps(filtered_query, indent=4)}")
    
    # Use deep comparison for dictionaries
    if filtered_query == case['expected_output']:
        print("Test Result: PASSED")
    else:
        print("Test Result: FAILED")
