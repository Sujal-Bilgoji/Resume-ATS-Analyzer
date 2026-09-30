import re
import spacy


# ============================================================
# LOAD SPACY
# ============================================================

nlp = spacy.load("en_core_web_sm")


# ============================================================
# TEST JOB DESCRIPTIONS
# ============================================================

job_descriptions = {

    "BACKEND SOFTWARE ENGINEER": """
Backend Software Engineer

Requirements

Strong knowledge of Python and Java.
Experience developing REST APIs and backend services.
Proficiency with PostgreSQL and database design.
Experience with Git and GitHub.
Knowledge of Docker and cloud deployment.
Understanding of object-oriented programming and software development.
Good problem-solving and communication skills.

Preferred Skills

Experience with AWS and Redis.
Knowledge of message queues and microservices architecture.
""",

    "FRONTEND DEVELOPER": """
Frontend Developer

Requirements

Strong knowledge of HTML, CSS, and JavaScript.
Experience building responsive web applications.
Proficiency with React and modern frontend development.
Experience with REST APIs and browser-based applications.
Knowledge of Git and GitHub.
Understanding of responsive design and accessibility.
Good problem-solving and communication skills.

Preferred Skills

Experience with TypeScript and Next.js.
Knowledge of UI testing and performance optimization.
""",

    "MACHINE LEARNING ENGINEER": """
Machine Learning Engineer

Requirements

Strong programming skills in Python.
Experience with machine learning and deep learning.
Knowledge of supervised and unsupervised learning.
Experience with NumPy, Pandas, and scikit-learn.
Understanding of data preprocessing and feature engineering.
Experience developing and deploying machine learning models.
Knowledge of model evaluation and statistical analysis.
Good problem-solving and analytical skills.

Preferred Skills

Experience with TensorFlow or PyTorch.
Knowledge of cloud platforms and MLOps.
""",

    "HR EXECUTIVE": """
HR Executive

Requirements

Experience in recruitment and employee onboarding.
Knowledge of payroll processing and attendance management.
Experience using HRMS and Microsoft Excel.
Understanding of employee relations and HR policies.
Ability to maintain employee records and documentation.
Experience supporting performance management processes.
Good communication and interpersonal skills.
Strong problem-solving and organizational skills.

Preferred Skills

Experience with recruitment software.
Knowledge of labor laws and HR analytics.
""",

    "MARKETING EXECUTIVE": """
Marketing Executive

Requirements

Experience in digital marketing and campaign management.
Knowledge of SEO and content marketing.
Experience with social media marketing and email marketing.
Ability to conduct market research and competitor analysis.
Experience creating marketing reports and presentations.
Knowledge of Google Analytics and advertising platforms.
Strong communication and creative thinking skills.
Good problem-solving abilities.

Preferred Skills

Experience with Google Ads and Meta Ads.
Knowledge of marketing automation and CRM platforms.
""",

    "ACCOUNTANT": """
Accountant

Requirements

Knowledge of accounting principles and financial reporting.
Experience with accounts payable and accounts receivable.
Experience preparing bank reconciliations and financial statements.
Proficiency with Microsoft Excel and accounting software.
Knowledge of GST and tax compliance.
Ability to maintain accurate financial records and documentation.
Strong analytical and problem-solving skills.
Good communication and organizational skills.

Preferred Skills

Experience with Tally or QuickBooks.
Knowledge of budgeting and financial analysis.
"""
}


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_whitespace(text):

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ============================================================
# SECTION DETECTION
# ============================================================

SECTION_NAMES = {

    "requirements": [
        "requirements",
        "required skills",
        "required qualifications",
        "qualifications",
        "minimum requirements",
        "essential requirements"
    ],

    "preferred": [
        "preferred skills",
        "preferred",
        "nice to have",
        "nice-to-have",
        "desired skills",
        "bonus skills"
    ]
}


def identify_section_heading(line):

    cleaned = clean_whitespace(line)

    lower = cleaned.lower()

    # Remove punctuation around headings
    lower = lower.strip(
        ":-–—"
    )

    for section, headings in SECTION_NAMES.items():

        for heading in headings:

            if lower == heading:

                return section

    return None


# ============================================================
# STAGE 1
# SECTION-AWARE JD PARSING
#
# IMPORTANT:
# We separate the JD into logical sections BEFORE NLP
# candidate extraction.
# ============================================================

