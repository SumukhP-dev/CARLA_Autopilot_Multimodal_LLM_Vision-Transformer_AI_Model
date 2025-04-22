import os

# Add you Grok API key here
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

import openai

responses = []

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

scenario = ()
completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content":
        }
    ],
    model="",
)

response = completion.choices[0].message.content

