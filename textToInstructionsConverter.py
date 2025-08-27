import os
from google import genai

# Add you Google API key here
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class TextToInstructionsConverter:
    def __init__(self):
        self.client = genai.Client(api_key="YOUR_API_KEY_HERE")

    def convert(self, scenario):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=scenario,
        )

        print(response.text)

        return response.text
