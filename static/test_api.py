
import os
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError

load_dotenv()

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4.1-mini",
        input="Solve 12 × 8. Reply with the answer and one short step.",
        max_output_tokens=80,
    )

    print("API connection successful!")
    print("AI answer:", response.output_text)

except AuthenticationError:
    print("Authentication failed. Check the API key.")

except RateLimitError as e:
    print("Rate or billing limit error:", str(e))

except Exception as e:
    print("API test failed:", type(e).__name__, str(e))
