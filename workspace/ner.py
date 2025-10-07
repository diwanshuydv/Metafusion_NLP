import pandas as pd 
import spacy 
import requests 
from bs4 import BeautifulSoup
import time
nlp = spacy.load("en_core_web_lg")

def add_person_to_mongo_query(mongo_query, natural_language_query):
    doc = nlp(natural_language_query)
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if persons:
        # Add person names to MongoDB query using $in operator for multiple names
        mongo_query['response.event.blobs.match_id'] = persons[0]
    return mongo_query
nl="Was Abdul identified in any surveillance footage?"
mongo_dict={
     "response.event.c_timestamp": {
    "$gte": "2025-06-27T09:15:59Z",
    "$lt": "2025-06-28T09:15:59Z"
  },
  "response.event.blobs.attribs.upper_color": "blue",
  "response.event.blobs.attribs.upper_type": "tshirt",
  "response.event.blobs.attribs.footwear": "sport"     # Faulty: extra top-level field
}
#print(add_person_to_mongo_query(mongo_dict,nl))
