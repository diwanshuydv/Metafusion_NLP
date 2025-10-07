import requests
import json
import csv
import os
import time
# --- Configuration ---
API_URL = "http://0.0.0.0:8080/completion"
QUESTIONS_FILE = "questions.txt"
OUTPUT_FILE = "responses.csv"
N_PREDICT = 256 # Number of tokens to predict
SCHEMA = """Identifier Fields-->
  camgroup_id: Group identifier for filtering events by site, location, deployment, or custom name
  task_id: Map natural language application names to their corresponding short_name values
  Values: `ANPR, CROWD_EST, CROWD_COUNT, FR, ABANDONED_BAG, INTRUDER_DETECT, CAM_TAMPERING, SLIP_DETECT, PPE_VOILATION, wrong_way, helmet_violation, triple_riding, speed_violation, red_light_violation, violence_detection, dwell, wii, whh, qm, tg, lane_violation, seatbelt, parking_violation, pat, vat, fns`
    """"mappings"""": [
                    {""""application_name"""": """"License Plate Recognition"""", """"task_id_value"""": """"ANPR""""},
                    {""""application_name"""": """"Crowd Estimation"""", """"task_id_value"""": """"CROWD_EST""""},
                    {""""application_name"""": """"Crowd Count"""", """"task_id_value"""": """"CROWD_COUNT""""},
                    {""""application_name"""": """"Facial Recognition"""", """"task_id_value"""": """"FR""""},
                    {""""application_name"""": """"Abandoned Bag Alert"""", """"task_id_value"""": """"ABANDONED_BAG""""},
                    {""""application_name"""": """"Intruder Alert"""", """"task_id_value"""": """"INTRUDER_DETECT""""},
                    {""""application_name"""": """"Camera Tampering"""", """"task_id_value"""": """"CAM_TAMPERING""""},
                    {""""application_name"""": """"Person Slip Detection"""", """"task_id_value"""": """"SLIP_DETECT""""},
                    {""""application_name"""": """"PPE Violation"""", """"task_id_value"""": """"PPE_VOILATION""""},
                    {""""application_name"""": """"Wrong Way"""", """"task_id_value"""": """"wrong_way""""},
                    {""""application_name"""": """"Helmet Violation"""", """"task_id_value"""": """"helmet_violation""""},
                    {""""application_name"""": """"Triple Riding"""", """"task_id_value"""": """"triple_riding""""},
                    {""""application_name"""": """"Speed Violation"""", """"task_id_value"""": """"speed_violation""""},
                    {""""application_name"""": """"Red Light Violation"""", """"task_id_value"""": """"red_light_violation""""},
                    {""""application_name"""": """"Violence Detection"""", """"task_id_value"""": """"violence_detection""""},
                    {""""application_name"""": """"Loitering"""", """"task_id_value"""": """"dwell""""},
                    {""""application_name"""": """"Woman In Isolation"""", """"task_id_value"""": """"wii""""},
                    {""""application_name"""": """"Woman Hailing Help"""", """"task_id_value"""": """"whh""""},
                    {""""application_name"""": """"Queue Management"""", """"task_id_value"""": """"qm""""},
                    {""""application_name"""": """"Tailgating"""", """"task_id_value"""": """"tg""""},
                    {""""application_name"""": """"Lane violation"""", """"task_id_value"""": """"lane_violation""""},
                    {""""application_name"""": """"Seat belt"""", """"task_id_value"""": """"seatbelt""""},
                    {""""application_name"""": """"Parking violation"""", """"task_id_value"""": """"parking_violation""""},
                    {""""application_name"""": """"Person Attribute"""", """"task_id_value"""": """"pat""""},
                    {""""application_name"""": """"Vehicle Attribute"""", """"task_id_value"""": """"vat""""},
                    {""""application_name"""": """"Fire and Smoke Detection"""", """"task_id_value"""": """"fns""""},
                    {""""application_name"""": """"VIDES"""", """"task_id_value"""": """"parking_violation""""}
                  ]
  camera_id: Individual camera identifier

Event Fields-->
  event_priority: Event priority level (`p1, p2, p3, p4` - p1 highest)
  event_id: Unique event identifier string
  c_timestamp: Event timestamp in ISO format (YYYY-MM-DDTHH:MM:SSZ)

Blob Fields-->
  url: Blob/image URL string
  blob_priority: Blob priority level (`p1, p2, p3, p4`) -- p1 is highest priority and p4 lowest
  score: Detection confidence score (0.0 to 1.0)
  match_id: Person identification by their name for queries like find <person_name>. 

Vehicle Attributes-->
  special_type: Special vehicle categories (`army_vehicle, ambulance, graminseva_4wheeler, graminseva_3wheeler, campervan`)
  brand_name: Vehicle brand [""""tvs"""", """"maruti_suzuki"""", """"eicher"""", """"ashok_leyland"""", """"mercedes_benz"""", """"royal_enfield"""", """"chevrolet"""", """"fiat"""", """"jaguar"""", """"audi"""", """"toyota"""", """"sml"""", """"bajaj"""", """"jbm"""", """"bharat_benz"""", """"hero_motor"""", """"volvo"""", """"nissan"""", """"renault"""", """"volkswagen"""", """"mazda"""", """"hero_honda"""", """"hyundai"""", """"mg"""", """"skoda"""", """"land_rover"""", """"yamaha"""", """"kia"""", """"mahindra"""", """"mitsubishi"""", """"ford"""", """"jeep"""", """"tata_motors"""", """"honda"""", """"bmw"""", """"coupe"""", """"force""""]
  vehicle_color: Vehicle color [""""khakhi"""", """"silver"""", """"yellow"""", """"pink"""", """"purple"""", """"green"""", """"blue"""", """"brown"""", """"maroon"""", """"red"""", """"orange"""", """"violet"""", """"white"""", """"black"""", """"grey""""]
  vehicle_type: Vehicle body type [""""sedan"""", """"suv"""", """"micro"""", """"hatchback"""", """"wagon"""", """"pick_up"""", """"convertible""""]
  vehicle_itype: Vehicle classification [""""hmv"""", """"lmv"""", """"lgv"""", """"3_axle"""", """"5_axle"""", """"mcwg"""", """"6_axle"""", """"2_axle"""", """"4_axle"""", """"heavy_vehicle""""]
  vehicle_speed: Current vehicle speed (number)
  vehicle_speed_limit: Speed limit for vehicle (number)
  vehicle_label: Detected vehicle type[""""bus"""", """"car"""", """"truck"""", """"motorbike"""", """"bicycle"""", """"e_rikshaw"""", """"cycle_rikshaw"""", """"tractor"""", """"cement_mixer"""", """"mini_truck"""", """"mini_bus"""", """"mini_van"""", """"van""""]
  plate_layout: License plate layout (`one_raw, two_raw`)
  ocr_result: License plate OCR text - use for number plate queries
  registration_type: Vehicle registration (`commercial, non-commercial`)
  Person Attributes-->
  actions: Person actions (`calling, talking, gathering, holding, pushing, pulling, carry_arm, carry_hand`)
  age: Age category (`child, adult, older_adult`)
  body_type: Body build (`fat, normal, thin`)
  gender: Person gender (`female, male`)
  hair_color: Hair color [""""black"""", """"blue"""", """"brown"""", """"green"""", """"grey"""", """"orange"""", """"pink"""", """"purple"""", """"red"""", """"white"""", """"yellow""""]
  hair_type: Hair style (`bald_head, long_hair, short_hair`)
  upper_type: Upper clothing type [""""stride"""", """"splice"""", """"casual"""", """"formal"""", """"jacket"""", """"logo"""", """"plaid"""", """"thin_stripes"""", """"tshirt"""", """"other"""", """"v_neck"""", """"suit"""", """"thick_stripes"""", """"shirt"""", """"sweater"""", """"vest"""", """"cotton"""", """"suit_up"""", """"tight""""],
  upper_color: Upper clothing color [""""black"""", """"blue"""", """"brown"""", """"green"""", """"grey"""", """"orange"""", """"pink"""", """"purple"""", """"red"""", """"white"""", """"yellow""""], lower_type: Lower clothing type [""""stripe"""", """"pattern"""", """"long_coat"""", """"trousers"""", """"shorts"""", """"skirt_and_dress"""", """"boots"""", """"long_trousers"""", """"skirt"""", """"short_skirt"""", """"dress"""", """"jeans"""", """"tight_trousers"""", """"capri"""", """"hot_pants"""", """"long_skirt"""", """"plaid"""", """"thin_stripes"""", """"suits"""", """"casual"""", """"formal""""]
  lower_color: Lower clothing color [""""black"""", """"blue"""", """"brown"""", """"green"""", """"grey"""", """"orange"""", """"pink"""", """"purple"""", """"red"""", """"white"""", """"yellow""""],
  sleeve_type: Sleeve length (`short_sleeve, long_sleeve`)
  footwear: Shoe type [""""leather"""", """"sport"""", """"boots"""", """"cloth"""", """"casual"""", """"sandals"""", """"stocking"""", """"leather_shoes"""", """"shoes"""", """"sneaker""""],
  footwear_color: Shoe color [""""black"""", """"blue"""", """"brown"""", """"green"""", """"grey"""", """"orange"""", """"pink"""", """"purple"""", """"red"""", """"white"""", """"yellow""""],
  carrying: Items carried [""""hand_bag"""", """"shoulder_bag"""", """"hold_objects_in_front"""", """"backpack"""", """"messenger_bag"""", """"nothing"""", """"plastic_bags"""", """"baby_buggy"""", """"shopping_trolley"""", """"umbrella"""", """"folder"""", """"luggage_case"""", """"suitcase"""", """"box"""", """"plastic_bag"""", """"paper_bag"""", """"hand_trunk"""", """"other""""]
  carrying_color: Color of carried items [""""black"""", """"blue"""", """"brown"""", """"green"""", """"grey"""", """"orange"""", """"pink"""", """"purple"""", """"red"""", """"white"""", """"yellow""""],
  accessories: Worn accessories [""""glasses"""", """"muffler"""", """"hat"""", """"nothing"""", """"headphone"""", """"hair_band"""", """"kerchief""""]
  occupation: Person's job/role (free text)
  orientation: Facing direction (`front, back, side`)

Crowd & Violation Fields-->
  crowd_estimate: Integer count from crowd estimation
  erratic_crowd: Whether crowd behavior is erratic (`yes, no`)
  crowd_flow_percentage: Crowd flow percentage (0-100)
  violation: General violation flag (`yes, no`)
  red_light_violation: Red light violation (`yes, no`)
  stop_line_violation: Stop line violation (`yes, no`)

Key Usage Notes-->
  Use task_id values to filter by application type
  Use ocr_result for license plate number searches with regex
  Priority levels p1=highest, p4=lowest for both events and blobs
  Timestamps are in ISO format with 'Z' suffix
  All color fields use lowercase color names
  Enum values are case-sensitive and use underscores
"""

