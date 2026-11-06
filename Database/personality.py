"""
Personality (Holland RIASEC) module.

SRS FR5 and FR7: a 15-question psychometric quiz based on Holland's theory of
career choice, and cosine similarity (scikit-learn) between the student's
personality profile and each career's personality profile.

How it works
1. The student rates 15 statements from 1 (strongly disagree) to 5 (strongly
   agree). Each statement belongs to one of the six Holland types.
2. Each type's score is the average of its answers, scaled to 0-1.
3. Each career has a Holland code such as "IS" (Investigative, Social). The
   first letter gets weight 1.0, the second 0.7 and the third 0.4; the other
   types get 0.1.
4. Both six-number profiles are mean-centred (so the comparison looks at the
   *shape* of the profile, not whether someone answers everything high or low)
   and compared with sklearn.metrics.pairwise.cosine_similarity. The result,
   from -1 to 1, is converted to a 0-100% "personality match".
"""
try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover - the app still works without it
    SKLEARN_AVAILABLE = False

TYPES = ["R", "I", "A", "S", "E", "C"]

TYPE_INFO = {
    "R": ("Realistic", "Practical, hands-on work with tools, machines or the outdoors"),
    "I": ("Investigative", "Analysing, researching and solving problems"),
    "A": ("Artistic", "Creating, designing and expressing ideas"),
    "S": ("Social", "Helping, teaching and caring for people"),
    "E": ("Enterprising", "Leading, persuading and running businesses"),
    "C": ("Conventional", "Organising, keeping records and following clear procedures"),
}

# 15 statements (based on the SRS, Appendix 9.3)
QUESTIONS = [
    ("q1", "R", "I prefer working with machines and tools rather than people."),
    ("q2", "R", "I enjoy building or repairing things."),
    ("q3", "R", "I like outdoor or physical activities."),
    ("q4", "I", "I enjoy solving complex problems and puzzles."),
    ("q5", "I", "I like conducting experiments and research."),
    ("q6", "I", "I prefer working with data and theories."),
    ("q7", "A", "I enjoy creative activities like drawing, writing, or music."),
    ("q8", "A", "I like expressing myself through art or design."),
    ("q9", "S", "I enjoy helping and teaching others."),
    ("q10", "S", "I like working in teams and collaborating."),
    ("q11", "S", "I am interested in understanding people's problems."),
    ("q12", "E", "I enjoy leading teams and persuading others."),
    ("q13", "E", "I am interested in business and sales."),
    ("q14", "C", "I prefer organised, structured work environments."),
    ("q15", "C", "I enjoy keeping accurate records and following clear procedures."),
]

ANSWER_LABELS = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]

# Holland code for every career (dominant type first)
HOLLAND_CODES = {
    "Software Engineer": "IRC", "AI Engineer": "IR", "Data Scientist": "IC",
    "Web Developer": "AI", "Cyber Security Analyst": "IC", "Doctor": "IS",
    "Dentist": "RI", "Pharmacist": "IC", "Graphic Designer": "AR", "Animator": "AI",
    "Accountant": "CI", "Bank Manager": "EC", "Marketing Manager": "EA",
    "Civil Engineer": "RC", "Mechanical Engineer": "RI", "Electrical Engineer": "RI",
    "Teacher": "SA", "Lecturer": "SI", "Lawyer": "EI", "CSS Officer": "ES",
    "AI Research Scientist": "IR", "Machine Learning Engineer": "IR", "Data Analyst": "IC",
    "Cloud Engineer": "IR", "DevOps Engineer": "IRC", "Mobile App Developer": "IA",
    "Network Engineer": "RI", "Database Administrator": "CI", "UI/UX Designer": "AI",
    "Game Developer": "AI", "Biomedical Engineer": "IS", "Chemical Engineer": "IR",
    "Environmental Engineer": "IS", "Economist": "IC", "Financial Analyst": "IC",
    "Human Resources Manager": "SE", "Content Writer": "AS", "Psychologist": "IS",
    "Journalist": "AS", "Public Administration Officer": "EC",
    "Nurse": "SI", "Physiotherapist": "SR", "Medical Lab Technologist": "RC",
    "Radiologic Technologist": "RI", "Nutritionist": "IS", "Veterinary Doctor": "IR",
    "Public Health Specialist": "SE", "Biotechnologist": "IR", "Microbiologist": "IR",
    "Chemist": "IR", "Physicist": "IR", "Geologist": "IR", "Statistician": "IC",
    "Actuary": "CI", "Agriculture Officer": "RI", "Full Stack Developer": "IR",
    "Software QA Engineer": "CI", "Data Engineer": "IC", "Product Manager": "EI",
    "Aerospace Engineer": "IR", "Mechatronics Engineer": "RI", "Petroleum Engineer": "RI",
    "Textile Engineer": "RC", "Telecom Engineer": "RI", "Architect": "AI",
    "Urban Planner": "EI", "Chartered Accountant": "CE", "Banking Officer": "CE",
    "Business Analyst": "IE", "Digital Marketing Specialist": "EA",
    "Supply Chain Manager": "CE", "Hotel Manager": "ES", "Army Officer": "RE",
    "Commercial Pilot": "RI", "Civil Judge": "ES", "Social Worker": "SA",
    "Fashion Designer": "AE", "Interior Designer": "AE", "Video Editor": "AR", "Chef": "RA",
    "Entrepreneur": "ER", "Business Consultant": "EI", "IT Project Manager": "EC",
    "Photographer": "AR", "Art Director": "AE", "Music Producer": "AR",
    "Industrial Engineer": "RC", "Radiologist": "IR",
}

