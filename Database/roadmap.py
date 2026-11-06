"""
Career roadmap generator.

Builds a step-by-step path from the student's current education level to a
career: Intermediate group -> entry test -> degree -> postgraduate study ->
licence / professional step -> skills -> first job -> growth.

Each career belongs to a "track" that describes the usual route in Pakistan.
Careers added later by an admin fall back to a track chosen from their field
of study, so every career always gets a roadmap.

Rules such as minimum marks, age limits and test formats change from year to
year, so the roadmap points students to the official body to confirm them.
"""

EDUCATION_RANK = {
    "matric": 1, "o level": 1,
    "intermediate": 2, "a level": 2, "fsc": 2,
    "bs": 3, "bachelor": 3, "b.com": 3, "bcom": 3, "llb": 3, "bsc": 3,
    "ba": 3, "bba": 3, "mbbs": 3,
    "ms": 4, "mba": 4, "mphil": 4, "master": 4, "masters": 4, "msc": 4,
    "phd": 5,
}

ANY = "any"

TRACKS = {
    "mbbs": {
        "group": "FSc Pre-Medical (or A Level with Biology and Chemistry)",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "MDCAT",
        "test_note": "Held under PMDC rules. PMDC sets the minimum FSc Pre-Medical percentage "
                     "(raised to 65% from 2026) and other conditions, so check its current notice.",
        "degree": "MBBS", "years": 5,
        "after": [("House job and PMDC registration",
                   "One year of supervised house job, then register with PMDC to practise.", 1)],
        "first_job": "House Officer, then Medical Officer",
        "growth": "Specialise through FCPS (CPSP) or a postgraduate degree to become a consultant.",
    },
    "bds": {
        "group": "FSc Pre-Medical (or A Level with Biology and Chemistry)",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "MDCAT",
        "test_note": "Held under PMDC rules; check PMDC's current notice for the minimum marks.",
        "degree": "BDS (Bachelor of Dental Surgery)", "years": 4,
        "after": [("House job and PMDC registration",
                   "One year of house job, then register with PMDC.", 1)],
        "first_job": "Dental Surgeon (hospital or clinic)",
        "growth": "Specialise (FCPS or MDS) in orthodontics, oral surgery or another field, or open a clinic.",
    },
    "pharmd": {
        "group": "FSc Pre-Medical (or A Level with Biology and Chemistry)",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University entry test (varies by university)",
        "degree": "Pharm-D (Doctor of Pharmacy)", "years": 5,
        "after": [("Register with the Pharmacy Council of Pakistan",
                   "Registration is needed to work as a pharmacist.", 0)],
        "first_job": "Hospital, community or industry pharmacist",
        "growth": "Clinical pharmacy, pharmaceutical industry, quality control or regulatory affairs.",
    },
    "psychology": {
        "group": "FSc Pre-Medical or FA (with Psychology if available)",
        "group_fields": {"Medical", "Arts"},
        "test": "University entry test",
        "degree": "BS Psychology", "years": 4,
        "postgrad": ("MS Clinical Psychology", 2),
        "first_job": "Assistant psychologist or counsellor",
        "growth": "Clinical psychologist, school or organisational psychologist, private practice or research.",
    },
    "health": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University entry test",
        "degree": "BS in the relevant health science", "years": 4,
        "first_job": "Entry-level role in a hospital or clinic",
        "growth": "Senior and specialist roles, or a master's degree.",
    },
    "engineering": {
        "group": "FSc Pre-Engineering (or A Level with Maths and Physics)",
        "group_fields": {"Engineering"},
        "group_hint": "Pre-Engineering needs the Science group with Maths in Matric.",
        "test": "ECAT (UET), NUST NET or the university's own entry test",
        "degree": "BSc / BE {discipline} (PEC-accredited)", "years": 4,
        "after": [("Register with Pakistan Engineering Council (PEC)",
                   "Register as a Registered Engineer after graduating.", 0)],
        "first_job": "Trainee or Junior {career}",
        "growth": "Senior engineer, project manager, and Professional Engineer status with PEC.",
    },
    "computing": {
        "group": "ICS (Computer Science) or FSc Pre-Engineering",
        "group_fields": {"Computer Science", "Engineering"},
        "group_hint": "ICS and Pre-Engineering usually need the Science group with Maths in Matric; ask your college about switching. Some universities also accept Pre-Medical with extra Maths courses.",
        "test": "University entry test (for example NUST NET, FAST or NTS)",
        "degree": "BS Computer Science, Software Engineering or IT", "years": 4,
        "postgrad": ("MS Computer Science / Artificial Intelligence", 2),
        "first_job": "Internship, then Junior {career}",
        "growth": "Senior {career}, team lead, then architect or engineering manager.",
    },
    "accounting": {
        "group": "I.Com (or ICS / FA with Maths or Economics)",
        "group_fields": {"Commerce", "Computer Science", "Arts"},
        "test": "University entry test",
        "degree": "BS Accounting & Finance (or B.Com)", "years": 4,
        "after": [("Professional qualification",
                   "CA through ICAP or ACCA greatly improves job options (optional, 2-3 years alongside work).", 0)],
        "first_job": "Audit or accounts trainee",
        "growth": "Senior accountant, finance manager, then CFO.",
    },
    "finance": {
        "group": "I.Com or ICS (Maths is helpful)",
        "group_fields": {"Commerce", "Computer Science", "Engineering"},
        "test": "University entry test",
        "degree": "BS Accounting & Finance, BBA (Finance) or BS Economics", "years": 4,
        "after": [("Professional certification (optional)",
                   "CFA or ACCA strengthens a finance career.", 0)],
        "first_job": "Junior {career} or finance trainee",
        "growth": "Senior analyst, portfolio or finance manager.",
    },
    "economics": {
        "group": "I.Com, ICS or FA with Economics and Maths",
        "group_fields": {"Commerce", "Computer Science", "Arts"},
        "test": "University entry test",
        "degree": "BS Economics", "years": 4,
        "postgrad": ("MS / MPhil Economics", 2),
        "first_job": "Research assistant or junior economist",
        "growth": "Economist at banks, government, think tanks or international organisations.",
    },
    "business": {
        "group": "I.Com (any Intermediate group is accepted)",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BBA (Bachelor of Business Administration)", "years": 4,
        "postgrad": ("MBA", 2),
        "first_job": "Management trainee",
        "growth": "{career}, then senior management roles.",
    },
    "law": {
        "group": "Any Intermediate group (FA is common)",
        "group_fields": ANY,
        "test": "LAT (HEC's Law Admission Test)",
        "test_note": "LAT is required for admission to the LLB programme; check HEC for the current schedule.",
        "degree": "5-year LLB", "years": 5,
        "after": [("Enrol as an advocate",
                   "Complete the required apprenticeship and enrol with the Bar Council to practise.", 1)],
        "first_job": "Associate at a law firm or junior advocate",
        "growth": "High Court advocate, legal advisor, or the judiciary through competitive exams.",
    },
    "design": {
        "group": "FA, ICS or any group (your portfolio matters most)",
        "group_fields": ANY,
        "test": "University aptitude test and portfolio review",
        "degree": "BS Graphic Design, Fine Arts, Animation or Multimedia", "years": 4,
        "first_job": "Junior {career}",
        "growth": "Senior designer, art director or freelance studio.",
    },
    "media": {
        "group": "FA or any Intermediate group",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS Mass Communication, Media Studies or English", "years": 4,
        "first_job": "Junior {career} or intern at a media organisation",
        "growth": "Senior {career}, editor, or producer.",
    },
    "teaching": {
        "group": "The Intermediate group of the subject you want to teach",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS in your teaching subject", "years": 4,
        "after": [("B.Ed (Bachelor of Education)",
                   "Usually required for school teaching posts.", 2)],
        "first_job": "School teacher (government posts are filled through tests such as NTS or the public service commission)",
        "growth": "Senior teacher, head of department, then principal.",
    },
    "lecturer": {
        "group": "The Intermediate group of the subject you want to teach",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS in your subject", "years": 4,
        "postgrad": ("MS / MPhil in your subject", 2),
        "after": [("Lecturer recruitment test",
                   "Government colleges hire lecturers through FPSC or provincial public service commissions.", 0)],
        "first_job": "Lecturer",
        "growth": "Assistant Professor and above (usually needs a PhD).",
    },
    "css": {
        "group": "Any Intermediate group",
        "group_fields": ANY,
        "test": None,
        "degree": "Any bachelor's degree", "years": 4,
        "after": [("CSS competitive exam (FPSC)",
                   "Stages: preliminary MCQ test, written exam, psychological assessment and interview. "
                   "The age limit is currently 21-30 and an increase has been proposed, so check FPSC's current rules.", 1),
                  ("Training at the Civil Services Academy",
                   "Successful candidates are allocated a service group and trained before their first posting.", 1)],
        "first_job": "Officer in your allocated service group (for example Assistant Commissioner or ASP)",
        "growth": "Promotion through the service grades to senior government positions.",
    },
    "public_admin": {
        "group": "Any Intermediate group",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS Public Administration, Political Science or a related subject", "years": 4,
        "postgrad": ("MPA / MS Public Administration", 2),
        "after": [("Government recruitment",
                   "Posts are filled through FPSC or provincial public service commissions.", 0)],
        "first_job": "Administrative officer",
        "growth": "Senior administrative and policy roles.",
    },
    "nursing": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University or nursing college entry test",
        "degree": "BSN (Bachelor of Science in Nursing)", "years": 4,
        "after": [("Register with the Pakistan Nursing and Midwifery Council (PNMC)",
                   "Registration is required to practise as a nurse.", 0)],
        "first_job": "Staff Nurse in a hospital",
        "growth": "Charge nurse, nursing supervisor, specialist nurse (MSN), or nursing teacher.",
    },
    "physio": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University entry test",
        "degree": "DPT (Doctor of Physical Therapy)", "years": 5,
        "after": [("Register with the Allied Health Professionals Council (AHPC)",
                   "Allied health professionals must now register with AHPC to work.", 0)],
        "first_job": "Physiotherapist in a hospital, clinic or sports team",
        "growth": "Specialise (sports, neuro or paediatric physiotherapy), MS, or open a clinic.",
    },
    "allied": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University entry test",
        "degree": "BS in the relevant allied health science", "years": 4,
        "after": [("Register with the Allied Health Professionals Council (AHPC)",
                   "Allied health professionals must now register with AHPC to work.", 0)],
        "first_job": "{career} in a hospital or diagnostic lab",
        "growth": "Senior technologist, lab or department manager, or MS in the specialty.",
    },
    "vet": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "University entry test",
        "degree": "DVM (Doctor of Veterinary Medicine)", "years": 5,
        "after": [("Register with the Pakistan Veterinary Medical Council (PVMC)",
                   "Registration is required to practise as a veterinarian.", 0)],
        "first_job": "Veterinary Officer (livestock department, farm or clinic)",
        "growth": "Specialise (surgery, poultry, dairy), research, or your own clinic.",
    },
    "public_health": {
        "group": "FSc Pre-Medical",
        "group_fields": {"Medical"},
        "test": "University entry test",
        "degree": "MBBS or a BS in a health science", "years": 4,
        "postgrad": ("MPH (Master of Public Health)", 2),
        "first_job": "Public health officer with a health department, NGO or international agency",
        "growth": "Programme manager, epidemiologist, or health policy roles.",
    },
    "agriculture": {
        "group": "FSc Pre-Medical or Pre-Engineering",
        "group_fields": {"Medical", "Engineering"},
        "test": "University entry test (for example at an agriculture university)",
        "degree": "BSc (Hons) Agriculture", "years": 4,
        "first_job": "Agriculture Officer (government) or field officer in an agri company",
        "growth": "Senior agriculture officer, research scientist, or agribusiness.",
    },
    "science": {
        "group": "FSc Pre-Medical, Pre-Engineering or ICS (the group closest to your subject)",
        "group_fields": {"Medical", "Engineering", "Computer Science"},
        "test": "University entry test",
        "degree": "BS in your science subject", "years": 4,
        "postgrad": ("MS / MPhil in your subject", 2),
        "first_job": "Junior {career} or research assistant",
        "growth": "Senior scientist, research lead, or PhD and university teaching.",
    },
    "actuarial": {
        "group": "FSc Pre-Engineering or ICS (strong Maths needed)",
        "group_fields": {"Engineering", "Computer Science"},
        "test": "University entry test",
        "degree": "BS Actuarial Science, Statistics or Mathematics", "years": 4,
        "after": [("Professional actuarial exams",
                   "Exams from bodies such as the Society of Actuaries or the Institute and Faculty of Actuaries, taken alongside work.", 0)],
        "first_job": "Actuarial analyst at an insurance company",
        "growth": "Qualified actuary, chief actuary, or risk management roles.",
    },
    "architecture": {
        "group": "FSc Pre-Engineering (some universities accept other groups with an aptitude test)",
        "group_fields": {"Engineering", "Computer Science", "Arts"},
        "test": "University entry test and design aptitude test",
        "degree": "B.Arch (Bachelor of Architecture, PCATP-accredited)", "years": 5,
        "after": [("Register with the Pakistan Council of Architects and Town Planners (PCATP)",
                   "Registration is required to practise as an architect.", 0)],
        "first_job": "Junior Architect at a design firm",
        "growth": "Project architect, principal architect, or your own practice.",
    },
    "planning": {
        "group": "FSc Pre-Engineering or ICS",
        "group_fields": {"Engineering", "Computer Science"},
        "test": "University entry test",
        "degree": "BS City and Regional Planning", "years": 4,
        "after": [("Register with the Pakistan Council of Architects and Town Planners (PCATP)",
                   "Registration is required to practise as a town planner.", 0)],
        "first_job": "Assistant Planner (development authority or consultancy)",
        "growth": "Senior planner, urban policy or transport planning roles.",
    },
    "ca": {
        "stage": "Qualification",
        "group": "I.Com, ICS or any Intermediate group",
        "group_fields": ANY,
        "test": None,
        "degree": "CA qualification through ICAP (PRC, CAF, CFAP and the final case study)", "years": 4,
        "after": [("Training contract (articleship)",
                   "Usually 2.5 to 4 years with an ICAP-approved firm, done alongside the later exams.", 1)],
        "first_job": "Chartered Accountant at an audit firm, bank or company",
        "growth": "Audit manager, finance director, CFO, or partner in a firm.",
    },
    "army": {
        "stage": "Training",
        "group": "Any Intermediate group (FA or FSc)",
        "group_fields": ANY,
        "test": "Initial tests and ISSB (Inter Services Selection Board)",
        "test_note": "PMA Long Course has required at least 60% in FA/FSc, an age of about 17-22, "
                     "and medical and physical standards. Check joinpakarmy.gov.pk for the current course.",
        "degree": "PMA Long Course at the Pakistan Military Academy, Kakul", "years": 2,
        "first_job": "Commissioned officer (Second Lieutenant)",
        "growth": "Promotion through the ranks: Captain, Major, Lieutenant Colonel and above.",
    },
    "pilot": {
        "stage": "Training",
        "group": "FSc Pre-Engineering (Physics and Maths)",
        "group_fields": {"Engineering", "Computer Science"},
        "test": "Flying school entry test and a Class 1 aviation medical",
        "test_note": "Check entry rules with approved flying schools and the Pakistan Civil Aviation Authority.",
        "degree": "Commercial Pilot Licence (CPL) training at an approved flying school", "years": 2,
        "after": [("Airline type rating",
                   "Airlines train you on a specific aircraft type before you fly passengers.", 0)],
        "first_job": "First Officer (co-pilot)",
        "growth": "Senior First Officer, then Captain.",
    },
    "judge": {
        "group": "Any Intermediate group (FA is common)",
        "group_fields": ANY,
        "test": "LAT (HEC's Law Admission Test)",
        "degree": "5-year LLB", "years": 5,
        "after": [("Enrol as an advocate and gain experience",
                   "Practise in the courts; judicial posts usually ask for some years of practice.", 2),
                  ("Civil Judge competitive exam",
                   "Held by the provincial High Court or public service commission. Check the current eligibility rules.", 1)],
        "first_job": "Civil Judge / Judicial Magistrate",
        "growth": "Senior Civil Judge, Additional and District and Sessions Judge.",
    },
    "hospitality": {
        "group": "Any Intermediate group",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS Hospitality and Tourism Management", "years": 4,
        "first_job": "Management trainee at a hotel",
        "growth": "Department head, hotel manager, then general manager.",
    },
    "culinary": {
        "stage": "Training",
        "group": "Any Intermediate group",
        "group_fields": ANY,
        "test": None,
        "degree": "Culinary arts diploma or certificate", "years": 1,
        "first_job": "Commis chef (junior cook) in a restaurant or hotel",
        "growth": "Chef de partie, sous chef, head chef, or your own restaurant.",
    },
    "social_work": {
        "group": "FA or any Intermediate group",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "BS Social Work", "years": 4,
        "first_job": "Field or case officer at an NGO or social welfare department",
        "growth": "Programme manager, MS Social Work, or policy roles.",
    },
    "radiology": {
        "group": "FSc Pre-Medical (or A Level with Biology and Chemistry)",
        "group_fields": {"Medical"},
        "group_hint": "Pre-Medical needs Biology in Matric (Science group).",
        "test": "MDCAT",
        "test_note": "Held under PMDC rules; check PMDC's current notice for the minimum marks.",
        "degree": "MBBS", "years": 5,
        "postgrad": ("Specialist training in radiology (FCPS through CPSP)", 4),
        "after": [("House job and PMDC registration",
                   "One year of supervised house job before specialist training.", 1)],
        "first_job": "Radiology resident, then Consultant Radiologist",
        "growth": "Sub-specialise (for example interventional or neuro radiology), or lead a department.",
    },
    "entrepreneur": {
        "group": "Any Intermediate group (I.Com is helpful)",
        "group_fields": ANY,
        "test": None,
        "degree": "BBA or any bachelor's degree (helpful but not required)", "years": 4,
        "first_job": "Start a small venture, or join a startup to learn",
        "growth": "Grow the business, join an incubator or accelerator, and raise investment.",
    },
    "general": {
        "group": "The Intermediate group closest to this field",
        "group_fields": ANY,
        "test": "University entry test",
        "degree": "A bachelor's degree in {field}", "years": 4,
        "postgrad": ("A master's degree in the same field", 2),
        "first_job": "Entry-level {career}",
        "growth": "Senior and leadership roles.",
    },
}

