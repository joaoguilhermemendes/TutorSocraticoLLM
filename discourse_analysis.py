import json
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Patterns the analysis can identify across the full session
PATTERNS = {
    "progression": "Student showed consistent movement toward understanding, building on each exchange.",
    "resistance": "Student repeatedly pushed back or dismissed the tutor's questions without engaging.",
    "loop": "Student kept returning to the same misconception even after it was challenged.",
    "stagnation": "Student showed no meaningful movement — neither progressing nor actively resisting.",
    "breakthrough": "Student showed a sudden shift from a misconception to correct understanding.",
}

ANALYSIS_PROMPT = """You are an educational researcher analysing a Socratic tutoring session on the Monty Hall Problem.

You will receive:
1. The full conversation transcript
2. A per-turn classification log showing the student's reasoning category at each turn

Your task: identify the dominant discourse pattern across the FULL session and return ONLY this JSON:
{
  "pattern": "<one of the five keys below>",
  "rationale": "<two or three sentences explaining why this pattern fits, citing specific turns>",
  "turning_point": "<describe the moment the student's reasoning shifted, or null if no shift occurred>",
  "dominant_category": "<the Paul & Elder category that appeared most across the session>",
  "misconception_resolved": <true or false>
}

Valid pattern keys: progression | resistance | loop | stagnation | breakthrough

Pattern definitions:
""" + "\n".join(f'"{k}": {v}' for k, v in PATTERNS.items()) + """

Return ONLY the JSON. No extra text."""


def analyze_session(history, classification_log):
    # build the full transcript as a readable string
    transcript = ""
    for msg in history:
        role = "Student" if msg["role"] == "user" else "Tutor"
        transcript += f"{role}: {msg['content']}\n"

    # build the classification log as a readable string
    log_text = ""
    for entry in classification_log:
        flag = f" ⚠ {entry['misconception_label']}" if entry["misconception_flag"] else ""
        log_text += f"Turn {entry['turn']}: {entry['category']}{flag} — {entry['rationale']}\n"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": (
                f"Full transcript:\n{transcript}\n"
                f"Classification log:\n{log_text}\n\n"
                "Analyse the session and return JSON."
            )}
        ],
        temperature=0.2,
        max_tokens=400,
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    analysis = json.loads(raw)

    # fallback if the model returns an invalid pattern
    if analysis.get("pattern") not in PATTERNS:
        analysis["pattern"] = "stagnation"

    return analysis


# run directly (test)
if __name__ == "__main__":
    test_history = [
        {"role": "assistant", "content": "There are three doors. Behind one is a car, behind the others are goats. You pick Door 1. The host opens Door 3 revealing a goat. Do you switch or stay?"},
        {"role": "user", "content": "I'd stay. It's 50/50 now."},
        {"role": "assistant", "content": "Why do you think the two remaining doors have equal probability?"},
        {"role": "user", "content": "Because there are two doors and one has the car. Simple."},
        {"role": "assistant", "content": "Did the host choose which door to open randomly?"},
        {"role": "user", "content": "Oh wait — the host always knows where the car is, right? So his choice tells me something."},
        {"role": "assistant", "content": "What does his choice tell you about your original door versus the other one?"},
        {"role": "user", "content": "My door still has 1/3 chance. The other door now has 2/3. I should switch!"},
    ]
    test_log = [
        {"turn": 1, "category": "assumption", "rationale": "Student assumes 50/50 after door is opened.", "misconception_flag": True, "misconception_label": "50/50 fallacy"},
        {"turn": 2, "category": "inference", "rationale": "Student draws conclusion without considering host's knowledge.", "misconception_flag": True, "misconception_label": "50/50 fallacy"},
        {"turn": 3, "category": "information", "rationale": "Student starts to consider the host's knowledge.", "misconception_flag": False, "misconception_label": None},
        {"turn": 4, "category": "implication", "rationale": "Student derives correct implication from host's action.", "misconception_flag": False, "misconception_label": None},
    ]

    result = analyze_session(test_history, test_log)
    print(f"Pattern             : {result['pattern']}")
    print(f"Rationale           : {result['rationale']}")
    print(f"Turning point       : {result['turning_point']}")
    print(f"Dominant category   : {result['dominant_category']}")
    print(f"Misconception resolved: {result['misconception_resolved']}")