natural_language_queries = [
    "Can you find all License Plate Recognition alerts originating from the 'vizag-cam-12' unit?",
    "Can you find all License Plate Recognition alerts originating from the vizag-cam-12 camera?",
    "Are there any PPE violations recorded?",
    "Show me events that captured a male individual.",
    "Show me any black SUVs detected from 2025-01-01 to 2025-01-31, where the license plate string pattern starts with \"MH04\".",
    "Any blue colored sedans?",
    "Show me all CAM_TAMPERING events that occurred recently.",
    "Was Abdul identified in any surveillance footage?",
    "Show me Yashs detections, specifically when he had leather boots and was carrying nothing, if he was talking.",
    "Find all traffic violations from Main_Road_Section between 2025-06-01 and 2025-06-30 for vehicles with license plates starting with DL.",
    "Find all traffic incidents from March 10th to May 22nd, 2024, where a vehicle with a license plate like MH12...6789 was caught speeding over 70.",
    "On 21/12/2025, were there any PPE Violation incidents in the Warehouse_CCTV group?",
    "List PAT alerts for adult men carrying a backpack (either blue or black) and wearing spectacles in the first week of 2025.",
    "Find any instances where the facial recognition identified Fatima.",
    "Find events from 'vizag-cam-12' over the past month involving a 'blue' 'Tata Motors' 'SUV' and a 'male' wearing a 'yellow' 'tshirt'.",
    "Were any adult females in green shirts observed?",
    "What heavy motor vehicles were found exceeding the speed limit?",
    "What hmv were found exceeding the speed limit?",
    "Locate any instances of 'Loitering' activity in the past 24 hours.",
    "Retrieve events between 2025-01-01 and 2025-01-31 where the number plate matches pattern 'DL.*8337' and the vehicle was violating a speed limit of 60 km/h.",
    "Find all events where a 'Toyota' vehicle, either white or silver, had a license plate containing '833' and a detection score above 0.8.",
    "Which vehicles were detected moving faster than 80 kilometers per hour?",
    "Retrieve all events from cameras starting with SEC- where a Toyota or Honda sedan was detected traveling between 80 and 100 km/h.",
    "Are there any Queue Management system alerts?",
    "Are there any PPE compliance warnings from the 'construction_site_gate' camera group?",
    "Are there any PPE compliance warnings from the construction_site_gate camera group?",
    "Show me any SUVs that had a number plate finishing with 8337 from March 15th to April 20th, 2025.",
    "golden off-road car",
    "Find any thin, older adults involved in a pushing action.",
    "Retrieve records of anyone sporting black footwear of the 'boots' type.",
    "During March 2025, were there any 'car' related incidents involving 'red light violations' or 'stop line violations'?",
    "During 1 March 2025 to 1 April 2025, were there any 'car' related incidents involving 'red light violations' or 'stop line violations'?",
    "Are there any 'Wrong Way' or 'Red Light Violation' events where a male person was wearing a 'short_sleeve' upper type, from cameras 'vizag-cam-12' or 'sector_42_cam' in the past 7 days?",
    "Locate individuals wearing specific colored shoes, e.g., red sneakers.",
    "Find events of 'Helmet Violation' where the 'camera_id' contains 'entry' and the detected vehicle type is a 'motorbike' or 'scooter' (motorbike label) between '2024-11-01' and '2024-11-30'.",
    "Show me any grown women in lengthy jackets with shoulder bags who were seen speaking.",
    "Show me all events from TiharBlockA during January 2025 involving a blue sedan whose registration includes DL.",
    "Show me all events from 'TiharBlockA' during January 2025 involving a blue sedan whose registration includes 'DL'.",
    "Find anyone with a rucksack.",
    "Show me alerts indicating physical altercations.",
    "Have any fire or smoke alerts been triggered in the 'factory_floor_east' area?",
    "Have any fire or smoke alerts been triggered in the factory_floor_east area?",
    "List PAT alerts for adult men carrying a backpack (either blue or black) and wearing spectacles in the first week of 2025.",
    "find alerts in the first week of 2025.",
    "Find any instances where the facial recognition identified Fatima.",
    "Find all instances where 'Abdul' was recognized last week.",
    "Identify any person wearing eyewear.",
    "Get alerts from camera vizag-cam-12 showing a person wearing a hat and jeans.",
    "Find any instances of camera sabotage.",
    "Retrieve any 'Woman In Isolation' alerts.",
    "Retrieve 'woman hailing help' incidents from the 'office_entry' camera.",
    "Retrieve all 'Person Attribute' events where someone is seen 'talking' or 'calling' and has a 'thin' body type, captured by a camera ID containing 'vizag'.",
    "Were there any loitering incidents where the person was carrying an umbrella?",
    "Show me FR detections of individuals with items held in front.",
    "Show me all 'PPE Violation' events from 'B3_west' where the detected person has 'short_hair' and is wearing a 'jacket' with 'long_sleeve'.",
    "Show all 'Person Attribute' alerts for males with short sleeves and bald heads recorded by camera 'B3_west' on 2025-12-31.",
    "Identify all abandoned bag alerts detected by cameras starting with 'vizag-cam' where a female was seen carrying a 'luggage' item just before the alert.",
    "Get alerts showing individuals involved in a 'seatbelt infringement'.",
    "Retrieve Crowd Estimation events on the 'entry_cam_1' for March 15, 2025, during business hours, if the crowd flow was under half of the capacity.",
    "Show me critical priority events from the 'intruder_detect' task, where the detected person is an adult, has a cap, and their shirt is green or white.",
    "Retrieve all Person Slip Detection alerts from 15/03/2025 to 17/03/2025 where a child wore sport shoes that were neither black nor white.",
    "Find any helmet violations recorded.",
    "Retrieve 'Queue Management' events where a person with a bald head is wearing brown lower clothing, from cameras like 'MainEntryCam' or 'ServiceExitCam'.",
    "Are there any high-priority incidents (P1 or P2) related to fire or smoke detection?",
    "Locate all instances of potential fire or smoke detected in the 'warehouse' camera group during the night shift (10 PM to 6 AM) on 21/12/2025.",
    "Retrieve all ANPR events with license plates starting with 'KA01' between 2025-01-01 and 2025-01-31.",
    "Retrieve every ANPR detection.",
    "Show me non-commercial vehicles with license numbers like 'GJ06...' reported between 01/01/2025 and 28/02/2025.",
    "Retrieve all events where a vehicle appears to be moving in the wrong direction.",
    "Get all parking violation alerts from the parking_lot_A camera group.",
    "Retrieve all 'vehicle attribute' (vat) detections for 'Toyota' brand vehicles.",
    "Any incidents of cars moving against designated lanes?",
    "Find vehicles with license plate 'DL5C'.",
    "fns' events with smoke detected on a “red” vehicle.",
    "All 'fns' events with high priority (p1).",
    "Are there any camera tampering alerts from 'office_entry'?",
    "Show me any alerts for too many riders or seatbelt issues during the period March 15 to April 15, 2025.",
    "Find all person slip detections for Abdul or Fatima from camera IDs containing 'office' during November 2025.",
    "I need all instances of loitering involving adults wearing black pants and a white shirt between '2025-01-01' and '2025-01-31'.",
    "Retrieve all intruder alerts for individuals detected from the side orientation carrying a shoulder bag from camera IDs starting with 'main_gate' on '15th March 2025'.",
    "List 'violence_detection' alerts from 'vizag-cam-12' with adult males wearing formal shoes within the first two weeks of June 2025.",
    "Show me events where crowd management detected individuals facing away from the queue.",
    "Find Fatima's person attribute detections.",
    "Find all priority 1 alerts related to PPE violations.",
    "Show me all critical and important crowd estimation events.",
    "Find all 'Crowd Count' events from 2025-06-20 to 2025-06-21 where an adult is wearing 'sneaker' footwear and has 'long_hair', from cameras like 'Cam_001', 'Cam_002', 'Cam_003'.",
    "Were there any reports of abandoned items?",
    "Are there any helmet violation detections?",
    "Get events between '15th March 2025' and '21/03/2025' for a 'male' 'child' person, specifically for 'triple_riding' violations observed from camera group 'B3_west'.",
    "Find all events from camera 'TiharBlockA' related to License Plate Recognition.",
    "Are there any camera tampering alerts?",
    "Find alerts related to vehicles driving in the wrong direction.",
    "Were there any 'helmet violations' where the person's 'jacket' was 'red'?",
    "Get all 'speed violation' events where the license plate 'ocr_result' starts with 'MH' and the detected speed was above '100' km/h, occurring between '2025-07-01' and '2025-07-31'.",
    "Get me all red light violations from camera vizag-cam-12.",
    "Any incidents of cars moving against designated lanes?",
    "Show me any alerts for too many riders or seatbelt issues during the period March 15 to April 15, 2025.",
    "List parking violation alerts for motorcycles or bikes with low speed (under 10) in ParkingLotA.",
    "Find triple riding with red vehicle and commercial registration.",
    "Find red light violations involving commercial vehicles.",
    "Find tailgating events involving vehicles of type suv or wagon.",
    "Show all alerts for 'Woman In Isolation' incidents.",
    "Get 'woman hailing help' incidents captured by the 'office_entry' camera.",
    "Find 'Person Attribute' events where someone is talking or calling and has a thin body type, captured by cameras with IDs containing 'vizag'.",
    "Were there any loitering cases involving a person carrying an umbrella?",
    "Show facial recognition events with individuals holding objects in front.",
    "List facial recognition alerts for people holding items in front of them.",
    "Find 'PPE Violation' events from 'B3_west' where the person has short hair, wears a long-sleeved jacket.",
    "List 'Person Attribute' alerts for bald males with short sleeves recorded by 'B3_west' on 2025-12-31.",
    "Identify abandoned bag alerts from 'vizag-cam*' cameras where a female was carrying luggage beforehand.",
    "Show all alerts for seatbelt violations.",
    "Retrieve crowd estimation data from 'entry_cam_1' on 2025-03-15 during business hours when crowd flow was below 50%.",
    "Get critical alerts from 'intruder_detect' involving adults wearing a cap and a green or white shirt.",
    "Show person slip detection events from 2025-03-15 to 2025-03-17 where a child wore sport shoes not black or white.",
    "List all recorded helmet violations.",
    "Retrieve 'Queue Management' events showing bald individuals wearing brown pants from 'MainEntryCam' or 'ServiceExitCam'.",
    "List high-priority (P1 or P2) fire or smoke detection incidents.",
    "Find potential fire or smoke alerts in the 'warehouse' camera group during the night shift on 2025-12-21.",
    "Get ANPR detections with license plates starting with 'KA01' between 2025-01-01 and 2025-01-31.",
    "Show all ANPR detections.",
    "Find non-commercial vehicle detections with license numbers like 'GJ06...' from 2025-01-01 to 2025-02-28.",
    "List alerts for vehicles moving in the wrong direction.",
    "Show parking violation events from the 'parking_lot_A' camera group.",
    "Get all vehicle attribute detections for 'Toyota' vehicles.",
    "List any cases of cars moving against the designated lane.",
    "Find vehicles detected with the license plate 'DL5C'.",
    "Show 'fns' alerts where smoke was detected on a red vehicle.",
    "List all high-priority (P1) 'fns' events.",
    "Get camera tampering alerts from the 'office_entry' camera.",
    "Find alerts related to triple riding or seatbelt violations between 2025-03-15 and 2025-04-15.",
    "Show slip detection events involving Abdul or Fatima from 'office*' cameras during November 2025.",
    "Find loitering incidents involving adults in black pants and white shirts between 2025-01-01 and 2025-01-31.",
    "Get intruder alerts for people carrying shoulder bags detected from the side by 'main_gate*' cameras on 2025-03-15.",
    "List 'violence_detection' alerts from 'vizag-cam-12' for adult males wearing formal shoes during the first half of June 2025.",
    "Show crowd management events where individuals were facing away from the queue.",
    "Retrieve person attribute detections for Fatima.",
    "List all priority 1 PPE violation alerts.",
    "Find all high and critical priority crowd estimation events.",
    "Show 'Crowd Count' alerts from 2025-06-20 to 2025-06-21 for adults wearing sneakers and having long hair, from 'Cam_001', 'Cam_002', or 'Cam_003'.",
    "List all reports involving abandoned items.",
    "Find all helmet violation alerts.",
    "Get events from 2025-03-15 to 2025-03-21 involving male children violating triple riding rules from 'B3_west'.",
    "Show all License Plate Recognition events from camera 'TiharBlockA'.",
    "Check for any camera tampering alerts.",
    "Find alerts for vehicles driving in the wrong direction.",
    "Were there any helmet violations where the person's jacket was red?",
    "Get speed violation events where license plate starts with 'MH' and speed exceeded 100 km/h between 2025-07-01 and 2025-07-31.",
    "Retrieve all red light violations from 'vizag-cam-12'.",
    "Find any incidents of wrong-way driving.",
    "Get alerts for too many riders or seatbelt violations from 2025-03-15 to 2025-04-15.",
    "List parking violations involving motorcycles or bikes moving under 10 km/h in ParkingLotA.",
    "Find triple riding incidents involving red vehicles with commercial registration.",
    "List red light violations by commercial vehicles.",
    "Get tailgating events involving SUVs or wagons.",
    "Find all ANPR detections with license numbers starting with 'MH12'.",
    "List vehicles with OCR results matching the pattern 'DL8C*' seen near the east gate.",
    "Retrieve all red light violations for cars with 'UP14' plates from April 2025.",
    "Show me over-speeding vehicles with license numbers beginning with 'KA03'.",
    "Get vehicle alerts for commercial trucks with OCR license results containing 'RJ*'.",
    "Were there any bikes with license plates starting with 'TN09' involved in triple riding?",
    "Show license plate detections of black SUVs with 'GJ01' OCR codes.",
    "Find vehicles with OCR outputs matching 'PB1*' that violated stop signs.",
    "Retrieve speed violations with license plates beginning with 'CH*' from the highway_cam group.",
    "Find repeated violations by the same license plate 'MH01AB1234'.",
    "List all fire detection alerts triggered in residential areas after midnight.",
    "Were there any smoke detections from the basement cameras in the last 7 days?",
    "Get high-priority (P1) fire or smoke events where the fire was detected near exit routes.",
    "Show all 'fns' alerts where smoke was detected inside elevators.",
    "Find all smoke detection alerts triggered between 10 PM and 6 AM in the warehouse zone.",
    "Retrieve incidents where both smoke and heat signatures were recorded.",
    "Any fire or smoke alerts raised from cameras located in power supply rooms?",
    "Give me a list of fire alerts captured by 'block_B_*' camera group in February 2025.",
    "Show smoke detection events involving vehicles inside parking lots.",
    "Were any red vehicles involved in fire or smoke alerts this year?",
    "Find 'fns' alerts from 2025 where the temperature at the scene exceeded 80°C.",
    "List all cases of fire or smoke detected in kitchens or food zones.",
    "Find all ANPR detections from today where the license number starts with 'MH12'.",
    "List vehicles detected yesterday with OCR results matching the pattern 'DL8C*' near the east gate.",
    "Retrieve red light violations in the last month for cars with license plates starting with 'UP14'.",
    "Show over-speeding vehicles from last week with license numbers beginning with 'KA03'.",
    "Get vehicle alerts from today for commercial trucks with OCR results containing 'RJ*'.",
    "Were any bikes involved in triple riding yesterday with license plates starting with 'TN09'?",
    "Show today's license plate detections of black SUVs with OCR starting with 'GJ01'.",
    "Find stop sign violations from last week involving vehicles with OCR outputs matching 'PB1*'.",
    "Retrieve speed violations from the highway_cam group over the past 7 days for plates beginning with 'CH*'.",
    "List all repeated violations in the last 30 days by the license plate 'MH01AB1234'.",
    "List all fire detection alerts triggered in residential areas after midnight today.",
    "Were there any smoke detections from basement cameras in the last 7 days?",
    "Get today's high-priority (P1) fire or smoke alerts near exit routes.",
    "Show all smoke alerts detected inside elevators over the past week.",
    "Find smoke detection alerts triggered between 10 PM and 6 AM during the past 3 nights in the warehouse zone.",
    "Retrieve fire/smoke incidents from this week where both smoke and heat signatures were recorded.",
    "Any fire or smoke alerts raised today from cameras in power supply rooms?",
    "List all fire alerts captured yesterday by cameras in the 'block_B_*' group.",
    "Show smoke detections from this month involving vehicles in parking lots.",
    "Were any red vehicles involved in fire or smoke alerts this week?",
    "Find all fire/smoke alerts from this year where temperatures exceeded 80°C.",
    "List all fire or smoke incidents reported in kitchens or food zones over the past 30 days.",
    "lower type jeans",
    "find lower type jeans",
    "sleeve type short sleeves",
    "find sleeve type short sleeves",
    "long hairs",
    "find long hairs",
    "leather_shoes",
    "find leather_shoes",
    "leather_shoes in footwear",
    "find leather_shoes in footwear",
    "casual footwear",
    "find casual footwear",
    "find male with long hairs",
    "male with short hairs",
    "find male with short hairs",
    "customer wearing long trouser",
    "find customer wearing long trouser",
    "male with normal body type",
    "find male with normal body type",
    "sport in footwear",
    "find sport in footwear",
    "find male wearing shirt",
    "find women wearing jeans",
    "find male wearing long trousers",
    "male wearing long trousers",
    "find wearing glasses",
    "find glasses",
    "glasses",
    "find male who are adult",
    "find car MH20GE3537",
    "find erratic crowd on 11 feb",
    "find yashjain",
    "find yash jain",
    "yashjain",
    "find abandoned bags on 15th april",
    "find person intrusion on 19 march",
    "search for camera view obstruction alerts on 27 feb",
    "search for person collapsed on 17 feb",
    "find person collapse",
    "find person collapse_*",
    "search for alerts in which person falls on ground on 17 feb",
    "find cars driving in wrong way on 12 Nov 2024",
    "find cars driving wrong way",
    "find cars in wrong way",
    "find wrong way alerts",
    "find car violating speed limit",
    "find cars of white color",
    "find white cars",
    "find white car",
    "find red car",
    "person wearing glasses",
    "find female wearing glasses",
    "find white cars",
    "find orange sedan",
    "find orange hatchback",
    "find GJ13AB7065",
    "find GJ13AB7065 on 25 April at 12:01 pm",
    "find GJ13AB7065 on 25 April",
    "find woman hailing",
    "find woman hailing help",
    "find Alerts woman hailing help",
    "find alerts woman hailing help in SOurce group stresstesting_qa",
    "find alerts woman in isolation",
    "find crowd estimate",
    "find crowd count alerts label out",
    "find crowd count alerts",
    "find crowd count alerts on 27 feb",
    "find intruder alerts on 19 feb",
    "find yash_jain",
    "find yashjain on 18 Mar 2025",
    "Find tailgating alerts source name Test1"
]
natural_language_queries = natural_language_queries[0:2]
# --- Prompt Template ---
# The {question} part will be replaced by each line from your questions.txt
def create_prompt(question):
    return SCHEMA+f"""
Always use ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`) for timestamps.
For queries involving confidence (e.g., "score greater than 70 percent"), use `score` with operators like `$gt`, `$lt` (e.g., `"$gt": 0.7`).
    Today is 2025-09-24T19:52:42Z use only when the query explicitly mentions to use the current date and time like using words today, last week. Never include or infer the date unless strictly mentioned in the query.
natural_language_query: {question.strip()}

parsed_mongo_query:
  """
