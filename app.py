import os
import uuid
import random
import re
import json
from groq import Groq
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from classifier import classify_and_question
from discourse_analysis import analyze_session
from database import save_participant, save_turn, save_analysis, mark_completed, save_evaluation
load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret"))
templates = Jinja2Templates(directory="templates")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# In-memory store for the active session- persisted to Supabase at each step
participants = {}

LANGUAGE_NAMES = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
}

EDUCATION_MAP = {
    "ensino_medio": "high_school",
    "superior_incompleto": "undergraduate_incomplete",
    "superior_completo": "undergraduate_complete",
    "pos_graduacao": "postgraduate",
}

UI_TEXT = {
    "pt": {
        "language_title": "Escolha seu idioma",
        "language_subtitle": "Selecione o idioma antes de iniciar a pesquisa.",
        "language_label": "Idioma",
        "language_continue": "Continuar",
        "language_portuguese": "Português (padrão)",
        "language_english": "English",
        "language_spanish": "Español",
        "consent_label": "Pesquisa Acadêmica · 2026",
        "consent_title": "Termo de Consentimento Livre e Esclarecido",
        "consent_p1": "Você está sendo convidado(a) a participar de uma pesquisa sobre aprendizagem de probabilidade com apoio de inteligência artificial",
        "consent_p2": "O que você vai fazer: responder algumas perguntas sobre seu perfil e interagir com um sistema de tutoria sobre o Problema de Monty Hall - um problema clássico de probabilidade. Ao final, pediremos que responda um breve questionário.",
        "consent_p3": "Duração estimada: 10 a 15 minutos.",
        "consent_p4": "Riscos: não há riscos previstos além do tempo despendido. Sua participação é completamente voluntária e você pode desistir a qualquer momento.",
        "consent_p5": "Dados: suas respostas serão armazenadas de forma anônima e utilizadas exclusivamente para fins de pesquisa acadêmica. Nenhum dado pessoal identificável será divulgado.",
        "consent_agree": "Li e compreendi as informações acima. Concordo em participar desta pesquisa voluntariamente e sei que posso desistir a qualquer momento sem nenhum prejuízo.",
        "consent_button": "Concordar e continuar",
        "screening_stage": "Etapa 1 de 3 · Perfil do participante",
        "screening_title": "Algumas perguntas antes de começar",
        "screening_subtitle": "Suas respostas são anônimas e serão usadas apenas para caracterizar a amostra da pesquisa.",
        "screening_age": "Idade",
        "screening_age_placeholder": "Ex: 22",
        "screening_education": "Nível de escolaridade",
        "screening_education_select": "Selecione",
        "education_high_school": "Ensino médio completo",
        "education_undergrad_incomplete": "Ensino superior incompleto",
        "education_undergrad_complete": "Ensino superior completo",
        "education_postgraduate": "Pós-graduação",
        "screening_prior": "Você já conhecia o Problema de Monty Hall antes desta pesquisa?",
        "screening_prior_no": "Não, nunca ouvi falar",
        "screening_prior_heard": "Já ouvi o nome, mas não conheço bem",
        "screening_prior_yes": "Sim, conheço o problema e a solução",
        "screening_probability": "Como você avalia seu conhecimento em probabilidade e estatística?",
        "screening_probability_low": "Nenhum",
        "screening_probability_high": "Muito alto",
        "screening_continue": "Continuar",
        "screening_submitting": "Enviando...",
        "screening_leave_warning": "Envio em andamento. Se você sair agora, pode perder esta etapa.",
        "session_title": "Problema de Monty Hall",
        "session_stage": "Etapa 2 de 3 · Sessão",
        "session_done": "Você chegou ao fim da sessão. Clique para responder o questionário final.",
        "session_done_cta": "Ir para o questionário",
        "session_placeholder": "Digite sua resposta aqui...",
        "session_send": "Enviar",
        "session_you": "Você",
        "session_refresh_blocked": "Atualização da página desativada durante a sessão.",
        "session_leave_warning": "Se você sair da sessão agora, pode perder o contexto visível da conversa.",
        "evaluation_stage": "Etapa 3 de 3 · Questionário final",
        "evaluation_title": "Avaliação pós-sessão",
        "evaluation_subtitle": "Responda com base na sua experiência durante a sessão. Não há respostas certas ou erradas.",
        "evaluation_q1": "Após a sessão, sinto que compreendo por que a estratégia de trocar de porta aumenta as chances de ganhar.",
        "evaluation_q2": "Sinto que cheguei à resposta por conta própria, sem que ela fosse dada diretamente.",
        "evaluation_q3": "As perguntas feitas durante a sessão me ajudaram a pensar mais profundamente sobre o problema.",
        "evaluation_q4": "Em algum momento senti frustração por não receber uma resposta direta.",
        "evaluation_q5": "Percebi que o tutor adaptava suas perguntas com base no que eu respondia.",
        "evaluation_q6": "Descreva brevemente o que mudou no seu entendimento sobre o problema durante a sessão (ou o que ficou confuso).",
        "evaluation_placeholder": "Sua resposta...",
        "evaluation_likert_disagree": "Discordo totalmente",
        "evaluation_likert_agree": "Concordo totalmente",
        "evaluation_send": "Enviar respostas",
        "evaluation_done_label": "Pesquisa concluída",
        "evaluation_done_title": "Obrigado pela sua participação.",
        "evaluation_done_body": "Suas respostas foram registradas com sucesso. Os resultados desta pesquisa serão utilizados exclusivamente para fins acadêmicos.",
    },
    "en": {
        "language_title": "Choose your language",
        "language_subtitle": "Select the language before starting the study.",
        "language_label": "Language",
        "language_continue": "Continue",
        "language_portuguese": "Português (default)",
        "language_english": "English",
        "language_spanish": "Español",
        "consent_label": "Academic Study · 2026",
        "consent_title": "Informed Consent Form",
        "consent_p1": "You are invited to participate in a study on learning probability with AI support, conducted as part of an undergraduate research project.",
        "consent_p2": "What you will do: answer a few profile questions and interact with a tutoring system about the Monty Hall Problem, a classic probability task. At the end, you will complete a short questionnaire.",
        "consent_p3": "Estimated duration: 10 to 15 minutes.",
        "consent_p4": "Risks: there are no expected risks beyond time spent. Participation is fully voluntary and you may withdraw at any time.",
        "consent_p5": "Data: your responses will be stored anonymously and used exclusively for academic research. No personally identifiable data will be disclosed.",
        "consent_agree": "I have read and understood the information above. I agree to participate voluntarily and understand I can withdraw at any time without penalty.",
        "consent_button": "Agree and continue",
        "screening_stage": "Step 1 of 3 · Participant profile",
        "screening_title": "A few questions before we start",
        "screening_subtitle": "Your answers are anonymous and will be used only to characterize the study sample.",
        "screening_age": "Age",
        "screening_age_placeholder": "E.g.: 22",
        "screening_education": "Education level",
        "screening_education_select": "Select",
        "education_high_school": "Completed high school",
        "education_undergrad_incomplete": "Incomplete undergraduate education",
        "education_undergrad_complete": "Completed undergraduate education",
        "education_postgraduate": "Postgraduate",
        "screening_prior": "Did you already know the Monty Hall Problem before this study?",
        "screening_prior_no": "No, I had never heard of it",
        "screening_prior_heard": "I heard the name, but I do not know it well",
        "screening_prior_yes": "Yes, I know the problem and the solution",
        "screening_probability": "How do you rate your knowledge of probability and statistics?",
        "screening_probability_low": "None",
        "screening_probability_high": "Very high",
        "screening_continue": "Continue",
        "screening_submitting": "Submitting...",
        "screening_leave_warning": "Submission in progress. If you leave now, this step may be lost.",
        "session_title": "Monty Hall Problem",
        "session_stage": "Step 2 of 3 · Session",
        "session_done": "You reached the end of the session. Click to complete the final questionnaire.",
        "session_done_cta": "Go to questionnaire",
        "session_placeholder": "Type your response here...",
        "session_send": "Send",
        "session_you": "You",
        "session_refresh_blocked": "Page refresh is disabled during the session.",
        "session_leave_warning": "If you leave now, you may lose the visible conversation context.",
        "evaluation_stage": "Step 3 of 3 · Final questionnaire",
        "evaluation_title": "Post-session evaluation",
        "evaluation_subtitle": "Answer based on your session experience. There are no right or wrong answers.",
        "evaluation_q1": "After the session, I feel I understand why switching doors increases the chance of winning.",
        "evaluation_q2": "I feel I reached the answer on my own, without it being given directly.",
        "evaluation_q3": "The questions during the session helped me think more deeply about the problem.",
        "evaluation_q4": "At some point, I felt frustrated for not receiving a direct answer.",
        "evaluation_q5": "I noticed the tutor adapted questions based on what I answered.",
        "evaluation_q6": "Briefly describe what changed in your understanding during the session (or what remained confusing).",
        "evaluation_placeholder": "Your response...",
        "evaluation_likert_disagree": "Strongly disagree",
        "evaluation_likert_agree": "Strongly agree",
        "evaluation_send": "Submit responses",
        "evaluation_done_label": "Study completed",
        "evaluation_done_title": "Thank you for your participation.",
        "evaluation_done_body": "Your responses were recorded successfully. The results of this study will be used exclusively for academic purposes.",
    },
    "es": {
        "language_title": "Elige tu idioma",
        "language_subtitle": "Selecciona el idioma antes de iniciar la investigación.",
        "language_label": "Idioma",
        "language_continue": "Continuar",
        "language_portuguese": "Português (predeterminado)",
        "language_english": "English",
        "language_spanish": "Español",
        "consent_label": "Investigación Académica · 2026",
        "consent_title": "Consentimiento informado",
        "consent_p1": "Se te invita a participar en una investigación sobre aprendizaje de probabilidad con apoyo de IA.",
        "consent_p2": "Qué harás: responder algunas preguntas sobre tu perfil e interactuar con un sistema de tutoría sobre el Problema de Monty Hall, un problema clásico de probabilidad. Al final, responderás un breve cuestionario.",
        "consent_p3": "Duración estimada: 10 a 15 minutos.",
        "consent_p4": "Riesgos: no hay riesgos previstos más allá del tiempo dedicado. La participación es totalmente voluntaria y puedes retirarte en cualquier momento.",
        "consent_p5": "Datos: tus respuestas se almacenarán de forma anónima y se usarán exclusivamente con fines académicos. No se divulgarán datos personales identificables.",
        "consent_agree": "Leí y comprendí la información anterior. Acepto participar voluntariamente y sé que puedo retirarme en cualquier momento sin ningún perjuicio.",
        "consent_button": "Aceptar y continuar",
        "screening_stage": "Etapa 1 de 3 · Perfil del participante",
        "screening_title": "Algunas preguntas antes de comenzar",
        "screening_subtitle": "Tus respuestas son anónimas y se usarán solo para caracterizar la muestra del estudio.",
        "screening_age": "Edad",
        "screening_age_placeholder": "Ej.: 22",
        "screening_education": "Nivel educativo",
        "screening_education_select": "Selecciona",
        "education_high_school": "Secundaria completa",
        "education_undergrad_incomplete": "Educación superior incompleta",
        "education_undergrad_complete": "Educación superior completa",
        "education_postgraduate": "Posgrado",
        "screening_prior": "¿Ya conocías el Problema de Monty Hall antes de esta investigación?",
        "screening_prior_no": "No, nunca había oído hablar",
        "screening_prior_heard": "Escuché el nombre, pero no lo conozco bien",
        "screening_prior_yes": "Sí, conozco el problema y la solución",
        "screening_probability": "¿Cómo evalúas tu conocimiento en probabilidad y estadística?",
        "screening_probability_low": "Ninguno",
        "screening_probability_high": "Muy alto",
        "screening_continue": "Continuar",
        "screening_submitting": "Enviando...",
        "screening_leave_warning": "Envío en curso. Si sales ahora, esta etapa puede perderse.",
        "session_title": "Problema de Monty Hall",
        "session_stage": "Etapa 2 de 3 · Sesión",
        "session_done": "Llegaste al final de la sesión. Haz clic para responder el cuestionario final.",
        "session_done_cta": "Ir al cuestionario",
        "session_placeholder": "Escribe tu respuesta aquí...",
        "session_send": "Enviar",
        "session_you": "Tú",
        "session_refresh_blocked": "La actualización de página está desactivada durante la sesión.",
        "session_leave_warning": "Si sales ahora, puedes perder el contexto visible de la conversación.",
        "evaluation_stage": "Etapa 3 de 3 · Cuestionario final",
        "evaluation_title": "Evaluación posterior a la sesión",
        "evaluation_subtitle": "Responde según tu experiencia durante la sesión. No hay respuestas correctas o incorrectas.",
        "evaluation_q1": "Después de la sesión, siento que comprendo por qué cambiar de puerta aumenta la probabilidad de ganar.",
        "evaluation_q2": "Siento que llegué a la respuesta por mi cuenta, sin que me la dieran directamente.",
        "evaluation_q3": "Las preguntas de la sesión me ayudaron a pensar más profundamente sobre el problema.",
        "evaluation_q4": "En algún momento sentí frustración por no recibir una respuesta directa.",
        "evaluation_q5": "Percibí que el tutor adaptaba sus preguntas según mis respuestas.",
        "evaluation_q6": "Describe brevemente qué cambió en tu comprensión durante la sesión (o qué quedó confuso).",
        "evaluation_placeholder": "Tu respuesta...",
        "evaluation_likert_disagree": "Totalmente en desacuerdo",
        "evaluation_likert_agree": "Totalmente de acuerdo",
        "evaluation_send": "Enviar respuestas",
        "evaluation_done_label": "Investigación finalizada",
        "evaluation_done_title": "Gracias por tu participación.",
        "evaluation_done_body": "Tus respuestas fueron registradas con éxito. Los resultados de esta investigación se usarán exclusivamente con fines académicos.",
    },
}

