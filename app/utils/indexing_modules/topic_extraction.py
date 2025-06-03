import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()  # Uses OPENAI_API_KEY from env

def extract_topics_gpt(text, n_topics=5):
    print("result_text start--------------------------------------")
    prompt = f"""You are a helpful AI Assistant whose only task is to extract important topics, keywords, and entities from given text.
Extract the {n_topics} most important topics, keywords, or entities from this text.

Rules:
1. Follow the strict JSON output as per output Schema.

Output Format:
{{"topics":["string","string","string"]}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-4o" if available
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.2,
        max_tokens=64
    )
    reply = response.choices[0].message.content.strip()
    print(reply)
    # Try parsing the JSON as expected: {"topics": [ ... ]}
    try:
        topics = json.loads(reply)
        if isinstance(topics.get("topics"), list):
            return [str(t).strip() for t in topics["topics"]]
    except Exception as e:
        print("Parsing error:", e)
        # Fallback: try to fix or split string
        reply_clean = reply.replace("'", '"')
        try:
            topics = json.loads(reply_clean)
            if isinstance(topics.get("topics"), list):
                return [str(t).strip() for t in topics["topics"]]
        except Exception:
            # Fallback: comma-split
            topics_str = reply_clean
            if "topics" in topics_str:
                topics_str = topics_str.split("topics")[1]
            return [t.strip().strip('"\'') for t in topics_str.replace('[', '').replace(']', '').split(',') if t.strip()]
    return []