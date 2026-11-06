from ai_engine import recommend_career


print("========================================")
print("AI CAREER COUNSELLING ENGINE TEST")
print("========================================")


# ==========================================================
# TEST 1 — COMPUTER SCIENCE STUDENT
# ==========================================================

print("\nTEST 1: Computer Science Student")
print("----------------------------------------")

results = recommend_career(
    education="BS",
    field="Computer Science",
    marks=85,
    interest="Programming",
    skills=[
        "Python",
        "Programming",
        "Machine Learning",
        "Deep Learning"
    ]
)

for index, career in enumerate(results, start=1):
    print(
        f"{index}. {career['career_name']} "
        f"- {career['score']}%"
    )


# ==========================================================
# TEST 2 — MEDICAL STUDENT
# ==========================================================

print("\nTEST 2: Medical Student")
print("----------------------------------------")

results = recommend_career(
    education="Intermediate",
    field="Medical",
    marks=90,
    interest="Biology",
    skills=[
        "Biology",
        "Patient Care",
        "Diagnosis"
    ]
)

for index, career in enumerate(results, start=1):
    print(
        f"{index}. {career['career_name']} "
        f"- {career['score']}%"
    )


# ==========================================================
# TEST 3 — CSS / PUBLIC SERVICE
# ==========================================================

print("\nTEST 3: CSS / Public Service")
print("----------------------------------------")

results = recommend_career(
    education="BS",
    field="Computer Science",
    marks=80,
    interest="Public Service",
    skills=[
        "Leadership",
        "Administration"
    ]
)

for index, career in enumerate(results, start=1):
    print(
        f"{index}. {career['career_name']} "
        f"- {career['score']}%"
    )


print("\n========================================")
print("AI ENGINE TEST COMPLETED")
print("========================================")