SYSTEM_PROMPT = """You are a Socratic tutor helping a student understand the Monty Hall Problem.
RULES — follow these strictly:
1. NEVER give the correct answer directly.
2. NEVER suggest or plant misconceptions in your opening — let the student reveal their own intuition.
3. In each turn, usually ask 2-3 short linked questions that guide one clear reasoning path.
4. Calibrate your question to what the student just said — directly target their last claim.
5. If the student shows progress, acknowledge it briefly and advance one step deeper; do not restart earlier steps.
6. If the student has shown no progress after 4 exchanges, give ONE minimal hint — one fact, not the answer.
7. When the student reaches the correct conclusion (1/3 vs 2/3), ask them to consolidate: explain it as if teaching someone else.
8. When the student gives a complete and correct explanation of WHY switching gives 2/3 — meaning they explain both the initial 1/3 probability AND the concentration of the remaining 2/3 — respond with a single congratulatory sentence and include the marker <<DONE>> at the end. Do not ask another question.
9. Use simple, everyday language for a general audience. Avoid jargon and long words.
10. Keep each question under 20 words.
11. Strong anti-repetition: avoid repeating wording or structure from this message and recent turns.
12. Prefer open questions that make the student explain reasoning; avoid yes/no unless needed to confirm a key structural idea.
Start by presenting the Monty Hall Problem clearly and concisely in 3-4 sentences, then ask ONE open question: "What would you do — switch or stay?" Say nothing else.
"""