def main():
    # Open the output CSV file for writing
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        # 2. Write the updated header row to the CSV
        csv_writer.writerow(["natural_language_queries", "response", "time_taken_seconds"])
        print(f"Created '{OUTPUT_FILE}' and wrote header.")

        total = len(natural_language_queries)
        # Loop directly over your Python list
        for i, question in enumerate(natural_language_queries):
            if not question.strip():  # Skip empty strings
                continue
            
            print(f"Processing question {i+1}/{total}: {question.strip()}")
            
            # Create the prompt for the current question
            prompt_text = create_prompt(question)
            
            # Define the payload for the API request
            payload = {
                "prompt": prompt_text,
                "n_predict": N_PREDICT,
                "temperature": 0.0
            }

            try:
                # 3. Record start time
                start_time = time.monotonic()
                
                # Send the POST request to the Llama server
                response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
                
                # Record end time
                end_time = time.monotonic()
                
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                
                # Calculate the elapsed time
                time_taken = end_time - start_time

                # Extract the content from the JSON response
                response_data = response.json()
                completion = response_data.get('content', 'ERROR: "content" key not found in response').strip()

                # 4. Write the question, response, and time taken to the CSV
                csv_writer.writerow([question.strip(), completion, f"{time_taken:.4f}"])

            except requests.exceptions.RequestException as e:
                print(f"  -> Error processing question: {e}")
                # Add a placeholder for time_taken in case of an error
                csv_writer.writerow([question.strip(), f"ERROR: {e}", "N/A"])
    
    print(f"\n✅ Done! All responses have been saved to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    # Make sure you have the rest of your script defined here, including:
    # API_URL, OUTPUT_FILE, N_PREDICT, natural_language_queries list, and create_prompt function
    main()

