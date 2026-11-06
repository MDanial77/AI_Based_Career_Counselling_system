"""
Lightweight NLP engine (standard library only, works offline).

What it does with the student's free-text description:
  1. Pre-processing  : lower-casing, tokenising, stop-word removal, stemming.
  2. Extraction      : detects interests and skills from the text using
                       a stemmed keyword/phrase lexicon.
  3. TF-IDF matching : compares the text with every career in the database
                       (name + description + skills + interest) using
                       TF-IDF vectors and cosine similarity.
"""
import math
import re
from collections import Counter

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do",
    "for", "from", "have", "i", "in", "into", "is", "it", "like", "love",
    "enjoy", "want", "would", "me", "my", "of", "on", "or", "so", "that",
    "the", "this", "to", "very", "really", "with", "am", "also", "being",
    "become", "interested", "good", "well", "much", "lot", "things", "thing",
}

_SUFFIXES = ("ations", "ation", "ings", "ing", "ers", "er", "ed", "es", "ly", "s")


def stem(word):
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokenize(text):
    words = re.findall(r"[a-z0-9+#]+", str(text or "").lower())
    return [stem(w) for w in words if w not in STOP_WORDS and len(w) > 1]


# ----------------------------------------------------------
# Lexicons: interest / skill  ->  words or phrases that signal it
# ----------------------------------------------------------

INTEREST_LEXICON = {
    "Programming": ["programming", "coding", "code", "software", "app", "website", "web", "developer", "algorithm", "python", "java", "debug", "build apps", "machine learning", "artificial intelligence", "ai", "neural network"],
    "Mathematics": ["actuary", "insurance risk", "math", "mathematics", "statistics", "numbers", "equation", "calculation", "data", "analytics", "logic", "puzzle"],
    "Biology": ["animal", "pets", "livestock", "veterinary", "nursing", "nurse", "physiotherapy", "nutrition", "diet", "farming", "agriculture", "crops", "biotechnology", "biology", "patient", "hospital", "doctor", "medicine", "medical", "health", "human body", "disease", "surgery", "nursing", "clinic", "treat people"],
    "Business": ["audit", "chartered accountant", "bank", "supply chain", "logistics", "hotel", "tourism", "product manager", "business", "manage", "management", "marketing", "sales", "entrepreneur", "finance", "accounting", "startup", "bank", "customer", "company"],
    "Arts": ["fashion", "clothes", "interior", "architecture", "cooking", "chef", "food", "video editing", "film", "art", "draw", "drawing", "design", "creative", "painting", "animation", "photography", "video", "writing", "story", "music", "illustration", "journalism"],
    "Teaching": ["teach", "teacher", "student", "explain", "classroom", "tutor", "mentor", "lecture", "school", "educate"],
    "Technology": ["pilot", "aircraft", "airplane", "fly planes", "drone", "telecom", "testing software", "technology", "network", "security", "hacking", "cyber", "cloud", "server", "computer", "hardware", "linux", "devops", "robot", "machine learning", "artificial intelligence", "ai", "neural network"],
    "Physics": ["geology", "rocks", "oil and gas", "aerospace", "physics", "electric", "circuit", "mechanic", "energy", "engineering", "motor", "structure", "construction", "build bridges"],
    "Chemistry": ["chemistry", "chemical", "laboratory", "experiment", "pharmacy", "drug", "reaction", "environment"],
    "Debate": ["judge", "debate", "law", "court", "argue", "lawyer", "justice", "public speaking", "journalist", "interview"],
    "Public Service": ["army", "military", "soldier", "defence", "defense", "serve the nation", "social work", "help poor", "city planning", "government", "civil service", "css", "public service", "administration", "policy", "serve country", "community", "officer"],
}