EXPOSITORY_PROMPT = """You are an expository tutor helping a student understand the Monty Hall Problem.
RULES — follow these strictly:
1. Explain directly and clearly; do not use Socratic questioning style.
2. Use simple language for a general audience.
3. Keep responses concise and focused on the student's latest message.
4. When needed, explain with a short causal chain: initial 1/3 on chosen door, remaining 2/3 transferred after host opens a goat door.
5. Ask if the student understood after each explanation.
6. If the student asks to stop, acknowledge and finish politely.
Start by presenting the Monty Hall Problem in 3-4 sentences and directly explain that switching is better and why, then ask: "Did this make sense to you?"
"""

EXPOSITORY_REEXPLAIN_PROMPT = """You are an expository tutor on the Monty Hall Problem.
The student said they did not understand (or likely did not understand).
Explain again in a different, simpler way using short sentences.
Do not be Socratic. Do not ask multiple questions.
End with exactly one check question: "Does this explanation make sense now?"
"""

EXPOSITORY_RUBRIC_PROMPT = """You assess student understanding of Monty Hall using this rubric:
N0: no justification.
N1: intuitive but incorrect.
N2: partially correct.
N3: correct without causal demonstration.
N4: correct with explicit causal demonstration (mentions initial 1/3 and transferred 2/3).

Return ONLY JSON:
{
  "rubric_level": <0..4>,
  "rubric_label": "<n0|n1|n2|n3|n4>",
  "rubric_rationale": "<one short sentence>"
}
"""