NAME_TRACK = {
    "doctor": "mbbs", "dentist": "bds", "pharmacist": "pharmd",
    "psychologist": "psychology", "lawyer": "law", "css officer": "css",
    "public administration officer": "public_admin", "teacher": "teaching",
    "lecturer": "lecturer", "accountant": "accounting",
    "financial analyst": "finance", "economist": "economics",
    "bank manager": "business", "marketing manager": "business",
    "human resources manager": "business", "content writer": "media",
    "journalist": "media", "graphic designer": "design", "animator": "design",
    "nurse": "nursing", "physiotherapist": "physio",
    "medical lab technologist": "allied", "radiologic technologist": "allied",
    "nutritionist": "allied", "veterinary doctor": "vet",
    "public health specialist": "public_health", "agriculture officer": "agriculture",
    "biotechnologist": "science", "microbiologist": "science", "chemist": "science",
    "physicist": "science", "geologist": "science", "statistician": "science",
    "actuary": "actuarial", "architect": "architecture", "urban planner": "planning",
    "chartered accountant": "ca", "banking officer": "finance",
    "business analyst": "business", "digital marketing specialist": "business",
    "supply chain manager": "business", "product manager": "computing",
    "hotel manager": "hospitality", "army officer": "army",
    "commercial pilot": "pilot", "civil judge": "judge", "social worker": "social_work",
    "fashion designer": "design", "interior designer": "design",
    "video editor": "media", "chef": "culinary",
    "entrepreneur": "entrepreneur", "business consultant": "business",
    "it project manager": "computing", "photographer": "design", "art director": "design",
    "music producer": "media", "industrial engineer": "engineering", "radiologist": "radiology",
}

