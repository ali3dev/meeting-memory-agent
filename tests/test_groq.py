import os
from dotenv import load_dotenv
from groq import Groq

# .env file se GROQ_API_KEY aur GROQ_MODEL load karta hai
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key:
    raise SystemExit("GROQ_API_KEY .env mein khali hai.")

client = Groq(api_key=api_key)

# with_raw_response se headers bhi mil jaate hain
raw = client.chat.completions.with_raw_response.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Ek line mein batao: Python kya hai?"
        }
    ],
    max_completion_tokens=512,
    reasoning_effort="low",
    include_reasoning=False,
)
resp = raw.parse()
headers = raw.headers

print("Jawab:", resp.choices[0].message.content)
print("Is call mein tokens use hue:", resp.usage.total_tokens)
print("-" * 40)
print("Model:", resp.model)
print("Choices:", len(resp.choices))

for index, choice in enumerate(resp.choices):
    print(f"\nChoice {index}")
    print("Finish reason:", choice.finish_reason)
    print("Content:", repr(choice.message.content))
    print("Message details:", choice.message.model_dump())

# Ye headers batate hain ke limit mein kitna baaki hai
keys = [
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
]
for k in keys:
    print(f"{k}: {headers.get(k)}")