SESSION_SUMMARY_PROMPT = """Summarize this Monty Hall tutoring session state in exactly 3 short lines:
1) Student current position
2) Active misconception (or 'none')
3) Progress status

Use plain language.
Return only the 3 lines. No bullets, no JSON."""

CONTEXT_WINDOW = 12
SUMMARY_EVERY_TURNS = 10

# KNOWN MISCONCEPTIONS to watch for:
# - "It's 50/50 after one door is opened"
# - "Switching doesn't change anything"
# - "The remaining doors are equally likely"
# - "The host's action is random"
# - "My original choice is as good as switching"


def get_participant(request: Request):
    pid = request.session.get("participant_id")
    if pid and pid in participants:
        return participants[pid]
    return None

def normalize_language(language_code: str) -> str:
    if language_code in LANGUAGE_NAMES:
        return language_code
    return "pt"


def get_ui(language_code: str):
    return UI_TEXT.get(normalize_language(language_code), UI_TEXT["pt"])


def get_selected_language(request: Request) -> str:
    selected_language = request.session.get("selected_language")
    if selected_language:
        return normalize_language(selected_language)

    header = (request.headers.get("accept-language") or "").lower()
    for token in re.split(r"[,;]", header):
        code = token.strip()
        if code.startswith("pt"):
            return "pt"
        if code.startswith("en"):
            return "en"
        if code.startswith("es"):
            return "es"
    return "pt"


