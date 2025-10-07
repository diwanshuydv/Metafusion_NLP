import datetime
import subprocess
import json

now = datetime.datetime.now(datetime.timezone.utc)
formatted_dt_0 = now.strftime("%Y-%m-%dT%H:%M:%SZ")
formatted_dt_plus_one_0 = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
formatted_dt_minus_one_0 = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
formatted_dt_plus_7_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")


docs_content = [
    "natural language query: Find yash mongodb query: {\"match_id\": \"Yash\"}",
    f"natural language query: Was Pravar present today mongodb query: {{\"match_id\": \"Pravar\", \"c_timestamp\": {{\"$gte\": \"{formatted_dt_0}\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    f"natural language query: Was Nikhil seen in last 7 days mongodb query: {{\"match_id\": \"Nikhil\", \"c_timestamp\": {{\"$gte\": \"{formatted_dt_plus_7_ago}\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    "natural language query: Find all events from 10 aug to 15 aug mongodb query: {\"c_timestamp\": {\"$gte\": \"2025-08-10T00:00:00Z\", \"$lte\": \"2025-08-16T00:00:00.000Z\"}}",
    "natural language query: Find all events of vehicle with number plate GJ10SS1010 mongodb query: {\"attribs.ocr_result\": \"GJ10SS1010\"}",
    "natural language query: Find all alerts of Rajat from 10 jan 2025 to 12 jan 2025 mongodb query: {\"match_id\": \"Rajat\", \"c_timestamp\": {\"$gte\": \"2025-01-10T00:00:00Z\", \"$lte\": \"2025-01-13T00:00:00.000Z\"}}",
    "natural language query: Find all events of person wearing glasses mongodb query: {\"attribs.accessories\": \"glasses\"}",
    f"natural language query: Find events of yash on 10th sept mongodb query: {{\"match_id\": \"Yash\", \"c_timestamp\": {{\"$gte\": \"2025-09-10T00:00:00Z\", \"$lte\": \"2025-09-11T00:00:00.000Z\"}}}}",
    f"natural language query: Find events of athul on 1st sept with score greater than 70 percent mongodb query: {{\"match_id\": \"Athul\", \"c_timestamp\": {{\"$gte\": \"2025-09-01T00:00:00Z\", \"$lte\": \"2025-09-02T00:00:00.000Z\"}}, \"score\": {{\"$gt\": 0.7}}}}",
    "natural language query: Find vehicle with number plate starting with GJ mongodb query: {\"attribs.ocr_result\": {\"$regex\": \"^GJ\"}}",
    "natural language query: Retrieve all events for vehicles with number plates ending in '1010' mongodb query: {\"attribs.ocr_result\": {\"$regex\": \"1010\"}}",
    "natural language query: List all alerts of license plate task mongodb query: {\"task_id\": \"ANPR\"}",
    "natural language query: Find Person Slip Detection results in 'south_fr' camera mongodb query: {\"camera_id\": \"south_fr\", \"task_id\": \"SLIP_DETECT\"}",
    "natural language query: Find all events on raj ghat camera mongodb query: {\"camera_id\": \"Raj Ghat\"}",
    "natural language query: Find all events on office group mongodb query: {\"camgroup_id\": \"office\"}",
    "natural language query: Provide alerts when someone wore a vneck and capri mongodb query: {\"attribs\": {\"upper_type\": \"v_neck\", \"lower_type\": \"capri\"}}",
    f"natural language query: Find all events of Helmet Violation of today mongodb query: {{\"task_id\": \"helmet_violation\", \"c_timestamp\": {{\"$gte\": \"{formatted_dt_0}\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    f"natural language query: Find alerts of man wearing shirt today mongodb query: {{\"attribs\": {{\"upper_type\": \"shirt\", \"gender\": \"male\"}}, \"c_timestamp\": {{\"$gte\": \"{formatted_dt_0}\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    "natural language query: Find events of children who wore hat and boots mongodb query: {\"attribs\": {\"age\": \"child\", \"accessories\": \"hat\", \"footwear\": \"boots\"}}",
    "natural language query: Find events of kids with a box and wearing long trousers mongodb query: {\"attribs\": {\"age\": \"child\", \"carrying\": \"box\", \"lower_type\": \"long_trousers\"}}",
    f"natural language query: Give alerts of fat people wearing blue tshirt and sport shoes yesterday mongodb query: {{\"attribs\": {{\"upper_type\": \"tshirt\", \"footwear\": \"sport\", \"upper_color\": \"blue\", \"body_type\": \"fat\"}}, \"c_timestamp\": {{\"$gte\": \"{formatted_dt_minus_one_0}\", \"$lte\": \"{formatted_dt_0}\"}}}}",
    "natural language query: Find woman wearing hat and black casual shoes mongodb query: {\"attribs\": {\"gender\": \"female\", \"accessories\": \"hat\", \"footwear\": \"casual\", \"footwear_color\": \"black\"}}",
    "natural language query: Find woman mongodb query: {\"attribs\": {\"gender\": \"female\"}}",
    f"natural language query: Find woman wearing glasses and sport shoes today mongodb query: {{\"attribs\": {{\"gender\": \"female\", \"accessories\": \"glasses\", \"footwear\": \"sport\"}}, \"c_timestamp\": {{\"$gte\": \"{formatted_dt_0}\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    "natural language query: Give alerts of fat young adult men wearing vest, tight trousers and sport shoes mongodb query: {\"attribs\": {\"age\": \"adult\", \"upper_type\": \"vest\", \"lower_type\": \"tight_trousers\", \"footwear\": \"sport\", \"gender\": \"male\", \"body_type\": \"fat\"}}",
    "natural language query: Give alerts of normal bald elderly man wearing suit, tight trousers and casual shoes mongodb query: {\"attribs\": {\"age\": \"older_adult\", \"upper_type\": \"suit_up\", \"lower_type\": \"tight_trousers\", \"footwear\": \"casual\", \"gender\": \"male\", \"body_type\": \"normal\", \"hair_type\": \"bald_head\"}}",
    "natural language query: Filter out events of thin woman with long hair wearing sunglasses, skirt and short sleeve mongodb query: {\"attribs\": {\"body_type\": \"thin\", \"sleeve_type\": \"short_sleeve\", \"lower_type\": \"skirt\", \"hair_type\": \"long_hair\", \"gender\": \"female\", \"accessories\": \"glasses\"}}",
    f"natural language query: Find yesterday's events of Ishaan mongodb query: {{\"match_id\": \"Ishaan\", \"c_timestamp\": {{\"$gte\": \"{formatted_dt_minus_one_0}\", \"$lte\": \"{formatted_dt_0}\"}}}}",
    "natural language query: Send alerts of young adult woman with black hair wearing sweater, dress and carrying a pink paper bag mongodb query: {\"attribs\": {\"age\": \"adult\", \"upper_type\": \"sweater\", \"lower_type\": \"dress\", \"carrying\": \"paper_bag\", \"carrying_color\": \"pink\", \"gender\": \"female\", \"hair_color\": \"black\"}}",
    "natural language query: Find all Red cars mongodb query: {\"attribs\": {\"vehicle_color\": \"red\", \"label\": \"car\"}}",
    "natural language query: Find all blue TVS Ambulances mongodb query: {\"attribs\": {\"brand_name\": \"tvs\", \"special_type\": \"ambulance\", \"vehicle_color\": \"blue\", \"label\": \"ambulance\"}}",
    "natural language query: Find all Abandoned Objects found from 10th march to 20th march mongodb query: {\"task_id\": \"ABANDONED_BAG\", \"c_timestamp\": {\"$gte\": \"2025-03-10T00:00:00Z\", \"$lte\": \"2025-03-21T00:00:00.000Z\"}}",
    "natural language query: List all alerts of Loitering task mongodb query: {\"task_id\": \"dwell\"}",
    f"natural language query: Find all events of a side view person carrying hand bag from 3rd april to today mongodb query: {{\"attribs\": {{\"carrying\": \"hand_bag\", \"orientation\": \"side\"}}, \"c_timestamp\": {{\"$gte\": \"2025-04-03T00:00:00Z\", \"$lte\": \"{formatted_dt_plus_one_0}\"}}}}",
    f"natural language query: Find all events of person calling while wearing short sleeve from jan 10 to yesterday mongodb query: {{\"attribs\": {{\"actions\": \"calling\", \"sleeve_type\": \"short_sleeve\"}}, \"c_timestamp\": {{\"$gte\": \"2025-01-10T00:00:00Z\", \"$lte\": \"{formatted_dt_0}\"}}}}",
    f"natural language query: Find men alerts from yesterday mongodb query: {{\"attribs\": {{\"gender\": \"male\"}}, \"c_timestamp\": {{\"$gte\": \"{formatted_dt_minus_one_0}\", \"$lte\": \"{formatted_dt_0}\"}}}}",
    "natural language query: Find mini bus that are khakhi and 3 axle mongodb query: {\"attribs\": {\"vehicle_i_type\": \"3_axle\", \"vehicle_color\": \"khakhi\", \"label\": \"mini_bus\"}}",
    "natural language query: Find all motorbikes that are mcwg by kia mongodb query: {\"attribs\": {\"vehicle_i_type\": \"mcwg\", \"brand_name\": \"kia\", \"label\": \"motorbike\"}}",
    "natural language query: Find all white cars mongodb query: {\"attribs\": {\"vehicle_color\": \"white\", \"label\": \"car\"}}",
    "natural language query: Find all ambulances mongodb query: {\"attribs\": {\"special_type\": \"ambulance\", \"label\": \"ambulance\"}}",
    "natural language query: Find all alerts of collapsed person mongodb query: {\"task_id\": \"SLIP_DETECT\"}",
    "natural language query: Find all vehicles with speed more than 20 mongodb query: {\"attribs.speed\": {\"$gte\": 20}}",
    "natural language query: Find all plates which are one row mongodb query: {\"attribs.plate_layout\": \"one_row\"}",
    "natural language query: Give all alerts of violation mongodb query: {\"attribs.violation\": \"true\"}",
    "natural language query: Give all alerts of violation of two row number plates mongodb query: {\"attribs\": {\"violation\": \"true\", \"plate_layout\": \"two_row\"}}",
    "natural language query: Find all Non Commercial Plates mongodb query: {\"attribs.registration_type\": \"non_commercial_plate\"}",
    "natural language query: Find all rlvd alerts mongodb query: {\"task_id\": \"red_light_violation\"}",
    "natural language query: Find all LMVs that are black and made by honda mongodb query: {\"attribs\": {\"vehicle_i_type\": \"lmv\", \"brand_name\": \"honda\", \"vehicle_color\": \"black\"}}",
    "natural language query: Find vehicle with number plate containing L1 mongodb query: {\"attribs.ocr_result\": {\"$regex\": \"L1\"}}",

    ]
query_pairs_modified = [
    'natural language query : Find events where a fat man with short hair is wearing a green jacket, carrying a suitcase, and standing near a red truck labeled \'eicher\'. mongodb query: {"body_type": "fat", "hair_type": "short_hair", "upper_color": "green", "upper_type": "jacket", "carrying": "suitcase", "vehicle_label": "truck", "vehicle_color": "red", "brand_name": "eicher"}',
    'natural language query : Find events of a female with long hair wearing a blue tshirt and riding a yellow motorbike registered as commercial. mongodb query: {"gender": "female", "hair_type": "long_hair", "upper_color": "blue", "upper_type": "tshirt", "vehicle_label": "motorbike", "vehicle_color": "yellow", "registration_type": "commercial"}',
    'natural language query : Find a man with black hair wearing casual shirt and white leather shoes standing near a speeding green SUV with plate containing 4321. mongodb query: {"hair_color": "black", "upper_type": "shirt", "footwear": "leather", "footwear_color": "white", "vehicle_color": "green", "vehicle_type": "suv", "ocr_result": {"$regex": "4321"}}',
    'natural language query : Find events of a person carrying a messenger bag and riding a black car exceeding speed limit, detected by Speed Violation application. mongodb query: {"task_id": "speed_violation", "carrying": "messenger_bag", "vehicle_label": "car", "vehicle_color": "black", "violation": "yes"}',
    'natural language query : Find a person with glasses and a bald head walking near a mini truck with army markings, flagged under Helmet Violation task. mongodb query: {"task_id": "helmet_violation", "accessories": "glasses", "hair_type": "bald_head", "vehicle_label": "mini_truck", "special_type": "army_vehicle"}',
    'natural language query : Find a child wearing sandals and jeans near a white ambulance going the wrong way. mongodb query: {"task_id": "wrong_way", "age": "child", "footwear": "sandals", "lower_type": "jeans", "vehicle_color": "white", "special_type": "ambulance"}',
    'natural language query : Find events of an older adult male with brown short hair wearing a formal vest, standing near a red light violator with plate ending in 09. mongodb query: {"task_id": "red_light_violation", "age": "older_adult", "gender": "male", "hair_color": "brown", "hair_type": "short_hair", "upper_type": "formal", "ocr_result": {"$regex": "09$"}}',
    'natural language query : Find a man wearing orange shoes near a yellow bus. mongodb query: {"gender": "male", "footwear_color": "orange", "vehicle_label": "bus"}',
    'natural language query : Find events of a female carrying a red handbag near a blue car. mongodb query: {"gender": "female", "carrying_color": "red", "vehicle_color": "blue"}',
    'natural language query : Find events where someone is wearing a white formal shirt and standing next to a sedan. mongodb query: {"upper_color": "white", "upper_type": "formal", "vehicle_type": "sedan"}',
    'natural language query : Find an adult with glasses next to a cycle rikshaw. mongodb query: {"age": "adult", "accessories": "glasses", "vehicle_label": "cycle_rikshaw"}',
    'natural language query : Find events with helmet violation involving a red hatchback. mongodb query: {"task_id": "helmet_violation", "vehicle_color": "red", "vehicle_type": "hatchback"}',
    'natural language query : Find someone pushing and wearing a grey jacket. mongodb query: {"actions": "pushing", "upper_type": "jacket", "upper_color": "grey"}',
    'natural language query : Find a person with short hair wearing casual shorts. mongodb query: {"hair_type": "short_hair", "lower_type": "shorts", "lower_color": "brown"}',
    'natural language query : Find someone with black jeans and white sneakers. mongodb query: {"lower_type": "jeans", "lower_color": "black", "footwear_color": "white"}',
    'natural language query : Find a person with long sleeves and yellow backpack. mongodb query: {"sleeve_type": "long_sleeve", "carrying_color": "yellow", "carrying": "backpack"}',
    'natural language query : Find a man wearing green trousers and brown leather shoes. mongodb query: {"gender": "male", "lower_color": "green", "footwear": "leather"}',
    'natural language query : Find events involving a red motorbike. mongodb query: {"vehicle_label": "motorbike", "vehicle_color": "red"}',
    'natural language query : Find a person wearing a formal shirt and blue jeans. mongodb query: {"upper_type": "formal", "lower_color": "blue"}',
    'natural language query : Find events where a truck has the brand \'tata_motors\'. mongodb query: {"vehicle_label": "truck", "brand_name": "tata_motors"}',
    'natural language query : Find an older adult carrying a plastic bag. mongodb query: {"age": "older_adult", "carrying": "plastic_bag"}',
    'natural language query : Find a vehicle with number plate containing \'MH04\'. mongodb query: {"ocr_result": {"$regex": "MH04"}, "vehicle_label": "car"}',
    'natural language query : Find a person wearing red sandals. mongodb query: {"footwear": "sandals", "footwear_color": "red"}',
    'natural language query : Find events of a bald man wearing a white jacket. mongodb query: {"hair_type": "bald_head", "upper_type": "jacket"}',
    'natural language query : Find events of a bald man wearing a white jacket. mongodb query: {"hair_type": "bald_head", "upper_type": "jacket"}',
    'natural language query : Find a woman carrying a shoulder bag. mongodb query: {"gender": "female", "carrying": "shoulder_bag"}',
    'natural language query : Find an ambulance labeled as \'bharat_benz\'. mongodb query: {"special_type": "ambulance", "brand_name": "bharat_benz"}',
    'natural language query : Find a man wearing a black hat. mongodb query: {"gender": "male", "accessories": "hat"}',
    'natural language query : Find a yellow van with LMV classification and plate layout of two rows registered as commercial. mongodb query: {"vehicle_color": "yellow", "vehicle_label": "van", "vehicle_itype": "lmv", "registration_type": "commercial"}',
    'natural language query : Find an older adult wearing a green sweater, white trousers, and glasses. mongodb query: {"age": "older_adult", "upper_type": "sweater", "lower_color": "white", "accessories": "glasses"}',
    'natural language query : Find a person wearing a long coat with long sleeves, a muffler, and black boots. mongodb query: {"lower_type": "long_coat", "sleeve_type": "long_sleeve", "accessories": "muffler", "footwear_color": "black"}',
    'natural language query : Find a violence detection event involving a person gathering, wearing an orange shirt and purple jeans. mongodb query: {"task_id": "violence_detection", "actions": "gathering", "upper_color": "orange", "lower_color": "purple"}',
    'natural language query : Find a woman with red hair wearing a formal suit and holding a luggage case. mongodb query: {"gender": "female", "hair_color": "red", "upper_type": "suit", "carrying": "luggage_case"}',
    'natural language query : Find a speed violation by a black car with vehicle speed above 80 and a brand of \'audi\'. mongodb query: {"task_id": "speed_violation", "vehicle_color": "black", "vehicle_speed": {"$gt": 80}, "brand_name": "audi"}',
    'natural language query : Find an ambulance with front orientation and event priority p1 and blob priority p2. mongodb query: {"special_type": "ambulance", "orientation": "front", "event_priority": "p1", "blob_priority": "p2"}',
    'natural language query : Find a man pushing a baby buggy and wearing a v-neck green shirt with casual trousers. mongodb query: {"gender": "male", "actions": "pushing", "carrying": "baby_buggy", "upper_type": "v_neck"}',
    'natural language query : Find a bald person with white hair wearing a cotton shirt and orange shoes. mongodb query: {"hair_type": "bald_head", "hair_color": "white", "upper_type": "cotton", "footwear_color": "orange"}',
    'natural language query : Find events of a thin person with blue jeans, a logo shirt, white sneakers, and short hair. mongodb query: {"body_type": "thin", "lower_type": "jeans", "upper_type": "logo", "footwear_color": "white", "hair_type": "short_hair"}',
    'natural language query : Find red motorcycles from Yamaha brand with MCWG classification, a single row plate layout, and speed greater than 70. mongodb query: {"vehicle_color": "red", "vehicle_label": "motorbike", "brand_name": "yamaha", "vehicle_itype": "mcwg", "vehicle_speed": {"$gt": 70}}',
    'natural language query : Find a man wearing an orange plaid shirt and yellow shorts, with long hair and glasses. mongodb query: {"gender": "male", "upper_type": "plaid", "upper_color": "orange", "lower_color": "yellow", "hair_type": "long_hair"}',
    'natural language query : Find events with a mini van labeled \'mahindra\' violating red light with stop line violation and p1 event priority. mongodb query: {"vehicle_label": "mini_van", "brand_name": "mahindra", "red_light_violation": "yes", "stop_line_violation": "yes", "event_priority": "p1"}',
    'natural language query : Find a triple riding violation involving a person with black trousers, white t-shirt, headphones, and casual shoes. mongodb query: {"task_id": "triple_riding", "lower_color": "black", "upper_type": "tshirt", "accessories": "headphone", "footwear": "casual"}',
    'natural language query : Find all red light violations that occurred today. mongodb query: {"task_id": "red_light_violation", "c_timestamp": {"$gte": "2025-06-25T00:00:00Z", "$lte": "2025-06-26T00:00:00Z"}}',
    'natural language query : Find all helmet violations that happened yesterday involving a person wearing a blue jacket. mongodb query: {"task_id": "helmet_violation", "upper_color": "blue", "upper_type": "jacket", "c_timestamp": {"$gte": "2025-06-24T00:00:00Z", "$lte": "2025-06-25T00:00:00Z"}}',
    'natural language query : Find events between June 15 and June 20 involving a female with red hair carrying an umbrella. mongodb query: {"gender": "female", "hair_color": "red", "carrying": "umbrella", "c_timestamp": {"$gte": "2025-06-15T00:00:00Z", "$lte": "2025-06-21T00:00:00Z"}}',
    'natural language query : Find events from June 1st with white hatchbacks exceeding the speed of 100. mongodb query: {"vehicle_color": "white", "vehicle_label": "hatchback", "vehicle_speed": {"$gt": 100}, "c_timestamp": {"$gte": "2025-06-01T00:00:00Z", "$lte": "2025-06-02T00:00:00Z"}}',
    'natural language query : Show all violence detection events from June 20 to June 25 involving a crowd estimate above 50. mongodb query: {"task_id": "violence_detection", "crowd_estimate": {"$gt": 50}, "c_timestamp": {"$gte": "2025-06-20T00:00:00Z", "$lte": "2025-06-26T00:00:00Z"}}',
    'natural language query : Find events from June 10 to June 12 where a fat person wearing a red formal shirt and white trousers was near a blue hatchback with Hyundai branding. mongodb query: {"body_type": "fat", "upper_color": "red", "upper_type": "formal", "lower_color": "white", "vehicle_color": "blue", "vehicle_label": "hatchback", "brand_name": "hyundai", "c_timestamp": {"$gte": "2025-06-10T00:00:00Z", "$lte": "2025-06-13T00:00:00Z"}}',
    'natural language query : Find parking violations that happened yesterday involving a man in orange shirt and black jeans standing near a grey truck. mongodb query: {"task_id": "parking_violation", "gender": "male", "upper_color": "orange", "lower_color": "black", "vehicle_color": "grey", "vehicle_label": "truck", "c_timestamp": {"$gte": "2025-06-24T00:00:00Z", "$lte": "2025-06-25T00:00:00Z"}}',
    'natural language query : Show all triple riding alerts on June 22 where the person was wearing sandals and carrying a black hand bag near a white mini truck with Tata Motors branding. mongodb query: {"task_id": "triple_riding", "footwear": "sandals", "carrying": "hand_bag", "carrying_color": "black", "vehicle_color": "white", "vehicle_label": "mini_truck", "brand_name": "tata_motors", "c_timestamp": {"$gte": "2025-06-22T00:00:00Z", "$lte": "2025-06-23T00:00:00Z"}}',
    'natural language query : Find speed violations today involving a black SUV from Ford with a person wearing a grey hoodie and jeans. mongodb query: {"task_id": "speed_violation", "vehicle_color": "black", "vehicle_type": "suv", "brand_name": "ford", "upper_type": "jacket", "upper_color": "grey", "lower_type": "jeans", "c_timestamp": {"$gte": "2025-06-25T00:00:00Z", "$lte": "2025-06-26T00:00:00Z"}}',
    'natural language query : From June 18 to 20, find events where a person with long hair and blue t-shirt was near a maruti_suzuki sedan violating a red light. mongodb query: {"hair_type": "long_hair", "upper_color": "blue", "vehicle_label": "sedan", "brand_name": "maruti_suzuki", "red_light_violation": "yes", "c_timestamp": {"$gte": "2025-06-18T00:00:00Z", "$lte": "2025-06-21T00:00:00Z"}}',
    'natural language query : Find events involving a person with long hair wearing a white shirt and red trousers near a yellow truck. mongodb query: {"hair_type": "long_hair", "upper_color": "white", "lower_color": "red", "vehicle_color": "yellow"}',
    'natural language query : Find events where a male wearing a green vest is near a white motorbike registered as commercial. mongodb query: {"gender": "male", "upper_type": "vest", "vehicle_color": "white", "registration_type": "commercial"}',
    'natural language query : Show facial recognition alerts where a female with short hair is wearing a pink skirt and holding something. mongodb query: {"task_id": "FR", "gender": "female", "hair_type": "short_hair", "lower_type": "skirt"}',
    'natural language query : Find events where a person is wearing black sandals, has brown hair, and is near a graminseva_4wheeler. mongodb query: {"footwear_color": "black", "hair_color": "brown", "special_type": "graminseva_4wheeler", "footwear": "sandals"}',
    'natural language query : Find crowd estimation events with a flow percentage over 80 and crowd estimate over 100 involving a person wearing a blue sweater facing front. mongodb query: {"task_id": "CROWD_EST", "crowd_estimate": {"$gt": 100}, "crowd_flow_percentage": {"$gt": 80}, "orientation": "front"}',
    'natural language query : Find events where a person named Arjun is wearing a black formal shirt, red jeans, and the detection score is above 80 percent. mongodb query: {"match_id": "Arjun", "upper_type": "formal", "upper_color": "black", "score": {"$gt": 0.8}}',
    'natural language query : Find intruder detection alerts involving a person with glasses, having a confidence score below 60 percent, wearing a white sweater and blue trousers. mongodb query: {"task_id": "INTRUDER_DETECT", "accessories": "glasses", "score": {"$lt": 0.6}, "upper_type": "sweater"}',
    'natural language query : Get all events where a person named Priya is carrying an umbrella, has orange shoes, and a confidence score above 90 percent. mongodb query: {"match_id": "Priya", "carrying": "umbrella", "footwear_color": "orange", "score": {"$gt": 0.9}}',
    'natural language query : Find red light violations involving a person named Vikram wearing a helmet, with detection score greater than 70 percent and riding a white motorbike. mongodb query: {"task_id": "red_light_violation", "match_id": "Vikram", "accessories": "hat", "vehicle_label": "motorbike", "score": {"$gt": 0.7}}',
    'natural language query : Get all events involving a woman named Nisha, wearing a green jacket and long skirt, with a detection confidence score under 50 percent. mongodb query: {"match_id": "Nisha", "gender": "female", "upper_type": "jacket", "score": {"$lt": 0.5}}',
    'natural language query : Find events where a female wearing a blue formal jacket, black jeans, and carrying a backpack is tagged with blob priority p1. mongodb query: {"gender": "female", "upper_type": "formal", "lower_color": "black", "blob_priority": "p1"}',
    'natural language query : Find events with event priority p2 where a person is wearing a green sweater, grey trousers, and has a bald head. mongodb query: {"event_priority": "p2", "upper_type": "sweater", "lower_color": "grey", "hair_type": "bald_head"}',
    'natural language query : Find violence detection events with event priority p1 involving someone wearing a red t-shirt and white sneakers. mongodb query: {"task_id": "violence_detection", "event_priority": "p1", "upper_type": "tshirt", "footwear_color": "white"}',
    'natural language query : Find events where blob priority is p3 and the person is wearing a yellow plaid shirt, black sandals, and has short hair. mongodb query: {"blob_priority": "p3", "upper_type": "plaid", "footwear_color": "black", "hair_type": "short_hair"}',
    'natural language query : Get events marked as priority p4 where a person is carrying a hand trunk, wearing orange boots and a v-neck upper. mongodb query: {"event_priority": "p4", "carrying": "hand_trunk", "footwear": "boots", "upper_type": "v_neck"}',
    'natural language query : Find events where a male is holding something, wearing a formal white shirt and brown trousers, with blob priority p2 and wearing sport shoes. mongodb query: {"gender": "male", "actions": "holding", "upper_type": "formal", "lower_color": "brown", "blob_priority": "p2"}',
    'natural language query : Get events where someone is talking, wearing a grey jacket and yellow jeans, with orange shoes and long hair. mongodb query: {"actions": "talking", "upper_type": "jacket", "lower_color": "yellow", "footwear_color": "orange", "hair_type": "long_hair"}',
    'natural language query : Find events of a female gathering with others, wearing a green shirt, pink skirt, black sneakers, and glasses. mongodb query: {"gender": "female", "actions": "gathering", "upper_type": "shirt", "lower_color": "pink", "accessories": "glasses"}',
    'natural language query : Find events where a person is pushing something, wearing a black sweater and red jeans, with blue shoes and side orientation. mongodb query: {"actions": "pushing", "upper_type": "sweater", "lower_color": "red", "footwear_color": "blue", "orientation": "side"}',
    'natural language query : Get events where a person is pulling a trolley, has bald head, is wearing a cotton shirt and jeans, with yellow boots. mongodb query: {"actions": "pulling", "hair_type": "bald_head", "upper_type": "cotton", "lower_type": "jeans", "footwear_color": "yellow"}',
    'natural language query : Find events where the estimated crowd size is 50, crowd flow is 85%, crowd behavior is erratic, and a person is wearing a red shirt and jeans. mongodb query: {"crowd_estimate": 50, "crowd_flow_percentage": 85, "erratic_crowd": "yes", "upper_color": "red", "lower_type": "jeans"}',
    'natural language query : Get events where crowd estimate is 100, flow is 40%, crowd is not erratic, and someone is carrying a blue backpack while wearing a black tshirt. mongodb query: {"crowd_estimate": 100, "crowd_flow_percentage": 40, "erratic_crowd": "no", "carrying": "backpack", "upper_type": "tshirt"}',
    'natural language query : Find events with erratic crowd behavior, crowd estimate of 200, crowd flow of 60%, a female with a white jacket and pink skirt. mongodb query: {"erratic_crowd": "yes", "crowd_estimate": 200, "crowd_flow_percentage": 60, "gender": "female", "upper_type": "jacket"}',
    'natural language query : Find crowd estimation events where the crowd estimate is 75, flow percentage is 30%, and someone is wearing a hat, blue shirt, and orange trousers. mongodb query: {"task_id": "CROWD_EST", "crowd_estimate": 75, "crowd_flow_percentage": 30, "accessories": "hat", "upper_color": "blue"}',
    'natural language query : Get events where the crowd estimate is 300, the flow is 90%, and a person is wearing a green jacket, black jeans, and glasses. mongodb query: {"crowd_estimate": 300, "crowd_flow_percentage": 90, "upper_color": "green", "lower_color": "black", "accessories": "glasses"}',
    'natural language query : Find all Facial Recognition events where the person has short hair and is wearing a formal upper body outfit. mongodb query: {"task_id": "FR", "hair_type": "short_hair", "upper_type": "formal"}',
    'natural language query : Find PPE Violation events where a person is male and wearing a jacket. mongodb query: {"task_id": "PPE_VOILATION", "gender": "male", "upper_type": "jacket"}',
    'natural language query : Show Intruder Alert events involving someone carrying a suitcase and wearing red sandals. mongodb query: {"task_id": "INTRUDER_DETECT", "carrying": "suitcase", "footwear": "sandals"}',
    'natural language query : Get Helmet Violation events where the vehicle color is black and it’s a motorbike. mongodb query: {"task_id": "helmet_violation", "vehicle_label": "motorbike", "vehicle_color": "black"}',
    'natural language query : Show all Red Light Violation events where the vehicle brand is tata_motors and it\'s a sedan. mongodb query: {"task_id": "red_light_violation", "brand_name": "tata_motors", "vehicle_type": "sedan"}',
    'natural language query : Find events where the number plate starts with \'DL\' and the vehicle is a white hatchback. mongodb query: {"ocr_result": {"$regex": "^DL"}, "vehicle_color": "white", "vehicle_type": "hatchback"}',
    'natural language query : Get events where the plate ends with \'07\', the vehicle is a sedan, and the brand is maruti_suzuki. mongodb query: {"ocr_result": {"$regex": "07$"}, "vehicle_type": "sedan", "brand_name": "maruti_suzuki"}',
    'natural language query : Find events where the number plate contains \'XYZ\', the registration type is commercial, and vehicle label is mini_truck. mongodb query: {"ocr_result": {"$regex": "XYZ"}, "registration_type": "commercial", "vehicle_label": "mini_truck"}',
    'natural language query : Show events with number plates starting with \'MH12\' and ending with \'09\', and the vehicle is a truck. mongodb query: {"ocr_result": {"$regex": "^MH12.*09$"}, "vehicle_label": "truck", "vehicle_color": "blue"}',
    'natural language query : Get all events where the plate contains \'B1\', the vehicle is a black car, and the layout is one_raw. mongodb query: {"ocr_result": {"$regex": "B1"}, "vehicle_label": "car", "plate_layout": "one_raw"}',
    'natural language query : Find events involving an army vehicle that is green and labeled as a truck. mongodb query: {"special_type": "army_vehicle", "vehicle_color": "green", "vehicle_label": "truck"}',
    'natural language query : Get all events where an ambulance was moving at speed greater than 60 and is labeled as a van. mongodb query: {"special_type": "ambulance", "vehicle_speed": {"$gt": 60}, "vehicle_label": "van"}',
    'natural language query: Find yash mongodb query: {"match_id": "Yash"}',
    f'natural language query: Was Pravar present today mongodb query: {{"match_id": "Pravar", "c_timestamp": {{"$gte": "{formatted_dt_0}", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    f'natural language query: Was Nikhil seen in last 7 days mongodb query: {{"match_id": "Nikhil", "c_timestamp": {{"$gte": "{formatted_dt_plus_7_ago}", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    'natural language query: Find all events from 10 aug to 15 aug mongodb query: {"c_timestamp": {"$gte": "2025-08-10T00:00:00Z", "$lte": "2025-08-16T00:00:00.000Z"}}',
    'natural language query: Find all events of vehicle with number plate GJ10SS1010 mongodb query: {"ocr_result": "GJ10SS1010"}',
    'natural language query: Find all alerts of Rajat from 10 jan 2025 to 12 jan 2025 mongodb query: {"match_id": "Rajat", "c_timestamp": {"$gte": "2025-01-10T00:00:00Z", "$lte": "2025-01-13T00:00:00.000Z"}}',
    'natural language query: Find all events of person wearing glasses mongodb query: {"accessories": "glasses"}',
    f'natural language query: Find events of yash on 10th sept mongodb query: {{"match_id": "Yash", "c_timestamp": {{"$gte": "2025-09-10T00:00:00Z", "$lte": "2025-09-11T00:00:00.000Z"}}}}',
    f'natural language query: Find events of athul on 1st sept with score greater than 70 percent mongodb query: {{"match_id": "Athul", "score": {{"$gt": 0.7}}, "c_timestamp": {{"$gte": "2025-09-01T00:00:00Z", "$lte": "2025-09-02T00:00:00.000Z"}}}}',
    'natural language query: Find vehicle with number plate starting with GJ mongodb query: {"ocr_result": {"$regex": "^GJ"}}',
    'natural language query: Retrieve all events for vehicles with number plates ending in \'1010\' mongodb query: {"ocr_result": {"$regex": "1010$"}}',
    'natural language query: List all alerts of license plate task mongodb query: {"task_id": "ANPR"}',
    'natural language query: Find Person Slip Detection results in \'south_fr\' camera mongodb query: {"camera_id": "south_fr", "task_id": "SLIP_DETECT"}',
    'natural language query: Find all events on raj ghat camera mongodb query: {"camera_id": "Raj Ghat"}',
    'natural language query: Find all events on office group mongodb query: {"camgroup_id": "office"}',
    'natural language query: Provide alerts when someone wore a vneck and capri mongodb query: {"upper_type": "v_neck", "lower_type": "capri"}',
    f'natural language query: Find all events of Helmet Violation of today mongodb query: {{"task_id": "helmet_violation", "c_timestamp": {{"$gte": "{formatted_dt_0}", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    f'natural language query: Find alerts of man wearing shirt today mongodb query: {{"upper_type": "shirt", "gender": "male", "c_timestamp": {{"$gte": "{formatted_dt_0}", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    'natural language query: Find events of children who wore hat and boots mongodb query: {"age": "child", "accessories": "hat", "footwear": "boots"}',
    'natural language query: Find events of kids with a box and wearing long trousers mongodb query: {"age": "child", "carrying": "box", "lower_type": "long_trousers"}',
    f'natural language query: Give alerts of fat people wearing blue tshirt and sport shoes yesterday mongodb query: {{"upper_type": "tshirt", "footwear": "sport", "upper_color": "blue", "body_type": "fat", "c_timestamp": {{"$gte": "{formatted_dt_minus_one_0}", "$lte": "{formatted_dt_0}"}}}}',
    'natural language query: Find woman wearing hat and black casual shoes mongodb query: {"gender": "female", "accessories": "hat", "footwear": "casual", "footwear_color": "black"}',
    'natural language query: Find woman mongodb query: {"gender": "female"}',
    f'natural language query: Find woman wearing glasses and sport shoes today mongodb query: {{"gender": "female", "accessories": "glasses", "footwear": "sport", "c_timestamp": {{"$gte": "{formatted_dt_0}", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    'natural language query: Give alerts of fat young adult men wearing vest, tight trousers and sport shoes mongodb query: {"age": "adult", "upper_type": "vest", "lower_type": "tight_trousers", "footwear": "sport", "gender": "male", "body_type": "fat"}',
    'natural language query: Give alerts of normal bald elderly man wearing suit, tight trousers and casual shoes mongodb query: {"age": "older_adult", "upper_type": "suit_up", "lower_type": "tight_trousers", "footwear": "casual", "gender": "male", "body_type": "normal", "hair_type": "bald_head"}',
    'natural language query: Filter out events of thin woman with long hair wearing sunglasses, skirt and short sleeve mongodb query: {"body_type": "thin", "sleeve_type": "short_sleeve", "lower_type": "skirt", "hair_type": "long_hair", "gender": "female", "accessories": "glasses"}',
    f'natural language query: Find yesterday\'s events of Ishaan mongodb query: {{"match_id": "Ishaan", "c_timestamp": {{"$gte": "{formatted_dt_minus_one_0}", "$lte": "{formatted_dt_0}"}}}}',
    'natural language query: Send alerts of young adult woman with black hair wearing sweater, dress and carrying a pink paper bag mongodb query: {"age": "adult", "upper_type": "sweater", "lower_type": "dress", "carrying": "paper_bag", "carrying_color": "pink", "gender": "female", "hair_color": "black"}',
    'natural language query: Find all Red cars mongodb query: {"vehicle_color": "red", "label": "car"}',
    'natural language query: Find all blue TVS Ambulances mongodb query: {"brand_name": "tvs", "special_type": "ambulance", "vehicle_color": "blue", "label": "ambulance"}',
    'natural language query: Find all Abandoned Objects found from 10th march to 20th march mongodb query: {"task_id": "ABANDONED_BAG", "c_timestamp": {"$gte": "2025-03-10T00:00:00Z", "$lte": "2025-03-21T00:00:00.000Z"}}',
    'natural language query: List all alerts of Loitering task mongodb query: {"task_id": "dwell"}',
    f'natural language query: Find all events of a side view person carrying hand bag from 3rd april to today mongodb query: {{"carrying": "hand_bag", "orientation": "side", "c_timestamp": {{"$gte": "2025-04-03T00:00:00Z", "$lte": "{formatted_dt_plus_one_0}"}}}}',
    f'natural language query: Find all events of person calling while wearing short sleeve from jan 10 to yesterday mongodb query: {{"actions": "calling", "sleeve_type": "short_sleeve", "c_timestamp": {{"$gte": "2025-01-10T00:00:00Z", "$lte": "{formatted_dt_0}"}}}}',
    f'natural language query: Find men alerts from yesterday mongodb query: {{"gender": "male", "c_timestamp": {{"$gte": "{formatted_dt_minus_one_0}", "$lte": "{formatted_dt_0}"}}}}',
    'natural language query: Find mini bus that are khakhi and 3 axle mongodb query: {"vehicle_i_type": "3_axle", "vehicle_color": "khakhi", "label": "mini_bus"}',
    'natural language query: Find all motorbikes that are mcwg by kia mongodb query: {"vehicle_i_type": "mcwg", "brand_name": "kia", "label": "motorbike"}',
    'natural language query: Find all white cars mongodb query: {"vehicle_color": "white", "label": "car"}',
    'natural language query: Find all ambulances mongodb query: {"special_type": "ambulance", "label": "ambulance"}',
    'natural language query: Find all alerts of collapsed person mongodb query: {"task_id": "SLIP_DETECT"}',
    'natural language query: Find all vehicles with speed more than 20 mongodb query: {"speed": {"$gte": 20}}',
    'natural language query: Find all plates which are one row mongodb query: {"plate_layout": "one_row"}',
    'natural language query: Give all alerts of violation mongodb query: {"violation": "true"}',
    'natural language query: Give all alerts of violation of two row number plates mongodb query: {"violation": "true", "plate_layout": "two_row"}',
    'natural language query: Find all Non Commercial Plates mongodb query: {"registration_type": "non_commercial_plate"}',
    'natural language query: Find all rlvd alerts mongodb query: {"task_id": "red_light_violation"}',
    'natural language query: Find all LMVs that are black and made by honda mongodb query: {"vehicle_i_type": "lmv", "brand_name": "honda", "vehicle_color": "black"}',
    'natural language query: Find vehicle with number plate containing L1 mongodb query: {"ocr_result": {"$regex": "L1"}}',
    'natural language query: Show events where a graminseva_3wheeler was detected and it is blue in color and labeled as e_rikshaw. mongodb query: {"special_type": "graminseva_3wheeler", "vehicle_color": "blue", "vehicle_label": "e_rikshaw"}',
    'natural language query: Get all events involving a campervan with black color and front orientation. mongodb query: {"special_type": "campervan", "vehicle_color": "black", "orientation": "front"}',
    'natural language query: Find events with graminseva_4wheeler labeled as a mini_bus and registered as commercial. mongodb query: {"special_type": "graminseva_4wheeler", "vehicle_label": "mini_bus", "registration_type": "commercial"}',
    'natural language query: Find events where a woman with long hair is wearing a blue skirt. mongodb query: {"gender": "female", "hair_type": "long_hair", "lower_type": "skirt"}',
    'natural language query: Show all events involving a child wearing a v_neck shirt and carrying a backpack. mongodb query: {"age": "child", "upper_type": "v_neck", "carrying": "backpack"}',
    'natural language query: Get events with people performing the action \'calling\', wearing red trousers, and having glasses. mongodb query: {"actions": "calling", "lower_color": "red", "accessories": "glasses"}',
    'natural language query: Find events involving someone with bald head, long sleeves, and carrying a paper bag. mongodb query: {"hair_type": "bald_head", "sleeve_type": "long_sleeve", "carrying": "paper_bag"}',
    'natural language query: Get all events marked with event priority p2 where the person is wearing an orange shirt and brown leather shoes. mongodb query: {"event_priority": "p2", "upper_color": "orange", "footwear": "leather"}',
    'natural language query: Find events where crowd estimate is more than 50, the crowd is behaving erratically, and the camera ID is \'station_north\'. mongodb query: {"crowd_estimate": {"$gt": 50}, "erratic_crowd": "yes", "camera_id": "station_north"}',
    'natural language query: Get all events where the crowd flow percentage is above 80, from camgroup \'city_center\', and labeled as \'CROWD_EST\' task. mongodb query: {"crowd_flow_percentage": {"$gt": 80}, "camgroup_id": "city_center", "task_id": "CROWD_EST"}',
    'natural language query: Show events where crowd flow is below 30 percent, crowd is not erratic, and camera ID is \'entry_gate_3\'. mongodb query: {"crowd_flow_percentage": {"$lt": 30}, "erratic_crowd": "no", "camera_id": "entry_gate_3"}',
    'natural language query: Find all events where the crowd estimate is exactly 100, erratic behavior is marked \'yes\', and the camera group is \'main_square\'. mongodb query: {"crowd_estimate": 100, "erratic_crowd": "yes", "camgroup_id": "main_square"}',
    'natural language query: Get events where crowd flow percentage is between 40 and 70, crowd estimate is over 20, and task is Crowd Estimation. mongodb query: {"crowd_flow_percentage": {"$gte": 40, "$lte": 70}, "crowd_estimate": {"$gt": 20}, "task_id": "CROWD_EST"}'
]



payload = {
    "docs": query_pairs_modified
}

json_payload = json.dumps(payload)

import shlex
quoted_json_payload = shlex.quote(json_payload)

curl_command = f"""curl -X POST http://localhost:6080/insert \\
  -H "Content-Type: application/json" \\
  -d {quoted_json_payload}""" # No extra quotes here, shlex.quote adds them

print("Generated curl command:")
print(curl_command)

# Execute the command
try:
    result = subprocess.run(curl_command, shell=True, check=True, capture_output=True, text=True)
    print("\nCurl command executed successfully!")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except subprocess.CalledProcessError as e:
    print(f"\nError executing curl command (Exit Status {e.returncode}):")
    print("STDOUT:", e.stdout)
    print("STDERR:", e.stderr)
    print("Command tried to execute:\n", e.cmd)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
