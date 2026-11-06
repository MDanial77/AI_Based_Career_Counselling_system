import math
import os
import re
import sqlite3
from collections import Counter

try:
    from Database import nlp_engine
except ImportError:  # when run from inside the Database folder
    import nlp_engine


# ==========================================================
# NORMALIZATION DATA
# ==========================================================

FIELD_ALIASES = {
    "cs": "computer science",
    "computer": "computer science",
    "computer science": "computer science",
    "software": "computer science",
    "it": "computer science",
    "information technology": "computer science",

    "medical": "medical",
    "medicine": "medical",
    "biology": "medical",
    "pre medical": "medical",
    "pre-medical": "medical",

    "arts": "arts",
    "art": "arts",
    "design": "arts",

    "commerce": "commerce",
    "accounting": "commerce",

    "business": "business",
    "management": "business",
    "marketing": "business",

    "engineering": "engineering",

    "education": "education",
    "teaching": "education",

    "law": "law",
    "llb": "law"
}


INTEREST_ALIASES = {
    "coding": "programming",
    "programming": "programming",
    "software": "programming",

    "math": "mathematics",
    "maths": "mathematics",
    "mathematics": "mathematics",
    "statistics": "mathematics",

    "biology": "biology",
    "medical": "biology",
    "medicine": "biology",

    "business": "business",
    "management": "business",
    "marketing": "business",

    "arts": "arts",
    "art": "arts",
    "design": "arts",

    "teaching": "teaching",
    "education": "teaching",

    "technology": "technology",
    "tech": "technology",

    "chemistry": "chemistry",
    "physics": "physics",

    "debate": "debate",
    "law": "debate",

    "public service": "public service",
    "government": "public service"
}


SKILL_ALIASES = {
    "problem-solving": "problem solving",
    "problem solving": "problem solving",

    "machine-learning": "machine learning",
    "ml": "machine learning",

    "deep-learning": "deep learning",
    "dl": "deep learning",

    "web dev": "web development",
    "web-development": "web development",

    "cybersecurity": "cyber security",
    "cyber-security": "cyber security",

    "patient-care": "patient care",

    "communication skills": "communication",
    "communications": "communication",

    "leadership skills": "leadership",

    "graphic design": "design",

    "c plus plus": "c++",
    "cpp": "c++"
}


EDUCATION_LEVELS = {
    "matric": 1,
    "o level": 1,
    "olevel": 1,
    "matriculation": 1,
    "secondary": 1,

    "intermediate": 2,
    "fsc": 2,
    "fa": 2,
    "ics": 2,
    "i.com": 2,
    "icom": 2,
    "a level": 2,
    "a levels": 2,

    "diploma": 2,

    "bachelor": 3,
    "bachelors": 3,
    "bs": 3,
    "bsc": 3,
    "ba": 3,
    "bba": 3,
    "b.com": 3,
    "bcom": 3,
    "llb": 3,

    "master": 4,
    "masters": 4,
    "ms": 4,
    "msc": 4,
    "ma": 4,
    "mba": 4,

    "mphil": 5,
    "m.phil": 5,

    "phd": 6,
    "doctorate": 6
}


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "for", "from", "in", "into", "is", "it", "of", "on",
    "or", "that", "the", "this", "to", "with", "your"
}


# ==========================================================
# TEXT HELPERS
# ==========================================================

