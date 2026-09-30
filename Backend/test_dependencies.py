import spacy

nlp = spacy.load("en_core_web_sm")


sentences = [
    "Strong programming skills in Python.",
    "Experience building responsive web applications.",
    "Experience developing REST APIs and backend services.",
    "Ability to conduct market research and competitor analysis.",
    "Experience preparing bank reconciliations and financial statements.",
    "Good communication and organizational skills.",
    "Knowledge of supervised and unsupervised learning.",
    "Experience developing and deploying machine learning models."
]


for sentence in sentences:

    print()
    print("=" * 80)
    print(sentence)
    print("=" * 80)

    doc = nlp(sentence)

    for token in doc:

        print(
            f"{token.text:20}"
            f"POS={token.pos_:8}"
            f"DEP={token.dep_:12}"
            f"HEAD={token.head.text}"
        )