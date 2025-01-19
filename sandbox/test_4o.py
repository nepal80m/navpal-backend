import os
from openai import OpenAI

from dotenv import load_dotenv


def generate_text(prompt):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # Load API key from environment variable
    if not api_key:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
    print("API Key found.")

    client = OpenAI()

    # Configure the OpenAI client
    try:
        # Use the ChatCompletion API for more advanced interactions
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,      # Adjust as needed
        temperature=0.7,     # Adjust for creativity
        n=1,                 # Number of responses to generate
        stop=None            # Define stop sequences if needed
        )

        # Extract and return the generated text
        generated_text = response.choices[0].message.content.strip()
        return generated_text
    except Exception as e:
        # Handle OpenAI API errors
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    prompt = "Explain how AI works in a sentence in roman nepali."
    result = generate_text(prompt)
    if result:
        print("Generated Text:")
        print(result)
