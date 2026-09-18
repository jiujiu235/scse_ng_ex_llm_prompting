## Import the necessary modules
import json
import ollama

## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result

## Build your prompt based on the description the user provides 
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.
def build_prompt(description, available_items):
    system_prompt = f"""You are a campus lost-and-found assistant. You must only use the items provided in the lost-and-found database below for matching, and must not use any external information.

Matching rules:
1. Not all details of an item need to match to be considered a possible match.
2. You must strictly return only JSON content, without any additional explanations, markdown markers or other text.
3. The returned JSON must strictly follow the structure below:
{{
    "matches": ["ITEM_ID"],
    "confidence": "CONFIDENCE_LEVEL"
}}
4. The "confidence" field must be exactly one of the following values: LOW, MEDIUM, HIGH.
5. If no matches are found, return an empty list for "matches".

Unclaimed items in the current database:
{json.dumps(available_items, ensure_ascii=False)}
"""
    user_prompt = f"Description of the lost item: {description}\nPlease match possible items according to the above rules."
    return system_prompt, user_prompt
    
## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = ollama.chat(
        model='qwen2',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response['message']['content']

## Logic to parse the response from Qwen and return the result. 
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    text = response_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.endswith('```'):
        text = text[:-3]
    return json.loads(text.strip())
    
## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if 'matches' not in result or 'confidence' not in result:
        return False
    if not isinstance(result['matches'], list):
        return False
    if result['confidence'] not in ('LOW', 'MEDIUM', 'HIGH'):
        return False
    valid_ids = {item['id'] for item in available_items}
    return all(item_id in valid_ids for item_id in result['matches'])

## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
""" 
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================
Describe the item you lost: I lost a black bag somewhere
Searching for possible matches...
MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM
Possible matches:
ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15
Result saved to output/match_result.json
 """
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("MATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    print("Possible matches:")
    if not result['matches']:
        print("No matches found.")
        return
    item_map = {item['id']: item for item in available_items}
    for item_id in result['matches']:
        item = item_map[item_id]
        print(f"ID: {item['id']}")
        print(f"Item: {item['item']}")
        print(f"Color: {item['color']}")
        print(f"Location: {item['location']}")
        print(f"Date found: {item['date']}")
    
## Control center for the entire program.
def main():
    items = load_items('found_items.json')
    unclaimed_items = get_unclaimed_items(items)
    
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    description = input("Describe the item you lost: ")
    print("Searching for possible matches...")
    
    system_prompt, user_prompt = build_prompt(description, unclaimed_items)
    response_text = ask_qwen(system_prompt, user_prompt)
    
    try:
        result = parse_response(response_text)
    except json.JSONDecodeError:
        print("Error: Failed to parse model response.")
        return
    
    if not validate_result(result, unclaimed_items):
        print("Error: Invalid result format or invalid item IDs.")
        return
    
    display_matches(result, unclaimed_items)
    save_path = 'output/match_result.json'
    save_result(result, save_path)
    print(f"Result saved to {save_path}")

if __name__ == "__main__":
    main()