# Fallback for careers added later without a code: use their main interest
INTEREST_CODES = {
    "Programming": "IR", "Mathematics": "IC", "Biology": "IS", "Business": "EC",
    "Arts": "AE", "Teaching": "SA", "Technology": "RI", "Physics": "IR",
    "Chemistry": "IR", "Debate": "ES", "Public Service": "SE",
}

WEIGHTS = (1.0, 0.7, 0.4)
BASE = 0.1


def clean_code(code):
    """Keep only valid, unique RIASEC letters (max 3)."""
    letters = []
    for letter in str(code or "").upper():
        if letter in TYPES and letter not in letters:
            letters.append(letter)
    return "".join(letters[:3])


def code_for(career):
    code = clean_code(career.get("holland_code"))
    if code:
        return code
    name = career.get("career_name", "")
    if name in HOLLAND_CODES:
        return HOLLAND_CODES[name]
    return INTEREST_CODES.get(career.get("interest", ""), "IR")


def career_vector(code):
    vector = {t: BASE for t in TYPES}
    for weight, letter in zip(WEIGHTS, clean_code(code)):
        vector[letter] = weight
    return [vector[t] for t in TYPES]


def score_answers(form, required=True):
    """Return {type: 0-1 score} from the quiz answers, or None if incomplete."""
    totals = {t: [] for t in TYPES}
    for key, letter, _ in QUESTIONS:
        raw = str(form.get(key, "")).strip()
        if raw not in {"1", "2", "3", "4", "5"}:
            if required:
                raise ValueError("Please answer all 15 personality questions.")
            return None
        totals[letter].append(int(raw))
    return {t: round((sum(v) / len(v) - 1) / 4, 3) for t, v in totals.items()}


def answers_from(form):
    return {key: int(form.get(key)) for key, _, _ in QUESTIONS
            if str(form.get(key, "")).strip() in {"1", "2", "3", "4", "5"}}


def top_types(scores, count=3):
    ordered = sorted(TYPES, key=lambda t: -scores.get(t, 0))
    return [{"code": t, "name": TYPE_INFO[t][0], "about": TYPE_INFO[t][1],
             "score": round(scores.get(t, 0) * 100)} for t in ordered[:count]]


def personality_matches(scores, careers):
    """Return {career_name: 0-100 personality match} using cosine similarity."""
    if not scores or not careers:
        return {}
    student = [scores[t] for t in TYPES]
    if not SKLEARN_AVAILABLE:
        return {}
    student = np.array([student], dtype=float)
    student = student - student.mean()
    if not np.any(student):
        # Every answer identical: no personality signal, so stay neutral.
        return {c["career_name"]: 50.0 for c in careers}
    matrix = np.array([career_vector(code_for(c)) for c in careers], dtype=float)
    matrix = matrix - matrix.mean(axis=1, keepdims=True)
    similarity = cosine_similarity(student, matrix)[0]          # -1 .. 1
    return {c["career_name"]: round(float((s + 1) / 2 * 100), 1)
            for c, s in zip(careers, similarity)}