# Exact degree names for careers that share a track
DEGREE_OVERRIDE = {
    "medical lab technologist": "BS Medical Laboratory Technology",
    "radiologic technologist": "BS Medical Imaging Technology",
    "nutritionist": "BS Human Nutrition and Dietetics",
    "biotechnologist": "BS Biotechnology",
    "microbiologist": "BS Microbiology",
    "chemist": "BS Chemistry",
    "physicist": "BS Physics",
    "geologist": "BS Geology",
    "statistician": "BS Statistics",
    "fashion designer": "BS Fashion Design",
    "interior designer": "BS Interior Design",
    "video editor": "BS Film and TV / Media Production (or short courses and a strong portfolio)",
    "business analyst": "BBA or BS Business Analytics",
    "digital marketing specialist": "BBA (Marketing) or BS Digital Marketing",
    "supply chain manager": "BBA or BS Supply Chain Management",
    "banking officer": "BS Banking and Finance, BBA or B.Com",
    "photographer": "BS Photography or Fine Arts (or short courses and a strong portfolio)",
    "art director": "BS Graphic Design or Fine Arts",
    "music producer": "Music production courses and a strong portfolio (a degree is optional)",
    "business consultant": "BBA, BS Economics or BS Accounting & Finance",
}

FIELD_TRACK = {
    "computer science": "computing", "engineering": "engineering",
    "medical": "health", "business": "business", "commerce": "accounting",
    "arts": "design", "education": "teaching", "law": "law",
    "public administration": "public_admin", "any": "css",
    "sciences": "science",
}


