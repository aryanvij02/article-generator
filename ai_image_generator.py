import os
import time
from openai import OpenAI
import requests
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

def check_image_size(image_url, max_size_mb=4):
    response = requests.get(image_url)
    image_size = len(response.content) / (1024 * 1024)  # Convert to MB
    return image_size <= max_size_mb

def sanitize_prompt(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant that helps create safe and appropriate image prompts."},
            {"role": "user", "content": f"Please rewrite the following image prompt to ensure it doesn't violate any content policies. Remove any potentially offensive or controversial elements, and focus on creating a safe, general representation: '{prompt}'"}
        ]
    )
    return response.choices[0].message.content.strip()

def generate_image(prompt, max_retries=5, retry_delay=3, max_size_mb=4):
    client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))
    image_prompt = f"Create a symbolic representation of {prompt} without using any text or specific individuals"

    for attempt in range(max_retries):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            
            if check_image_size(image_url, max_size_mb):
                return image_url
            else:
                print(f"Generated image is too large. Retrying. Attempt {attempt + 1}/{max_retries}")
                
        except Exception as e:
            error_message = str(e)
            print(f"An error occurred: {error_message}. Retrying. Attempt {attempt + 1}/{max_retries}")
            
            if "content_policy_violation" in error_message.lower():
                print("Content policy violation detected. Sanitizing prompt...")
                image_prompt = sanitize_prompt(image_prompt)
                print(f"Sanitized prompt: {image_prompt}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)

    print(f"Failed to generate a suitable image after {max_retries} attempts.")
    return None

if __name__ == "__main__":
    url = generate_image("Social Media Icons")
    print(url)
