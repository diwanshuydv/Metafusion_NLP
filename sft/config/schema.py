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