def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
    if not text:
        return text
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise translator.\n"
                    "Translate the text faithfully.\n"
                    "Keep the original intent and tone.\n"
                    "Do not add explanations.\n"
                    "Return only the translated text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Source language: {source_language}\n"
                    f"Target language: {target_language}\n\n"
                    f"Text:\n{text}"
                ),
            },
        ],
        temperature=0,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def to_english(text: str, language_code: str) -> str:
    if language_code == "en":
        return text
    return translate_text(
        text=text,
        target_language="English",
        source_language=LANGUAGE_NAMES.get(language_code, "auto"),
    )


def from_english(text: str, language_code: str) -> str:
    if language_code == "en":
        return text
    return translate_text(
        text=text,
        target_language=LANGUAGE_NAMES.get(language_code, "Portuguese"),
        source_language="English",
    )


def get_progress_signal(classification_log):
    recent = classification_log[-3:]
    if not recent:
        return "neutral"

    misconception_count = sum(1 for item in recent if item.get("misconception_flag"))
    if misconception_count >= 2:
        return "stuck"
    if misconception_count == 0:
        return "progressing"
    return "mixed"


def user_wants_to_stop(message: str, message_en: str) -> bool:
    text = (message or "").lower().strip()
    text_en = (message_en or "").lower().strip()

    stop_patterns = [
        r"\bdesisto\b",
        r"\bquero parar\b",
        r"\bvou parar\b",
        r"\bpodemos parar\b",
        r"\bencerrar\b",
        r"\bsair\b",
        r"\bi give up\b",
        r"\bi want to stop\b",
        r"\blet'?s stop\b",
        r"\bcan we stop\b",
        r"\bquit\b",
        r"\bstop\b",
        r"\bend (here|now)\b",
        r"\bme rindo\b",
        r"\bquiero parar\b",
        r"\bpodemos parar\b",
        r"\bterminar\b",
    ]
    negation_patterns = [
        r"\bn[aã]o quero parar\b",
        r"\bn[aã]o vou parar\b",
        r"\bdon'?t stop\b",
        r"\bdo not stop\b",
        r"\bno quiero parar\b",
    ]

    if any(re.search(pattern, text) for pattern in negation_patterns):
        return False
    if any(re.search(pattern, text_en) for pattern in negation_patterns):
        return False

    return any(re.search(pattern, text) for pattern in stop_patterns) or any(
        re.search(pattern, text_en) for pattern in stop_patterns
    )


def detect_understanding_signal(message_en: str):
    text = (message_en or "").lower().strip()
    negative_patterns = [
        r"\bi (still )?don'?t understand\b",
        r"\bi do not understand\b",
        r"\bnot clear\b",
        r"\bstill confused\b",
        r"\bi'?m confused\b",
        r"\bno,? ?i don'?t\b",
        r"\bnao entendi\b",
        r"\bn[aã]o entendi\b",
        r"\bno entendi\b",
        r"\bno entiendo\b",
    ]
    positive_patterns = [
        r"\bi understand\b",
        r"\bthat makes sense\b",
        r"\bgot it\b",
        r"\bok(ay)? i get it\b",
        r"\bentendi\b",
        r"\bagora entendi\b",
        r"\bsi entendi\b",
        r"\bs[ií],? entiendo\b",
    ]
    if any(re.search(pattern, text) for pattern in negative_patterns):
        return False
    if any(re.search(pattern, text) for pattern in positive_patterns):
        return True
    return None