SKILL_LEXICON = {
    "Python": ["python"],
    "Programming": ["programming", "coding", "write code", "developer"],
    "Problem Solving": ["solve problem", "solving problem", "problem solving", "puzzle", "troubleshoot"],
    "Debugging": ["debug", "fix bug", "fixing bug"],
    "SQL": ["sql", "database", "mysql", "query"],
    "Power BI": ["power bi", "dashboard"],
    "Statistics": ["statistics", "statistical", "probability"],
    "Data Analysis": ["data analysis", "analyse data", "analyze data", "analysing data", "analyzing data", "data analytics"],
    "HTML": ["html"], "CSS": ["css"], "JavaScript": ["javascript"], "Flask": ["flask"], "Git": ["git", "github"],
    "Networking": ["network", "router", "cisco"],
    "Linux": ["linux"],
    "Ethical Hacking": ["ethical hacking", "penetration test", "hacking"],
    "Cybersecurity": ["cyber security", "cybersecurity", "security"],
    "Communication": ["communicate", "communication", "talk to people", "presentation"],
    "Leadership": ["lead team", "leading team", "leadership", "leader", "manage team"],
    "Creativity": ["creative", "creativity", "imagination"],
    "Accounting": ["accounting", "bookkeeping", "tax"],
    "Biology": ["biology"],
    "Chemistry": ["chemistry"],
    "Patient Care": ["patient", "nursing", "care for", "help sick"],
    "Physics": ["physics"],
    "Teaching": ["teach", "tutor", "explain concept"],
    "Research": ["research", "investigate", "study papers"],
    "Public Speaking": ["public speaking", "speech", "present in front"],
    "Critical Thinking": ["critical thinking", "analyse argument", "analyze argument"],
    "Mathematics": ["math", "mathematics", "calculus", "algebra"],
    "Excel": ["excel", "spreadsheet"],
    "Marketing": ["marketing", "advertising", "social media"],
    "Graphic Design": ["graphic design", "photoshop", "logo", "poster"],
    "Content Writing": ["write article", "writing article", "blog", "content writing", "copywriting"],
    "Analytical Thinking": ["analytical", "analyse", "analyze", "analysing", "analyzing"],
    "Lesson Planning": ["lesson plan", "curriculum"],
    "Administration": ["administration", "organise", "organize", "paperwork"],
    "Nursing": ["nursing", "nurse"],
    "Animal Care": ["animal", "pets", "livestock"],
    "Physical Fitness": ["fitness", "sports", "exercise", "running"],
    "Discipline": ["discipline", "disciplined"],
    "Video Editing": ["video editing", "edit videos", "editing videos", "youtube"],
    "Fashion Design": ["fashion", "clothes design", "stitching"],
    "Cooking": ["cooking", "cook", "baking", "recipes"],
    "Design": ["building design", "architecture", "interior"],
    "Taxation": ["tax", "taxation"],
    "Auditing": ["audit", "auditing"],
    "Customer Service": ["customer service", "customers"],
    "Navigation": ["navigation", "flying", "fly planes"],
}


def _compile(lexicon):
    compiled = {}
    for name, phrases in lexicon.items():
        compiled[name] = [frozenset(tokenize(p)) for p in phrases if tokenize(p)]
    return compiled


_INTERESTS = _compile(INTEREST_LEXICON)
_SKILLS = _compile(SKILL_LEXICON)


def _hits(token_set, compiled):
    scores = {}
    for name, phrases in compiled.items():
        count = sum(1 for phrase in phrases if phrase <= token_set)
        if count:
            scores[name] = count
    return scores


def extract(text):
    """Detect interests and skills mentioned in free text."""
    tokens = set(tokenize(text))
    if not tokens:
        return {"interests": [], "skills": []}
    interests = sorted(_hits(tokens, _INTERESTS).items(), key=lambda x: -x[1])
    skills = sorted(_hits(tokens, _SKILLS).items(), key=lambda x: -x[1])
    return {
        "interests": [name for name, _ in interests[:3]],
        "skills": [name for name, _ in skills[:6]],
    }


# ----------------------------------------------------------
# TF-IDF similarity between the text and every career
# ----------------------------------------------------------

def career_similarities(text, careers):
    """Return {career_id: cosine similarity} using TF-IDF over careers."""
    found = extract(text)
    query_tokens = tokenize(text)
    for name in found["interests"] + found["skills"]:
        query_tokens += tokenize(name)
    if len(query_tokens) < 3:
        return {}

    documents = {}
    for career in careers:
        documents[career["id"]] = tokenize(" ".join([
            str(career["career_name"] or ""), str(career["career_name"] or ""),
            str(career["description"] or ""), str(career["required_skills"] or ""),
            str(career["interest"] or ""), str(career["future_scope"] or ""),
        ]))

    total = len(documents)
    doc_freq = Counter()
    for tokens in documents.values():
        doc_freq.update(set(tokens))
    idf = {t: math.log((1 + total) / (1 + df)) + 1 for t, df in doc_freq.items()}

    def vectorise(tokens):
        counts = Counter(t for t in tokens if t in idf)
        return {t: c * idf[t] for t, c in counts.items()}

    query = vectorise(query_tokens)
    q_norm = math.sqrt(sum(v * v for v in query.values()))
    if not q_norm:
        return {}

    similarities = {}
    for career_id, tokens in documents.items():
        vec = vectorise(tokens)
        d_norm = math.sqrt(sum(v * v for v in vec.values()))
        if not d_norm:
            continue
        dot = sum(query[t] * vec.get(t, 0) for t in query)
        similarities[career_id] = dot / (q_norm * d_norm)
    return similarities
