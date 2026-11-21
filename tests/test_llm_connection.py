
from meeting_memory_agent.generation.client import (
    create_llm_client,
    get_model_name,
)


def main():
    client = create_llm_client()
    model = get_model_name()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Reply with exactly: CONNECTION_SUCCESS",
            },
        ],
        temperature=0,
        max_tokens=30,
    )

    print("Model:", model)
    print("Response:", response.choices[0].message.content)
    print("Usage:", response.usage)


if __name__ == "__main__":
    main()