def evaluate_expository_rubric(history_en, student_message_en):
    recent_history = history_en[-CONTEXT_WINDOW:]
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": EXPOSITORY_RUBRIC_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Recent context:\n{chr(10).join(m['role'] + ': ' + m['content'] for m in recent_history)}\n\n"
                    f"Student explanation to score:\n{student_message_en}\n\n"
                    "Return JSON only."
                ),
            },
        ],
        temperature=0.1,
        max_tokens=180,
    )
    raw = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    data = json.loads(raw)
    level = data.get("rubric_level")
    if not isinstance(level, int) or level < 0 or level > 4:
        level = 0
    label = str(data.get("rubric_label", f"n{level}")).lower()
    if label not in {"n0", "n1", "n2", "n3", "n4"}:
        label = f"n{level}"
    rationale = data.get("rubric_rationale", "")
    return {"rubric_level": level, "rubric_label": label, "rubric_rationale": rationale}


def rubric_level_text(level: int):
    labels = {
        0: "no justification",
        1: "intuitive but incorrect",
        2: "partially correct",
        3: "correct without explicit causal demonstration",
        4: "correct with explicit causal demonstration",
    }
    return labels.get(level, "no justification")


def maybe_refresh_session_summary(participant, turn_number):
    if turn_number <= 0 or turn_number % SUMMARY_EVERY_TURNS != 0:
        return
    history_en = participant["history_en"]
    recent_history = history_en[-CONTEXT_WINDOW:]
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SESSION_SUMMARY_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Recent transcript:\n{chr(10).join(m['role'] + ': ' + m['content'] for m in recent_history)}\n\n"
                    "Write the 3-line summary now."
                ),
            },
        ],
        temperature=0.2,
        max_tokens=120,
    )
    participant["session_summary"] = response.choices[0].message.content.strip()


def build_generation_messages(system_prompt, history_en, session_summary):
    recent_history = history_en[-CONTEXT_WINDOW:]
    if not session_summary:
        return [{"role": "system", "content": system_prompt}] + recent_history
    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "system",
            "content": (
                "Session memory summary from older turns:\n"
                f"{session_summary}\n"
                "Use this as high-level context and prioritize the recent transcript."
            ),
        },
    ] + recent_history


def get_opening(history_en, language_code, group_name):
    system_prompt = SYSTEM_PROMPT if group_name == "socratic" else EXPOSITORY_PROMPT
    history_en.append({"role": "user", "content": "BEGIN"})
    generation_messages = build_generation_messages(system_prompt, history_en, session_summary=None)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=generation_messages,
        temperature=0.7,
        max_tokens=200,
    )
    reply_en = response.choices[0].message.content
    history_en.append({"role": "assistant", "content": reply_en})
    return from_english(reply_en, language_code)


def get_chat_messages_for_ui(participant):
    language_code = participant["language"]
    messages = []
    for msg in participant.get("history_en", []):
        if msg["role"] == "user" and msg["content"] == "BEGIN":
            continue
        role = "tutor" if msg["role"] == "assistant" else "user"
        messages.append(
            {
                "role": role,
                "content": from_english(msg["content"], language_code),
            }
        )
    if not messages and participant.get("opening"):
        messages.append({"role": "tutor", "content": participant["opening"]})
    return messages


def build_expository_analysis(rubric_level=None, rubric_label=None, rubric_rationale=None):
    resolved = None if rubric_level is None else rubric_level >= 4
    rationale = "Session used the expository control agent with direct explanations."
    if rubric_level is not None:
        rationale += f" Final level: {rubric_label} ({rubric_rationale or rubric_level_text(rubric_level)})."
    return {
        "pattern": "expository_control",
        "rationale": rationale,
        "turning_point": None,
        "dominant_category": "expository",
        "misconception_resolved": resolved,
    }


#  Routes 

@app.get("/", response_class=HTMLResponse)
async def language_page(request: Request):
    language_code = get_selected_language(request)
    return templates.TemplateResponse(
        "language.html",
        {"request": request, "ui": get_ui(language_code), "lang": language_code},
    )


@app.post("/language")
async def language_submit(request: Request, language: str = Form("pt")):
    request.session["selected_language"] = normalize_language(language)
    return RedirectResponse("/consent", status_code=303)


