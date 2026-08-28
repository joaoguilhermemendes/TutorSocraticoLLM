import json
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Categories from Paul & Elder's Elements of Thought
# Each one describes a type of reasoning flaw the student might show
CATEGORIES = {
    "assumption": "Student assumes the two remaining doors are equally likely (50/50 fallacy).",
    "inference": "Student draws a conclusion that doesn't follow from the information given.",
    "information": "Student is ignoring or missing a key piece of information (e.g. the host always opens a losing door).",
    "concept": "Student is confused about probability or what 'random' means here.",
    "implication": "Student hasn't thought through what their reasoning implies.",
    "point_of_view": "Student is only seeing the problem from one angle.",
    "question_at_issue": "Student is answering the wrong question.",
    "purpose": "Student hasn't clarified what they are actually trying to figure out.",
}

CLASSIFIER_PROMPT = """You are an expert in Paul & Elder's Critical Thinking Framework.

Analyse the student's latest message in the context of the Monty Hall Problem discussion.
Return ONLY a JSON object with these fields:
{
  "category": "<one of the eight keys below>",
  "rationale": "<one sentence explaining why this category fits>",
  "misconception_flag": <true or false>,
  "misconception_label": "<short label if misconception_flag is true, else null>",
  "rubric_level": <integer 0 to 4>,
  "rubric_label": "<n0|n1|n2|n3|n4>",
  "rubric_rationale": "<one short sentence>"
}

Valid category keys: assumption | inference | information | concept | implication | point_of_view | question_at_issue | purpose

Category definitions:
""" + "\n".join(f'"{k}": {v}' for k, v in CATEGORIES.items()) + """

Known misconceptions to flag:
- "It's 50/50 after one door is opened"
- "Switching doesn't change anything"
- "The remaining doors are equally likely"
- "The host's action is random"
- "My original choice is as good as switching"
- "The host are trying to trick me"

Rubric definition (learning quality):
- N0: no justification
- N1: intuitive but incorrect
- N2: partially correct
- N3: correct answer without causal demonstration
- N4: correct answer with explicit causal demonstration (mentions initial 1/3 and transferred 2/3 logic)

Return ONLY the JSON. No extra text."""

QUESTION_PROMPT = """You are a Socratic tutor helping a student understand the Monty Hall Problem.
You already know what reasoning flaw the student is showing. Generate short Socratic questions.

Rules:
1. Usually ask 2-3 short linked questions in the same message.
2. Keep each question under 20 words.
3. Strong anti-repetition: do not repeat wording or structure from this message or recent tutor turns.
4. NEVER give the answer or say what the probability is.
5. Base the question(s) on the student's exact last claim and the diagnosed category.
6. Make it direct: ask about a concrete part of what the student just said.
7. If progress_signal is "progressing", add a short acknowledgement (max 6 words) and then move one step deeper.
8. If progress_signal is "stuck", avoid old prompts; ask a sharper contrast tied to the student's latest claim.
9. If misconception_flag is true, expose the flaw without naming it.
10. Prefer open questions that invite explanation; avoid yes/no unless confirming a key structural idea.
11. Use very simple everyday words for a general audience.
12. Avoid jargon, abstract phrasing, and long sentence structures.
13. Return ONLY a JSON object: { "question": "<your question(s) here>" }"""


def classify_and_question(user_message, history, progress_signal="neutral", session_summary=None, context_window=12):
    #build a short summary of the conversation for context
    recent = history[-context_window:]
    history_text = ""
    if session_summary:
        history_text += f"Session summary:\n{session_summary}\n\n"
    for msg in recent:
        role = "Student" if msg["role"] == "user" else "Tutor"
        history_text += f"{role}: {msg['content']}\n"

    # call 1 - classify the student's reasoning
    classifier_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Conversation:\n{history_text}\nStudent's latest message: \"{user_message}\"\n\nClassify and return JSON."}
        ],
        temperature=0.2,
        max_tokens=300,
    )

    raw = classifier_response.choices[0].message.content
    # Strip markdown fences if the model added them
    raw = raw.replace("```json", "").replace("```", "").strip()
    classification = json.loads(raw)

    # fallback if the model returns an invalid category
    if classification.get("category") not in CATEGORIES:
        classification["category"] = "assumption"

    rubric_level = classification.get("rubric_level")
    if not isinstance(rubric_level, int) or rubric_level < 0 or rubric_level > 4:
        rubric_level = 0

    rubric_label = str(classification.get("rubric_label", "")).lower()
    if rubric_label not in {"n0", "n1", "n2", "n3", "n4"}:
        rubric_label = f"n{rubric_level}"

    rubric_rationale = classification.get("rubric_rationale", "")

    # call 2 - generate the Socratic question for that category
    category = classification["category"]
    rationale = classification.get("rationale", "")
    misconception = classification.get("misconception_flag", False)
    misc_label = classification.get("misconception_label", None)

    question_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": QUESTION_PROMPT},
            {"role": "user", "content": (
                f"Conversation:\n{history_text}\n"
                f"Student's latest message: \"{user_message}\"\n"
                f"Category: {category}\n"
                f"Definition: {CATEGORIES[category]}\n"
                f"Rationale: {rationale}\n"
                f"Progress signal: {progress_signal}\n"
                f"Misconception: {misconception}" + (f" ({misc_label})" if misc_label else "") +
                "\n\nGenerate the Socratic question. Return JSON only."
            )}
        ],
        temperature=0.7,
        max_tokens=150,
    )

    raw_q = question_response.choices[0].message.content
    raw_q = raw_q.replace("```json", "").replace("```", "").strip()
    question_data = json.loads(raw_q)

    return {
        "question": question_data.get("question", "[error generating question]"),
        "category": category,
        "rationale": rationale,
        "misconception_flag": misconception,
        "misconception_label": misc_label,
        "rubric_level": rubric_level,
        "rubric_label": rubric_label,
        "rubric_rationale": rubric_rationale,
    }


# directly run to check if the classifier is working (quick test)
if __name__ == "__main__":
    test_history = [
        {"role": "assistant", "content": (
            "Imagine you're on a game show. There are three doors: behind one is a car, "
            "behind the other two are goats. You pick Door 1. The host opens Door 3 to reveal "
            "a goat, then asks: switch to Door 2 or stay with Door 1? What would you do — switch or stay?"
        )}
    ]
    test_message = "I'd stay. There are two doors left so it's 50/50 now, switching doesn't help."

    print(f"Student: {test_message}\n")
    result = classify_and_question(test_message, test_history)
    print(f"Category    : {result['category']}")
    print(f"Rationale   : {result['rationale']}")
    print(f"Misconception: {result['misconception_flag']} — {result['misconception_label']}")
    print(f"Question    : {result['question']}")