def _rank(text):
    return EDUCATION_RANK.get(str(text or "").strip().lower(), 3)


def _track_for(career):
    name = str(career.get("career_name", "")).strip().lower()
    if name in NAME_TRACK:
        return NAME_TRACK[name]
    field = str(career.get("field_required", "")).strip().lower()
    return FIELD_TRACK.get(field, "general")


def _fill(text, career, field):
    name = career.get("career_name", "")
    return (text or "").format(
        career=name,
        discipline=name.replace("Engineer", "Engineering").strip(),
        field=field or "this field",
    )


def _fits(group_fields, student_field):
    return group_fields == ANY or student_field in group_fields


def build_roadmap(career, student_education, student_field, missing_skills=None):
    """Return the roadmap for one career as a dict with steps and a summary."""
    track_key = _track_for(career)
    track = TRACKS[track_key]
    career_field = career.get("field_required") or ""
    level = _rank(student_education)
    target_level = _rank(career.get("education_required") or career.get("required_education"))
    needs_postgrad = target_level >= 4 and "postgrad" in track
    if target_level >= 4 and "postgrad" not in track:
        track = dict(track, postgrad=("A master's degree (MS / MPhil)", 2))
        needs_postgrad = True

    steps = []

    def add(kind, title, detail, years=0, done=False, warn=None):
        steps.append({"kind": kind, "title": title, "detail": detail,
                      "years": years, "done": done, "warn": warn})

    add("start", f"You are here: {student_education}",
        f"Field of study: {student_field}." if student_field
        else "Any Matric group that leads to the Intermediate group below.", done=True)

    # 1. Intermediate group (only for Matric / O Level students)
    if level <= 1:
        warn = None
        if student_field and not _fits(track["group_fields"], student_field):
            warn = f"Your Matric group ({student_field}) is not the usual route. " + track.get(
                "group_hint", "Ask your school which Intermediate group you can join.")
        add("school", f"Intermediate: {track['group']}",
            "Two years. Aim for strong marks; they count towards university admission.",
            years=2, warn=warn)

    # 2. Entry test and degree (for Matric and Intermediate students)
    name_key = str(career.get("career_name", "")).strip().lower()
    degree = _fill(DEGREE_OVERRIDE.get(name_key, track["degree"]), career, career_field)
    if level <= 2:
        if track.get("test"):
            add("test", f"Entry test: {track['test']}",
                track.get("test_note", "Prepare during your final Intermediate year; "
                                       "admission is based on test and Intermediate marks."))
        warn = None
        if level == 2 and not _fits(track["group_fields"], student_field):
            warn = (f"This degree usually needs {track['group']}. You studied {student_field}, "
                    "so ask universities about eligibility or bridging courses.")
        stage = track.get("stage", "Degree")
        duration = (f"{track['years']} years of university study." if stage == "Degree"
                    else f"About {track['years']} year{'s' if track['years'] != 1 else ''}.")
        add("degree", f"{stage}: {degree}", duration, years=track["years"], warn=warn)
    else:
        warn = None
        professional = track_key in {"mbbs", "bds", "pharmd", "engineering", "law"}
        if professional and career_field and student_field != career_field:
            warn = f"This career needs a {degree}. Your current degree in {student_field} does not qualify directly."
        add("degree", f"Degree: {student_education} in {student_field}",
            "Complete your degree with good grades.", done=not warn, warn=warn)

    # 3. Postgraduate study
    if needs_postgrad and level < 4:
        name, years = track["postgrad"]
        add("postgrad", f"Postgraduate: {_fill(name, career, career_field)}",
            "Required for this career.", years=years)

    # 4. Licence, professional exam or certification
    for title, detail, years in track.get("after", []):
        add("licence", title, detail, years=years)

    # 5. Skills to build
    missing = [s for s in (missing_skills or []) if s]
    if missing:
        resources = career.get("learning_resources")
        detail = "Learn alongside your studies" + (f" with {resources}." if resources else ".")
        add("skills", "Build these skills: " + ", ".join(missing), detail)

    # 6. First job and growth
    add("job", f"First job: {_fill(track['first_job'], career, career_field)}",
        "Build a portfolio, do internships and apply through the job links in this report.")
    add("growth", "Grow", _fill(track["growth"], career, career_field))

    for index, step in enumerate(steps):
        step["number"] = index
    current = next((s for s in steps if not s["done"]), None)
    if current:
        current["current"] = True
    years_to_job = sum(s["years"] for s in steps if not s["done"])
    if years_to_job:
        summary = f"About {years_to_job} year{'s' if years_to_job != 1 else ''} from now to your first job"
    else:
        summary = "You can start applying for internships and junior roles now"
    return {"steps": steps, "years": years_to_job, "summary": summary,
            "track": track_key}


def required_subjects(career):
    """What to study for a career (SRS FR9 'required subjects')."""
    track = TRACKS[_track_for(career)]
    name_key = str(career.get("career_name", "")).strip().lower()
    field = career.get("field_required") or ""
    result = {
        "intermediate": track["group"],
        "test": track.get("test"),
        "degree": _fill(DEGREE_OVERRIDE.get(name_key, track["degree"]), career, field),
        "years": track["years"],
        "stage": track.get("stage", "Degree"),
        "postgrad": None,
        "licence": [title for title, _, _ in track.get("after", [])],
    }
    if _rank(career.get("education_required")) >= 4:
        postgrad = track.get("postgrad", ("A master's degree (MS / MPhil)", 2))
        result["postgrad"] = _fill(postgrad[0], career, field)
    return result
