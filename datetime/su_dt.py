import json
from sutime import SUTime
from datetime import datetime,timedelta, timezone
import re

REFERENCE_DATE_UTC=datetime.now(timezone.utc)
def convert_dates_in_json(json_string, reference_date=REFERENCE_DATE_UTC):
    """
    Parses a JSON string from sutime, converting all found dates and
    durations into the ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
    """
    try:
        date_entries = json.loads(json_string)
    except json.JSONDecodeError:
        return []

    converted_dates = []
    # A map for SUTime's time-of-day codes
    time_of_day_map = {'TMO': '08:00:00', 'TAF': '14:00:00', 'TEV': '18:00:00', 'TNI': '21:00:00'}

    for entry in date_entries:
        date_str = entry.get('value')
        # print(date_str)
        if not date_str:
            continue

        date_obj = None

        # 1. Check for Duration format (e.g., "P1W")
        if date_str.startswith('P'):
            # This simple parser handles Weeks (W) and Days (D)
            match = re.match(r'P(\d+)([WD])', date_str)
            if match:
                value, unit = int(match.group(1)), match.group(2)
                delta = timedelta(weeks=value) if unit == 'W' else timedelta(days=value)
                date_obj = reference_date - delta

        # 2. Check for SUTime Time-of-Day format (e.g., "...TNI")
        elif len(date_str) > 11 and date_str[10] == 'T':
            # print("here")
            try:
                date_part = date_str[:10]
                time_specifier = date_str[10:]
                # print(time_specifier)
                time_part = time_of_day_map.get(time_specifier)
                # print(time_part)
                if time_part:
    
                    date_obj = datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S')
            except (ValueError, IndexError):
                pass # Fall through to next check

        # 3. If not parsed yet, try standard formats
        if not date_obj:
            try:
                # Standard Date (YYYY-MM-DD)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    # ISO Week Date (YYYY-Www)
                    date_obj = datetime.strptime(f"{date_str}-1", "%G-W%V-%u")
                except ValueError:
                    continue # Skip if no format matches

        # If we successfully created a date object, format it and add to the list
        if date_obj:
            if date_obj.tzinfo is None:
                date_obj = date_obj.replace(tzinfo=timezone.utc)
            iso_format_date = date_obj.strftime('%Y-%m-%dT%H:%M:%SZ')
            converted_dates.append(iso_format_date)

    return converted_dates


relative_date_queries = [
    "Find all events of last 3 days.",
    "Show me incidents that happened in the past week.",
    "List alerts generated over the last 2 hours.",
    "Retrieve logs from the previous 10 minutes.",
    "Get data recorded within the past month.",
    "Were there any violations last 24 hours?",
    "Show entries from earlier today.",
    "Get all activity from this morning.",
    "What happened yesterday evening?",
    "Fetch alerts between 5th April and 10 April",
    "Get incidents recorded last night.",
    "Get incidents from today so far.",
    "Find anything recorded since last Monday.",
]

if __name__ == '__main__':
    for test_case in relative_date_queries:
        sutime = SUTime(mark_time_ranges=True, include_range=True)
        print("Query-",test_case)
        print(json.dumps(sutime.parse(test_case), sort_keys=True, indent=4))
        print("Extracted date:",convert_dates_in_json(json.dumps(sutime.parse(test_case), sort_keys=True, indent=4)))