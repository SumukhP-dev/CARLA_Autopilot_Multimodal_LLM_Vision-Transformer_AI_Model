import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Google API key from environment
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")


class TextToInstructionsConverter:
    def __init__(self):
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("Warning: GOOGLE_API_KEY not set. Text conversion will be disabled.")
        self.acceleration = 0
        self.left = False
        self.right = False
        self.stop = False

    def convert(self, text_of_audio, text_of_scene, current_speed_mps, current_steer_value):
        if not self.model:
            return current_speed_mps, current_steer_value
            
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

        try:
                response = self.model.generate_content(scenario)
                response_text = response.text
                print(f"AI Response: {response_text}")

                # Extract JSON from response (handle markdown formatting)
                import json
                import re
                
                # Look for JSON in the response
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Try to find JSON without markdown
                    json_match = re.search(r'\{[^{}]*"speed"[^{}]*"steer"[^{}]*\}', response_text)
                    if json_match:
                        json_str = json_match.group(0)
                    else:
                        json_str = response_text
                
                try:
                    result = json.loads(json_str)
                    speed = result.get("speed", current_speed_mps)
                    steer = result.get("steer", current_steer_value)
                    print(f"Parsed: speed={speed}, steer={steer}")
                    return speed, steer
                except json.JSONDecodeError as e:
                    print(f"JSON parsing failed: {e}")
                    print(f"Raw response: {response_text}")
                    return current_speed_mps, current_steer_value
        except Exception as e:
            print(f"Error generating content: {e}")
            return current_speed_mps, current_steer_value