@app.get("/consent", response_class=HTMLResponse)
async def consent_page(request: Request):
    language_code = get_selected_language(request)
    return templates.TemplateResponse(
        "consent.html",
        {"request": request, "ui": get_ui(language_code), "lang": language_code},
    )

@app.post("/consent")
async def consent_submit(
    request: Request,
    consent: str = Form(...),
):
    if consent != "yes":
        return RedirectResponse("/consent", status_code=303)
    language_code = get_selected_language(request)
    pid = str(uuid.uuid4())
    request.session["participant_id"] = pid
    participants[pid] = {
        "id": pid,
        "consent": True,
        "language": language_code,
        "screening": {},
        "group": None,
        "history_en": [],
        "classification_log": [],
        "session_analysis": None,
        "evaluation": {},
        "expository_state": None,
        "session_summary": None,
    }
    return RedirectResponse("/screening", status_code=303)

@app.get("/screening", response_class=HTMLResponse)
async def screening_page(request: Request):
    participant = get_participant(request)
    if not participant:
        return RedirectResponse("/")
    language_code = participant["language"]
    return templates.TemplateResponse(
        "screening.html",
        {
            "request": request,
            "ui": get_ui(language_code),
            "lang": language_code,
        },
    )

@app.post("/screening")
async def screening_submit(
    request: Request,
    age: str = Form(...),
    education: str = Form(...),
    prior_knowledge: str = Form(...),
    probability_familiarity: str = Form(...),
):
    p = get_participant(request)
    if not p:
        return RedirectResponse("/")
    p["screening"] = {
        "age": age,
        "education": EDUCATION_MAP.get(education, education),
        "prior_knowledge": prior_knowledge,
        "probability_familiarity": probability_familiarity,
    }
    p["group"] = random.choice(["socratic", "expository"])
    if p["group"] == "expository":
        p["expository_state"] = "check_understanding"

    # save participant to Supabase
    save_participant(p)

    opening = get_opening(p["history_en"], p["language"], p["group"])
    p["opening"] = opening
    return RedirectResponse("/session", status_code=303)

@app.get("/session", response_class=HTMLResponse)
async def session_page(request: Request):
    p = get_participant(request)
    if not p:
        return RedirectResponse("/")
    language_code = p["language"]
    return templates.TemplateResponse("session.html", {
        "request": request,
        "group": p["group"],
        "chat_messages": get_chat_messages_for_ui(p),
        "ui": get_ui(language_code),
        "lang": language_code,
    })

