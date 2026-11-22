import pdfplumber
import re
import pandas as pd
import os
from pathlib import Path

# Project root = folder above /scripts. Put result PDFs in data/results/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# =========================
# CREDIT MAPPINGS
# =========================

credits_sem1 = {
    "ABM101": 4, "ABM102": 4, "ACM101": 4, "ACM102": 4,
    "ACM103": 2, "ABM103": 2, "ABM104": 2, "HIL101": 1,
    "PDM101": 3, "ABW101": 2, "ACW101": 2, "RDC161": 1,
    "GKC161": 1, "ESC161": 2, "CEC161": 2
}

credits_sem2 = {
    "ABM201": 4, "ABM202": 4, "ABM203": 4, "ACM201": 4,
    "ACM202": 4, "ACM203": 2, "ACM204": 2, "ENL201": 2,
    "PYH261": 1, "PYH262": 1, "SYH261": 1, "SYH262": 1,
    "ACW201": 2,"ABW201": 2, "RDC261": 1, "RDC262": 1, "CAC261": 1,
    "CRC261": 2, "GKC261": 1
}

credits_sem3 = {
    "ABM301": 4, "ABM302": 4, "ACM301": 4, "ACM302": 4,
    "ACM303": 4, "ACM304": 2, "CLM301": 4, "SDC361": 2,
    "ABW301": 2, "ACW301": 2, "GKC361": 2, "ABM303": 4
}

credits_sem4 = {
    "ABM401": 4,
    "ABM402": 4,
    "ACM401": 4,
    "ACM402": 4,
    "ABM403": 4,
    "ACM403": 4,
    "ABM404": 2,
    "CAC461": 1,
    "GKC461": 1
}

semester_credits = {1: credits_sem1, 2: credits_sem2, 3: credits_sem3, 4: credits_sem4}

# =========================
# PATHS
# =========================

results_folder = DATA_DIR / "results"
output_csv     = DATA_DIR / "subjects_dataset.csv"

# =========================
# REGEX PATTERNS
# =========================

# Line 1: NAME (2+ uppercase words) followed by 2+ spaces then a subject code
name_line_pattern   = re.compile(r'^([A-Z][A-Z ]+?)\s{2,}([A-Z]{3}\d{3})')

# Line 2: roll number (5-8 digits) then caste category
rollno_line_pattern = re.compile(r'^(\d{5,8})\s+(GN|BC|SC|ST|OB)')

# Subject token — handles concatenated entries like "6.750ABM302 ..."
# Insert space before any subject code that is glued to a grade point
subject_pattern     = re.compile(
    r'([A-Z]{3}\d{3})\*?\s+([A-Z][A-Z+-]*|ABS)\s*([A-Z][A-Z+-]*|ABS)?\s+(\d+\.\d+)'
)

# Header lines repeated on every page of the result PDF
SKIP_CONTAINS = ("CONSOLIDATED CHART",)   # institute title line
SKIP_PREFIXES = (
    "ENTITY:", "CLASS:", "NAME /", "ENROLMENT",
    "SESSION:", "SEM:", "PAGE:"
)

# =========================
# TEXT EXTRACTION
# =========================

def extract_lines(pdf_path):
    """
    Use pdfplumber layout mode (works on Windows & Linux).
    layout=True + large layout_width_chars preserves column spacing.
    """
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(
                x_tolerance=3,
                y_tolerance=3,
                layout=True,
                layout_width_chars=200
            )
            if text:
                lines.extend(text.splitlines())
    return lines


# =========================
# SUBJECT FLUSHER
# =========================

def flush_student(name, roll, sem, buf):
    """Extract all subject rows from a student's buffered text block."""
    rows = []
    # Insert space before a subject code that is glued to a grade-point number
    # e.g.  "6.750ABM302"  →  "6.750 ABM302"
    buf = re.sub(r'(\d\.\d{3})([A-Z]{3}\d{3})', r'\1 \2', buf)
    buf = buf.replace("￾", " ")

    for m in subject_pattern.finditer(buf):
        code  = m.group(1)
        int_g = m.group(2)
        ext_g = m.group(3) or ""
        gp    = float(m.group(4))
        rows.append({
            "StudentName":   name,
            "RollNo":        roll,
            "Semester":      sem,
            "SubjectCode":   code,
            "Credits":       semester_credits[sem].get(code),
            "InternalGrade": int_g,
            "ExternalGrade": ext_g,
            "GradePoint":    gp,
        })
    return rows


# =========================
# PARSE ONE PDF
# =========================

def parse_pdf(pdf_path, sem):
    lines = extract_lines(pdf_path)

    all_rows       = []
    current_name   = None
    current_roll   = None
    subject_buffer = ""

    for raw_line in lines:
        line = raw_line.strip()

        # Skip blank or header lines
        if not line:
            continue
        if any(line.startswith(p) for p in SKIP_PREFIXES):
            continue
        if any(t in line for t in SKIP_CONTAINS):
            continue

        nm = name_line_pattern.match(line)
        rn = rollno_line_pattern.match(line)

        if nm:
            # Save the previous student before starting a new one
            if current_name and current_roll:
                all_rows.extend(flush_student(
                    current_name, current_roll, sem, subject_buffer
                ))

            current_name   = nm.group(1).strip()
            current_roll   = None
            subject_buffer = line          # name line already has subjects

        elif rn and current_name:
            current_roll    = rn.group(1)
            subject_buffer += " " + line   # roll line also has subjects

        elif current_name:
            # Continuation / enrolment / extra subject line
            subject_buffer += " " + line

    # Flush last student
    if current_name and current_roll:
        all_rows.extend(flush_student(
            current_name, current_roll, sem, subject_buffer
        ))

    return all_rows


# =========================
# MAIN LOOP
# =========================

all_results = []

pdf_files = sorted([f for f in os.listdir(results_folder) if f.endswith(".pdf")])

for file_name in pdf_files:

    sem_match = re.search(r'sem(\d+)', file_name.lower())
    if not sem_match:
        continue

    sem      = int(sem_match.group(1))
    pdf_path = os.path.join(results_folder, file_name)

    print(f"\nProcessing Semester {sem}: {file_name}")

    rows = parse_pdf(pdf_path, sem)
    all_results.extend(rows)
    print(f"  → {len(rows)} subject rows extracted")

# =========================
# BUILD & EXPORT DATAFRAME
# =========================

df = pd.DataFrame(all_results)

df.to_csv(output_csv, index=False)

print("\n===================================")
print(df.head(10).to_string())
print(f"\nTotal rows:      {len(df)}")
print(f"Unique students: {df['RollNo'].nunique()}")
print(f"Unique subjects: {df['SubjectCode'].nunique()}")
print(f"\nCSV saved at:\n{output_csv}")