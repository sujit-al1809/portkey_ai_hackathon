"""
Simple Portkey Test - Python Version
"""
from portkey_ai import Portkey

# Initialize Portkey client
portkey = Portkey(
    api_key="5N/MPI9SkW4t6zf7lzkKsQ1JpADV"
)

# Make a request - Use @provider/model format
response = portkey.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is Portkey?"}
    ],
    model="@openai/gpt-4o-mini",  # Use @provider/model format
    max_tokens=512
)

# Print the response
print(response.choices[0].message.content)