@app.post("/chat")
async def chat_endpoint(request: Request):
    p = get_participant(request)
    if not p:
        return JSONResponse({"error": "session not found"}, status_code=403)

    body = await request.json()
    user_message = body.get("message", "").strip()
    if not user_message:
        return JSONResponse({"error": "empty message"}, status_code=400)

    language_code = p["language"]
    user_message_en = to_english(user_message, language_code)
    history_en = p["history_en"]
    history_en.append({"role": "user", "content": user_message_en})

    if user_wants_to_stop(user_message, user_message_en):
        turn_number = len(p["classification_log"]) + 1
        meta = {
            "category": "purpose",
            "rationale": "Student explicitly requested to stop the session.",
            "misconception_flag": False,
            "misconception_label": None,
            "rubric_level": 0,
            "rubric_label": "n0",
            "rubric_rationale": "Student stopped without adding a justification for the choice.",
        }
        p["classification_log"].append({"turn": turn_number, **meta})
        reply_en = "Understood. We can stop here. Thanks for your participation."
        history_en.append({"role": "assistant", "content": reply_en})
        if p["group"] == "socratic":
            analysis = analyze_session(history_en, p["classification_log"])
        else:
            analysis = build_expository_analysis()
        p["session_analysis"] = analysis
        save_analysis(p["id"], analysis)
        mark_completed(p["id"])
        save_turn(p["id"], turn_number, user_message_en, reply_en, meta)
        reply = from_english(reply_en, language_code)
        return JSONResponse({"reply": reply, "done": True})

    if p["group"] == "socratic":
        # classify and generate question
        progress_signal = get_progress_signal(p["classification_log"])
        meta = classify_and_question(
            user_message=user_message_en,
            history=history_en,
            progress_signal=progress_signal,
            session_summary=p.get("session_summary"),
            context_window=CONTEXT_WINDOW,
        )
        turn_number = len(p["classification_log"]) + 1
        p["classification_log"].append({"turn": turn_number, **meta})
        maybe_refresh_session_summary(p, turn_number)

        # check if student reached correct understanding
        completion_messages = build_generation_messages(
            SYSTEM_PROMPT,
            history_en,
            p.get("session_summary"),
        )
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=completion_messages,
            temperature=0.2,
            max_tokens=200,
        )
        completion_reply_en = completion.choices[0].message.content

        if "<<DONE>>" in completion_reply_en:
            reply_en = completion_reply_en.replace("<<DONE>>", "").strip()
            done = True
            analysis = analyze_session(history_en, p["classification_log"])
            p["session_analysis"] = analysis
            save_analysis(p["id"], analysis)
            mark_completed(p["id"])
        else:
            reply_en = meta["question"]
            done = False
    else:
        state = p.get("expository_state", "check_understanding")
        turn_number = len(p["classification_log"]) + 1
        if state == "await_final_explanation":
            rubric = evaluate_expository_rubric(history_en, user_message_en)
            level = rubric["rubric_level"]
            reply_en = (
                "Thanks for your explanation. Session complete. Please continue to the final questionnaire."
            )
            meta = {
                "category": "expository_assessment",
                "rationale": "Final explanatory answer assessed with rubric.",
                "misconception_flag": level < 3,
                "misconception_label": "incomplete_explanation" if level < 4 else None,
                **rubric,
            }
            p["classification_log"].append({"turn": turn_number, **meta})
            analysis = build_expository_analysis(
                rubric_level=rubric["rubric_level"],
                rubric_label=rubric["rubric_label"],
                rubric_rationale=rubric["rubric_rationale"],
            )
            p["session_analysis"] = analysis
            save_analysis(p["id"], analysis)
            mark_completed(p["id"])
            maybe_refresh_session_summary(p, turn_number)
            done = True
            p["expository_state"] = "done"
        else:
            understood = detect_understanding_signal(user_message_en)
            if understood is True:
                reply_en = (
                    "Great. Now explain fully why switching is better, including why your first door is 1/3 and the other becomes 2/3."
                )
                p["expository_state"] = "await_final_explanation"
                meta = {
                    "category": "expository_check",
                    "rationale": "Student said they understood and was asked for a full explanation.",
                    "misconception_flag": False,
                    "misconception_label": None,
                    "rubric_level": None,
                    "rubric_label": None,
                    "rubric_rationale": None,
                }
            else:
                system_prompt = EXPOSITORY_REEXPLAIN_PROMPT if understood is False else EXPOSITORY_PROMPT
                generation_messages = build_generation_messages(
                    system_prompt,
                    history_en,
                    p.get("session_summary"),
                )
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=generation_messages,
                    temperature=0.4,
                    max_tokens=220,
                )
                reply_en = response.choices[0].message.content
                p["expository_state"] = "check_understanding"
                meta = {
                    "category": "expository",
                    "rationale": "Expository control response directly explains the concept and checks understanding.",
                    "misconception_flag": False,
                    "misconception_label": None,
                    "rubric_level": None,
                    "rubric_label": None,
                    "rubric_rationale": None,
                }
            p["classification_log"].append({"turn": turn_number, **meta})
            maybe_refresh_session_summary(p, turn_number)
            done = False

    history_en.append({"role": "assistant", "content": reply_en})
    reply = from_english(reply_en, language_code)

    #save this turn to Supabase
    save_turn(p["id"], turn_number, user_message_en, reply_en, meta)

    return JSONResponse({"reply": reply, "done": done})

@app.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request):
    participant = get_participant(request)
    if not participant:
        return RedirectResponse("/")
    language_code = participant["language"]
    return templates.TemplateResponse(
        "evaluation.html",
        {
            "request": request,
            "ui": get_ui(language_code),
            "lang": language_code,
        },
    )

@app.post("/evaluation")
async def evaluation_submit(request: Request):
    p = get_participant(request)
    if not p:
        return RedirectResponse("/")
    form = await request.form()
    form_data = dict(form)
    form_data_for_storage = dict(form_data)
    form_data_for_storage["q6_open"] = to_english(form_data.get("q6_open", ""), p["language"])
    p["evaluation"] = form_data_for_storage

    # save evaluation to Supabase
    save_evaluation(p["id"], form_data_for_storage)

    return templates.TemplateResponse("evaluation.html", {
        "request": request,
        "ui": get_ui(p["language"]),
        "lang": p["language"],
        "done": True,
    })
