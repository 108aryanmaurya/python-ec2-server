import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()  # Uses OPENAI_API_KEY from env

def generate_similar_questions_gpt(query, n_questions=4):
    prompt = f"""You are a helpful AI Assistant whose task is to generate similar questions.

Given a user question, generate {n_questions} new questions that are similar in intent, topic, and structure.

Rules:
1. Output ONLY in strict JSON format as per schema.
2. Do NOT include the original question in your outputs; all questions should be newly generated.
3. Avoid duplicating the same question with minor changes.
4. All questions should be clear, concise, and grammatically correct.

Output Format:
{{"question":["q1","q2","q3","q4"]}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-4o" if available
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.4,
        max_tokens=128
    )
    reply = response.choices[0].message.content.strip()
    print("RAW RESPONSE:", reply)
    # Try parsing the JSON as expected: {"question": [ ... ]}
    try:
        questions = json.loads(reply)
        if isinstance(questions.get("question"), list):
            return [str(q).strip() for q in questions["question"]]
    except Exception as e:
        print("Parsing error:", e)
        reply_clean = reply.replace("'", '"')
        try:
            questions = json.loads(reply_clean)
            if isinstance(questions.get("question"), list):
                return [str(q).strip() for q in questions["question"]]
        except Exception:
            # Fallback: comma-split
            questions_str = reply_clean
            if "question" in questions_str:
                questions_str = questions_str.split("question")[1]
            return [q.strip().strip('"\'') for q in questions_str.replace('[', '').replace(']', '').split(',') if q.strip()]
    return []
