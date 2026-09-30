import pdfplumber

pdf_path = r"C:\Users\Admin\Desktop\ATS Resume Analyzer\Backend\DA Resume.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]

    words = page.extract_words()

    for word in words[:20]:
        print(word)

        from resume_parser import parse_resume, build_skill_evidence

parsed_resume = parse_resume(text)

skill_evidence = build_skill_evidence(
    parsed_resume
)

print("\nSKILL EVIDENCE:\n")

for item in skill_evidence:
    print(item)