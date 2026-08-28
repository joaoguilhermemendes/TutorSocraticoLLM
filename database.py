import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY"),
)


def save_participant(participant):
    # Insert a new participant row when they finish screening
    data = {
        "id":               participant["id"],
        "group_name":       participant["group"],
        "age":              participant["screening"].get("age"),
        "education":        participant["screening"].get("education"),
        "prior_knowledge":  participant["screening"].get("prior_knowledge"),
        "prob_familiarity": participant["screening"].get("probability_familiarity"),
    }
    supabase.table("participants").insert(data).execute()


def save_turn(participant_id, turn_number, student_message, tutor_reply, meta):
    # Insert one row per conversation turn
    data = {
        "participant_id":     participant_id,
        "turn_number":        turn_number,
        "student_message":    student_message,
        "tutor_reply":        tutor_reply,
        "category":           meta.get("category"),
        "rationale":          meta.get("rationale"),
        "misconception_flag": meta.get("misconception_flag", False),
        "misconception_label": meta.get("misconception_label"),
    }
    if "rubric_level" in meta:
        data["rubric_level"] = meta.get("rubric_level")
    if "rubric_label" in meta:
        data["rubric_label"] = meta.get("rubric_label")
    if "rubric_rationale" in meta:
        data["rubric_rationale"] = meta.get("rubric_rationale")
    supabase.table("session_turns").insert(data).execute()


def save_analysis(participant_id, analysis):
    # Insert the discourse analysis result at the end of the session
    data = {
        "participant_id":        participant_id,
        "pattern":               analysis.get("pattern"),
        "rationale":             analysis.get("rationale"),
        "turning_point":         analysis.get("turning_point"),
        "dominant_category":     analysis.get("dominant_category"),
        "misconception_resolved": analysis.get("misconception_resolved"),
    }
    supabase.table("session_analysis").insert(data).execute()


def mark_completed(participant_id):
    supabase.table("participants").update({"completed": True}).eq("id", participant_id).execute()


def save_evaluation(participant_id, form_data):
    # Insert questionnaire responses
    data = {
        "participant_id":   participant_id,
        "q1_understanding": int(form_data.get("q1_understanding", 0)),
        "q2_autonomy":      int(form_data.get("q2_autonomy", 0)),
        "q3_engagement":    int(form_data.get("q3_engagement", 0)),
        "q4_frustration":   int(form_data.get("q4_frustration", 0)),
        "q5_adaptation":    int(form_data.get("q5_adaptation", 0)),
        "q6_open":          form_data.get("q6_open", ""),
    }
    supabase.table("evaluation").insert(data).execute()