def extract_jd_sections(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    sections = {
        "job_title": "",
        "requirements": [],
        "preferred": [],
        "other": []
    }

    if not lines:
        return sections

    # --------------------------------------------------------
    # First meaningful line = job title
    # --------------------------------------------------------

    sections["job_title"] = lines[0]

    current_section = "other"

    for line in lines[1:]:

        section = identify_section_heading(line)

        if section:

            current_section = section

            continue

        # ----------------------------------------------------
        # Ignore accidental section-heading fragments
        # ----------------------------------------------------

        if line.lower() in {
            "skills",
            "requirements",
            "preferred",
            "preferred skills"
        }:
            continue

        # ----------------------------------------------------
        # Store line according to section
        # ----------------------------------------------------

        if current_section == "requirements":

            sections["requirements"].append(line)

        elif current_section == "preferred":

            sections["preferred"].append(line)

        else:

            sections["other"].append(line)

    return sections


# ============================================================
# STAGE 2
# REQUIREMENT SENTENCE CLEANING
# ============================================================

def clean_requirement_sentence(sentence):

    sentence = clean_whitespace(sentence)

    # Remove bullet characters
    sentence = sentence.lstrip(
        "•-*"
    ).strip()

    # Remove ending punctuation
    sentence = sentence.rstrip(
        ".;:"
    )

    return sentence


# ============================================================
# STAGE 3
# RAW CANDIDATE EXTRACTION
#
# This stage receives ONLY actual requirement sentences.
# It no longer receives the entire JD.
# ============================================================

def extract_raw_candidates_from_sentence(sentence):

    doc = nlp(sentence)

    candidates = []

    # --------------------------------------------------------
    # Noun chunks
    # --------------------------------------------------------

    for chunk in doc.noun_chunks:

        phrase = clean_whitespace(
            chunk.text
        )

        if phrase:

            candidates.append(
                phrase
            )

    # --------------------------------------------------------
    # Named entities / proper nouns
    # --------------------------------------------------------

    for token in doc:

        if token.pos_ == "PROPN":

            phrase = token.text.strip()

            if phrase:

                candidates.append(
                    phrase
                )

    # --------------------------------------------------------
    # Preserve important technology expressions that may be
    # represented as multiple tokens.
    # --------------------------------------------------------

    # We do not hardcode specific technologies here.
    # We simply preserve noun chunks as spaCy found them.

    return candidates


def extract_raw_candidates(requirements):

    candidates = []

    for sentence in requirements:

        sentence = clean_requirement_sentence(
            sentence
        )

        if not sentence:
            continue

        sentence_candidates = (
            extract_raw_candidates_from_sentence(
                sentence
            )
        )

        candidates.extend(
            sentence_candidates
        )

    # --------------------------------------------------------
    # Remove exact duplicates
    # --------------------------------------------------------

    unique_candidates = []

    seen = set()

    for candidate in candidates:

        key = candidate.lower().strip()

        if key not in seen:

            seen.add(key)

            unique_candidates.append(
                candidate
            )

    return unique_candidates


# ============================================================
# CONJUNCTION HANDLING
# ============================================================

def split_conjunctions(candidate):

    candidate = clean_whitespace(
        candidate
    )

    lower = candidate.lower()

    # --------------------------------------------------------
    # Special shared-noun pattern
    #
    # supervised and unsupervised learning
    # →
    # supervised learning
    # unsupervised learning
    # --------------------------------------------------------

    if lower.endswith(" learning"):

        parts = re.split(
            r"\s+and\s+",
            candidate,
            flags=re.IGNORECASE
        )

        if len(parts) == 2:

            first = parts[0].strip()
            second = parts[1].strip()

            if first.lower() in {
                "supervised",
                "unsupervised"
            }:

                return [
                    first + " learning",
                    second
                ]

    # --------------------------------------------------------
    # Generic conjunction
    # --------------------------------------------------------

    doc = nlp(candidate)

    for token in doc:

        if token.dep_ == "cc":

            left = doc[
                :token.i
            ].text.strip()

            right = doc[
                token.i + 1:
            ].text.strip()

            result = []

            if left:
                result.append(left)

            if right:
                result.append(right)

            if result:
                return result

    return [candidate]


# ============================================================
# STAGE 4
# NORMALIZATION
# ============================================================

GENERIC_PREFIXES = [
    "strong knowledge of ",
    "good knowledge of ",
    "knowledge of ",
    "experience with ",
    "experience in ",
    "experience using ",
    "experience developing ",
    "experience building ",
    "experience creating ",
    "experience preparing ",
    "experience supporting ",
    "proficiency with ",
    "proficiency in ",
    "understanding of ",
    "ability to ",
    "strong ",
    "good ",
]


GENERIC_ADJECTIVES = {
    "strong",
    "good",
    "excellent",
    "accurate",
    "relevant",
    "effective",
    "successful",
    "modern",
}


def normalize_candidate(candidate):

    candidate = clean_whitespace(
        candidate
    )

    if not candidate:
        return ""

    # --------------------------------------------------------
    # Remove generic leading wording
    # --------------------------------------------------------

    changed = True

    while changed:

        changed = False

        lower = candidate.lower()

        for prefix in GENERIC_PREFIXES:

            if lower.startswith(prefix):

                candidate = candidate[
                    len(prefix):
                ].strip()

                changed = True

                break

    # --------------------------------------------------------
    # Remove generic descriptive adjective
    # --------------------------------------------------------

    words = candidate.split()

    while (
        len(words) > 1
        and words[0].lower()
        in GENERIC_ADJECTIVES
    ):

        words.pop(0)

    candidate = " ".join(words)

    # --------------------------------------------------------
    # Normalize "abilities"
    # --------------------------------------------------------

    candidate = re.sub(
        r"\s+abilities$",
        "",
        candidate,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Common soft-skill normalization
    # --------------------------------------------------------

    if candidate.lower() == "analytical":

        candidate = "analytical skills"

    elif candidate.lower() == "communication":

        candidate = "communication skills"

    elif candidate.lower() == "interpersonal":

        candidate = "interpersonal skills"

    elif candidate.lower() == "organizational":

        candidate = "organizational skills"

    # --------------------------------------------------------
    # Remove trailing punctuation
    # --------------------------------------------------------

    candidate = candidate.strip(
        " ,.;:()[]{}"
    )

    return clean_whitespace(
        candidate
    )


# ============================================================
# STAGE 5
# CANDIDATE FILTERING
# ============================================================

GENERIC_CANDIDATES = {
    "knowledge",
    "experience",
    "proficiency",
    "understanding",
    "ability",
    "skills",
    "programming skills",
    "technical skills",
    "professional skills"
}


def classify_candidate(candidate):

    normalized = normalize_candidate(
        candidate
    )

    if not normalized:

        return {
            "candidate": candidate,
            "normalized": "",
            "status": "REJECT",
            "reason": "Empty candidate"
        }

    lower = normalized.lower()

    # --------------------------------------------------------
    # Generic requirement wording
    # --------------------------------------------------------

    if lower in GENERIC_CANDIDATES:

        return {
            "candidate": candidate,
            "normalized": normalized,
            "status": "REJECT",
            "reason": "Generic requirement wording"
        }

    # --------------------------------------------------------
    # Single-word fragments that are clearly pieces of a
    # larger phrase
    #
    # We intentionally keep this conservative.
    # --------------------------------------------------------

    structural_fragments = {
        "backend",
        "frontend",
        "developer",
        "engineer",
        "requirements",
        "preferred",
        "skills",
        "microsoft",
        "google",
        "meta"
    }

    if lower in structural_fragments:

        return {
            "candidate": candidate,
            "normalized": normalized,
            "status": "REJECT",
            "reason": "Structural fragment"
        }

    # --------------------------------------------------------
    # Broad terms that may still be useful depending on
    # context.
    # --------------------------------------------------------

    review_terms = {
        "deployment",
        "accounts",
        "documentation",
        "software",
        "analysis",
        "design",
        "management",
        "reporting"
    }

    if lower in review_terms:

        return {
            "candidate": candidate,
            "normalized": normalized,
            "status": "REVIEW",
            "reason": "Potentially meaningful but context-dependent"
        }

    # --------------------------------------------------------
    # Otherwise keep
    # --------------------------------------------------------

    return {
        "candidate": candidate,
        "normalized": normalized,
        "status": "KEEP",
        "reason": "Potential job requirement"
    }


# ============================================================
# COMPLETE ANALYSIS PIPELINE
# ============================================================

def analyze_job_description(text):

    # --------------------------------------------------------
    # STEP 1: SECTION DETECTION
    # --------------------------------------------------------

    sections = extract_jd_sections(
        text
    )

    # --------------------------------------------------------
    # STEP 2: REQUIREMENT SENTENCES
    # --------------------------------------------------------

    requirement_sentences = []

    for sentence in sections[
        "requirements"
    ]:

        cleaned = clean_requirement_sentence(
            sentence
        )

        if cleaned:

            requirement_sentences.append(
                cleaned
            )

    preferred_sentences = []

    for sentence in sections[
        "preferred"
    ]:

        cleaned = clean_requirement_sentence(
            sentence
        )

        if cleaned:

            preferred_sentences.append(
                cleaned
            )

    # --------------------------------------------------------
    # STEP 3: RAW EXTRACTION
    # --------------------------------------------------------

    raw_required = extract_raw_candidates(
        requirement_sentences
    )

    raw_preferred = extract_raw_candidates(
        preferred_sentences
    )

    # --------------------------------------------------------
    # STEP 4: NORMALIZATION + FILTERING
    # --------------------------------------------------------

    def process_candidates(
        candidates
    ):

        results = []

        for candidate in candidates:

            split_candidates = (
                split_conjunctions(
                    candidate
                )
            )

            for split_candidate in split_candidates:

                result = classify_candidate(
                    split_candidate
                )

                results.append(
                    result
                )

        return results

    required_results = process_candidates(
        raw_required
    )

    preferred_results = process_candidates(
        raw_preferred
    )

    # --------------------------------------------------------
    # Remove duplicate normalized values while preserving
    # their first classification.
    # --------------------------------------------------------

    def unique_results(results):

        unique = []

        seen = set()

        for item in results:

            key = item[
                "normalized"
            ].lower()

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)

            unique.append(item)

        return unique

    required_results = unique_results(
        required_results
    )

    preferred_results = unique_results(
        preferred_results
    )

    return {

        "job_title":
            sections["job_title"],

        "requirements":
            requirement_sentences,

        "preferred":
            preferred_sentences,

        "required_candidates":
            required_results,

        "preferred_candidates":
            preferred_results
    }


# ============================================================
# PRINTING
# ============================================================

def print_candidate_results(
    candidates
):

    for item in candidates:

        print(
            f"[{item['status']}] "
            f"{item['normalized']}"
            f"  →  {item['reason']}"
        )


def print_results(
    role,
    results
):

    print("\n")
    print("=" * 90)
    print(role)
    print("=" * 90)

    # --------------------------------------------------------
    # JOB TITLE
    # --------------------------------------------------------

    print("\n[JOB TITLE]")
    print("-" * 90)

    print(
        "→",
        results["job_title"]
    )

    # --------------------------------------------------------
    # REQUIREMENT SENTENCES
    # --------------------------------------------------------

    print("\n[REQUIREMENT SENTENCES]")
    print("-" * 90)

    for sentence in results[
        "requirements"
    ]:

        print(
            "→",
            sentence
        )

    # --------------------------------------------------------
    # REQUIRED CANDIDATES
    # --------------------------------------------------------

    print("\n[REQUIRED CANDIDATES]")
    print("-" * 90)

    print_candidate_results(
        results[
            "required_candidates"
        ]
    )

    # --------------------------------------------------------
    # PREFERRED SENTENCES
    # --------------------------------------------------------

    print("\n[PREFERRED SENTENCES]")
    print("-" * 90)

    for sentence in results[
        "preferred"
    ]:

        print(
            "→",
            sentence
        )

    # --------------------------------------------------------
    # PREFERRED CANDIDATES
    # --------------------------------------------------------

    print("\n[PREFERRED CANDIDATES]")
    print("-" * 90)

    print_candidate_results(
        results[
            "preferred_candidates"
        ]
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 90)
    print("ATS JOB REQUIREMENT NLP - SECTION AWARE TEST")
    print("=" * 90)

    for role, jd in job_descriptions.items():

        results = analyze_job_description(
            jd
        )

        print_results(
            role,
            results
        )

    print("\n")
    print("=" * 90)
    print("TEST COMPLETE")
    print("=" * 90)