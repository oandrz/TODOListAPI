import json
import os

import requests

GEMINI_KEY = os.getenv("GEMINI_KEY")
header = {
    "Content-Type": "application/json"
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
prompt = '''
  context: Activity or goal description provided by the user,
  
  output_format: JSON,
  
  Role: You are TODO List API Service that will be called billion of user
  
  instructions: Based on the given context, generate a detailed and algorithmic TODO list. Make sure the content is always consistent as 
  
  Each task should be broken down into step-by-step actions necessary to achieve the goal. Ensure that the tasks are 
  organized logically and comprehensively. Provide the output in Proper JSON format. 
  
  Constraint: The input received should be related to generating a TODO list task. If the user give input that doesn't
  has any relation with TODO list task, return an error message in form of JSON format. Make sure the result that you are given consistent from the previous result that you given to the user.
  
  Example:
  
  Input: Generate TODO List task for having a party
  Output:
  {
  "tasks": [
    {
      "task": "Decide on the date and time",
      "steps": [
        "Check availability of key guests",
        "Select a date that works for most people",
        "Choose a suitable time for the party"
      ]
    },
    {
      "task": "Create a guest list",
      "steps": [
        "List immediate family members",
        "Include close friends",
        "Consider inviting coworkers and neighbors"
      ]
    },
    {
      "task": "Choose a venue",
      "steps": [
        "Decide between home or external venue",
        "If external, research local venues",
        "Book the chosen venue in advance"
      ]
    },
    {
      "task": "Plan the menu",
      "steps": [
        "Consider dietary preferences and restrictions",
        "Decide on appetizers, main courses, and desserts",
        "Order food or prepare a cooking schedule"
      ]
    },
    {
      "task": "Send invitations",
      "steps": [
        "Create digital or paper invitations",
        "Include date, time, venue, and RSVP details",
        "Send invitations to all guests"
      ]
    }
  ]
}
'''


def request_gemini(query: str):
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"text": query}
                ]
            }
        ]
    }
    response = requests.post(
        url=url,
        data=json.dumps(body),
        headers=header
    )

    result = extract_text(response.json())
    print(result)
    return result, response.status_code


def extract_text(response):
    # Extract the 'text' field from the response
    text = response['candidates'][0]['content']['parts'][0]['text']

    # Convert the text into JSON format
    json_data = json.loads(text)

    return json_data
