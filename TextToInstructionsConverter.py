import os
from google import genai

# Add you Google API key here
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class TextToInstructionsConverter:
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.acceleration = 0
        self.left = False
        self.right = False
        self.stop = False

    def convert(self, text_of_audio, text_of_scene, current_speed_mps, current_steer_value):
        scenario = f"""
            Analyze the following driving scenario and provide the required speed and steer values.
            You are an autonomous vehicle control system. Your objective is to follow the road while maintaining the target speed.
            
            {text_of_audio}
            {text_of_scene}
            
            Current vehicle state:
            Speed: {current_speed_mps} m/s
            Steer: {current_steer_value}
            
            Target state:
            Target Speed: {current_speed_mps} m/s
            
            Instruction:
            Generate a JSON object with two keys: "speed" (float) and "steer" (float). The "steer" value should be between -1.0 and 1.0.
            """



        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=scenario,
        )

        print(response.text)

        return response.text["speed"], response.text["steer"]
