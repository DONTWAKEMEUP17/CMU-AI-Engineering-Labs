import json
import os
from typing import Any, Dict
from litellm import completion

# You can replace these with other models as needed but this is the one we suggest for this lab.
MODEL = "openai/gpt-4o-mini"

api_key = os.getenv("OPENAI_API_KEY")


def get_itinerary(destination: str) -> Dict[str, Any]:
    """
    Returns a JSON-like dict with keys:
      - destination
      - price_range
      - ideal_visit_times
      - top_attractions
    """
    # implement litellm call here to generate a structured travel itinerary for the given destination

    # See https://docs.litellm.ai/docs/ for reference.

    response = completion(
        model=MODEL,
        response_format={ "type": "json_object" },
        messages=[
          {"role": "system", 
           "content": """
           You are a You are a travel assistant. Return a JSON object with exactly these fields: destination, price_range, ideal_visit_times, top_attractions.
           - destination: a string representing the travel destination
           - price_range: a string representing the price range for the destination(e.g., "budget", "mid-range", "luxury")
           - ideal_visit_times: a string representing the ideal times to visit the destination (e.g., "spring and fall", "year-round", "summer only")
           - top_attractions: a list of strings representing the top attractions at the destination
            Make sure to return the response in the specified JSON format without any additional text or explanations.
           """},
          {"role": "user", 
           "content": f"Generate a travel itinerary for the destination: {destination}"}
        ]
    )

    data = json.loads(response.choices[0].message.content)

    # Check all required fields exist 
    required_fields = ["destination", "price_range", "ideal_visit_times", "top_attractions"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing field: {field}")


    return data