def _clean_text(value):
    value = str(value or "").strip().lower()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def _split_values(value):
    """
    Split database values such as:
    'Chemistry, Biology'
    'Computer Science / IT'
    'Design; Art'
    """
    text = _clean_text(value)

    if not text:
        return []

    parts = re.split(
        r"\s*(?:,|;|\||/|\band\b)\s*",
        text
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def _normalize_field(value):
    value = _clean_text(value)
    return FIELD_ALIASES.get(value, value)


def _normalize_interest(value):
    value = _clean_text(value)
    return INTEREST_ALIASES.get(value, value)


def _normalize_skill(value):
    value = _clean_text(value)
    return SKILL_ALIASES.get(value, value)


def _tokenize(value):
    text = _clean_text(value)

    tokens = re.findall(
        r"[a-z0-9+#.]+",
        text
    )

    return [
        token
        for token in tokens
        if token not in STOPWORDS
    ]


def _cosine_similarity(text_a, text_b):
    """
    Lightweight text similarity using only Python's standard library.
    This avoids adding a new ML dependency while making the scoring
    depend on actual career data from the database.
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    vector_a = Counter(tokens_a)
    vector_b = Counter(tokens_b)

    common_tokens = set(vector_a) & set(vector_b)

    dot_product = sum(
        vector_a[token] * vector_b[token]
        for token in common_tokens
    )

    magnitude_a = math.sqrt(
        sum(value * value for value in vector_a.values())
    )

    magnitude_b = math.sqrt(
        sum(value * value for value in vector_b.values())
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def _phrase_similarity(value_a, value_b):
    """
    Similarity for fields, interests and skill phrases.
    """
    a = _clean_text(value_a)
    b = _clean_text(value_b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    if a in b or b in a:
        return 0.85

    tokens_a = set(_tokenize(a))
    tokens_b = set(_tokenize(b))

    if not tokens_a or not tokens_b:
        return 0.0

    overlap = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)

    if union == 0:
        return 0.0

    jaccard = overlap / union

    if jaccard >= 0.50:
        return 0.70

    if jaccard > 0:
        return 0.40

    return 0.0


# ==========================================================
# EDUCATION
# ==========================================================

def _normalize_education(value):
    value = _clean_text(value)

    aliases = {
        "inter": "intermediate",
        "f.sc": "fsc",
        "bachelor degree": "bachelor",
        "bachelors degree": "bachelor",
        "master degree": "master",
        "masters degree": "master"
    }

    return aliases.get(value, value)


def _education_match(user_education, required_education):
    user_education = _normalize_education(user_education)
    required_education = _normalize_education(required_education)

    if not required_education:
        return 1.0

    if user_education == required_education:
        return 1.0

    user_level = EDUCATION_LEVELS.get(user_education)
    required_level = EDUCATION_LEVELS.get(required_education)

    if user_level is not None and required_level is not None:
        if user_level >= required_level:
            return 1.0

        # One level below: partial compatibility only.
        if required_level - user_level == 1:
            return 0.35

        return 0.0

    return _phrase_similarity(
        user_education,
        required_education
    )


# ==========================================================
# ACADEMIC SCORE
# ==========================================================

def _marks_match(student_marks, minimum):
    try:
        minimum = float(minimum or 0)
    except (ValueError, TypeError):
        minimum = 0.0

    if minimum <= 0:
        return 1.0

    if student_marks >= minimum + 15:
        return 1.0

    if student_marks >= minimum:
        difference = student_marks - minimum

        return (
            0.75
            + (difference / 15) * 0.25
        )

    shortfall = minimum - student_marks

    if shortfall <= 5:
        return 0.20

    if shortfall <= 10:
        return 0.10

    return 0.0


# ==========================================================
# FIELD / INTEREST MATCHING
# ==========================================================

def _best_match_score(user_value, required_values):
    if not user_value:
        return 0.0

    if not required_values:
        return 0.0

    scores = [
        _phrase_similarity(
            user_value,
            required_value
        )
        for required_value in required_values
    ]

    return max(scores) if scores else 0.0


# ==========================================================
# SKILL MATCHING
# ==========================================================

def _analyse_skills(user_skills, required_skills):
    """
    Returns:
        skill_score
        matched_skills
        missing_skills
    """
    if not required_skills:
        return 0.0, set(), set()

    normalized_user_skills = [
        _normalize_skill(skill)
        for skill in user_skills
        if _normalize_skill(skill)
    ]

    matched_skills = set()
    missing_skills = set()

    for required_skill in required_skills:
        display_skill = required_skill.strip()
        normalized_required = _normalize_skill(
            required_skill
        )

        best_score = 0.0

        for user_skill in normalized_user_skills:
            score = _phrase_similarity(
                user_skill,
                normalized_required
            )

            if score > best_score:
                best_score = score

        # A phrase match of 0.70+ is treated as a real skill match.
        if best_score >= 0.70:
            matched_skills.add(display_skill)
        else:
            missing_skills.add(display_skill)

    skill_score = (
        len(matched_skills)
        / len(required_skills)
    )

    return (
        skill_score,
        matched_skills,
        missing_skills
    )


# ==========================================================
# DATA-DRIVEN PROFILE SIMILARITY
# ==========================================================

def _profile_similarity(
    user_field,
    user_interest,
    user_skills,
    career_name,
    required_fields,
    required_interests,
    required_skills,
    description
):
    """
    Builds a text profile for the user and a text profile for the
    career using database data, then compares them.

    This replaces the previous career-name-specific specialization
    block with a general data-driven comparison.
    """
    user_text = " ".join([
        user_field,
        user_interest,
        " ".join(user_skills)
    ])

    career_text = " ".join([
        career_name,
        " ".join(required_fields),
        " ".join(required_interests),
        " ".join(required_skills),
        str(description or "")
    ])

    return _cosine_similarity(
        user_text,
        career_text
    )


# ==========================================================
# MAIN RECOMMENDATION FUNCTION
# ==========================================================

def recommend_career(
    education,
    field,
    marks,
    interest,
    score_type=None,
    skills=None,
    limit=5,
    description_text=""
):
    # ------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------

    db_path = os.path.join(
        os.path.dirname(__file__),
        "career_counseling.db"
    )

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT * FROM Careers"
        )

        careers = cursor.fetchall()

        # --------------------------------------------------
        # LOAD NORMALIZED CAREER ↔ INTEREST RELATIONSHIPS
        # --------------------------------------------------

        career_interest_map = {}

        try:
            cursor.execute(
                """
                SELECT
                    ci.career_id,
                    i.interest_name
                FROM CareerInterests AS ci
                INNER JOIN Interests AS i
                    ON i.id = ci.interest_id
                ORDER BY ci.career_id, i.id
                """
            )

            for row in cursor.fetchall():
                career_interest_map.setdefault(
                    row["career_id"],
                    []
                ).append(
                    str(row["interest_name"] or "").strip()
                )

        except sqlite3.Error:
            # Backward-compatible fallback:
            # if the relationship tables do not exist,
            # the engine still uses Careers.interest.
            career_interest_map = {}

        # --------------------------------------------------
        # USER INPUT
        # --------------------------------------------------

        education = _normalize_education(education)
        normalized_field = _normalize_field(field)
        normalized_interest = _normalize_interest(interest)

        if skills is None:
            skills = []

        if isinstance(skills, str):
            skills = [
                item.strip()
                for item in skills.split(",")
                if item.strip()
            ]

        user_skills = [
            _normalize_skill(skill)
            for skill in skills
            if _normalize_skill(skill)
        ]

        try:
            marks = float(marks)
        except (ValueError, TypeError):
            marks = 0.0

        # NLP: skills mentioned in the free-text description are added
        # (at most 5), and the text is compared with every career (TF-IDF).
        description_text = str(description_text or "").strip()
        for inferred in nlp_engine.extract(description_text)["skills"][:5]:
            inferred = _normalize_skill(inferred)
            if inferred and inferred not in user_skills:
                user_skills.append(inferred)

        nlp_similarity = nlp_engine.career_similarities(
            description_text, careers
        )
        best_text_similarity = max(nlp_similarity.values(), default=0.0)

        recommended = []

        # --------------------------------------------------
        # SCORE EACH CAREER
        # --------------------------------------------------

        for career in careers:
            career_name = str(career["career_name"] or "").strip()

            if not career_name:
                continue

            career_key = career_name.lower()

            required_education_raw = str(
                career["education_required"] or ""
            ).strip()

            required_field_raw = str(
                career["field_required"] or ""
            ).strip()

            mapped_interest_values = career_interest_map.get(
                career["id"],
                []
            )

            if mapped_interest_values:
                required_interest_raw = ", ".join(mapped_interest_values)
            else:
                required_interest_raw = str(
                    career["interest"] or ""
                ).strip()

            required_skills_raw = str(
                career["required_skills"] or ""
            ).strip()

            description = str(career["description"] or "").strip()

            required_fields = [
                _normalize_field(value)
                for value in _split_values(required_field_raw)
            ]

            required_interests = [
                _normalize_interest(value)
                for value in _split_values(required_interest_raw)
            ]

            required_skills = [
                value.strip()
                for value in _split_values(required_skills_raw)
            ]

            field_is_flexible = (
                not required_fields
                or "any" in required_fields
            )

            try:
                minimum_percentage = float(
                    career["minimum_percentage"] or 0
                )
            except (ValueError, TypeError):
                minimum_percentage = 0.0

            if field_is_flexible:
                field_score = 0.65
            else:
                field_score = _best_match_score(
                    normalized_field,
                    required_fields
                )

            interest_score = _best_match_score(
                normalized_interest,
                required_interests
            )

            education_score = _education_match(
                education,
                required_education_raw
            )

            academic_score = _marks_match(
                marks,
                minimum_percentage
            )

            academic_requirement_met = (
                minimum_percentage <= 0
                or marks >= minimum_percentage
            )

            academic_shortfall = max(
                minimum_percentage - marks,
                0
            )

            (
                skill_score,
                matched_skills,
                missing_skills
            ) = _analyse_skills(
                user_skills,
                required_skills
            )

            data_similarity_score = _profile_similarity(
                normalized_field,
                normalized_interest,
                user_skills,
                career_name,
                required_fields,
                required_interests,
                required_skills,
                description
            )

            if normalized_interest == "public service":
                if career_key == "css officer":
                    career_is_eligible = True
                else:
                    career_is_eligible = (
                        "public service" in required_interests
                    )
            else:
                field_relevant = field_score >= 0.70
                interest_relevant = interest_score >= 0.70
                strong_skill_relevance = (
                    skill_score >= 0.50
                    and len(required_skills) > 0
                )
                profile_relevant = data_similarity_score >= 0.30
                career_is_eligible = (
                    field_relevant
                    or interest_relevant
                    or strong_skill_relevance
                    or profile_relevant
                )

            if not career_is_eligible:
                continue

            # ==================================================
            # FINAL AI SCORE
            # ==================================================

            # 10% weight: how well the student's own words match this career
            # (TF-IDF cosine). Without a description, the profile similarity
            # is used instead so this component is never a dead weight.
            if best_text_similarity > 0:
                text_match = nlp_similarity.get(career["id"], 0.0)
                specialization_score = min(
                    text_match / best_text_similarity, 1.0
                )
            else:
                text_match = 0.0
                specialization_score = min(data_similarity_score / 0.6, 1.0)

            field_points = round(field_score * 25, 2)
            interest_points = round(interest_score * 20, 2)
            education_points = round(education_score * 15, 2)
            academic_points = round(academic_score * 15, 2)
            skills_points = round(skill_score * 15, 2)
            specialization_points = round(
                specialization_score * 10,
                2
            )

            final_score = round(
                field_points
                + interest_points
                + education_points
                + academic_points
                + skills_points
                + specialization_points,
                2
            )
            final_score = min(final_score, 100.0)

            if final_score >= 85:
                suitability_label = "Excellent Fit"
            elif final_score >= 75:
                suitability_label = "Strong Fit"
            elif final_score >= 60:
                suitability_label = "Good Fit"
            elif final_score >= 45:
                suitability_label = "Moderate Fit"
            else:
                suitability_label = "Low Fit"

            reasons = []

            if field_score >= 0.95:
                reasons.append(
                    "Your field of study strongly matches this career."
                )
            elif field_score >= 0.70:
                reasons.append(
                    "Your field of study is relevant to this career."
                )
            elif field_is_flexible:
                reasons.append(
                    "This career accepts students from multiple academic fields."
                )

            if interest_score >= 0.95:
                reasons.append(
                    "Your interest strongly matches this career."
                )
            elif interest_score >= 0.70:
                reasons.append(
                    "Your interest is relevant to this career."
                )

            if education_score >= 1.0:
                reasons.append(
                    "Your education level satisfies the career requirement."
                )
            elif education_score > 0:
                reasons.append(
                    "Your education is close to the listed career requirement."
                )

            if minimum_percentage <= 0:
                reasons.append(
                    "No specific minimum academic percentage is listed for this career."
                )
            elif marks >= minimum_percentage:
                if marks >= minimum_percentage + 10:
                    reasons.append(
                        "Your academic performance comfortably exceeds the minimum requirement."
                    )
                else:
                    reasons.append(
                        "Your academic performance meets the minimum requirement for this career."
                    )
            else:
                reasons.append(
                    f"Your academic score is "
                    f"{academic_shortfall:.1f}% below the listed "
                    f"minimum requirement of "
                    f"{minimum_percentage:.1f}%."
                )

            if skill_score >= 0.60:
                reasons.append(
                    "Your skills strongly match the requirements of this career."
                )
            elif skill_score > 0:
                reasons.append(
                    "Some of your skills match this career's requirements."
                )

            if data_similarity_score >= 0.60:
                reasons.append(
                    "Your overall profile has strong similarity to this career's database profile."
                )
            elif data_similarity_score >= 0.30:
                reasons.append(
                    "Your overall profile has useful similarity to this career's database profile."
                )

            if best_text_similarity > 0 and specialization_score >= 0.75:
                reasons.append(
                    "Your own description closely matches this career."
                )

            match_details = {
                "user_field": normalized_field,
                "career_field": required_field_raw or "Flexible",
                "user_interest": normalized_interest,
                "career_interest": required_interest_raw or "Varies",
                "user_education": education,
                "career_education": required_education_raw or "No fixed requirement",
                "user_marks": marks,
                "minimum_marks": minimum_percentage,
                "matched_skills": sorted(matched_skills),
                "missing_skills": sorted(missing_skills),
                "academic_requirement_met": academic_requirement_met,
                "academic_shortfall": round(academic_shortfall, 2),
            }

            recommended.append({
                "career_name": career_name,
                "score": final_score,
                "suitability_label": suitability_label,
                "match_details": match_details,
               "score_breakdown": {
    "field": field_points,
    "interest": interest_points,
    "education": education_points,
    "academic": academic_points,
    "skills": skills_points,
    "specialization": specialization_points
},
                "education_eligible": (
                    not required_education_raw or education_score >= 1.0
                ),
                "required_education": required_education_raw,
                "field_required": required_field_raw,
                "career_id": career["id"],
                "interest": career["interest"],
                "holland_code": career["holland_code"] if "holland_code" in career.keys() else None,
                "description": career["description"] or "",
                "required_skills": career["required_skills"] or "",
                "future_scope": career["future_scope"] or "",
                "average_salary": career["average_salary"] or "",
                "learning_resources": career["learning_resources"] or "",
                "matched_skills": sorted(matched_skills),
                "missing_skills": sorted(missing_skills),
                "data_similarity": round(data_similarity_score, 4),
                "reasons": reasons,
            })

        recommended.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return recommended[:limit]

    except sqlite3.Error:
        return []
    finally:
        connection.close()