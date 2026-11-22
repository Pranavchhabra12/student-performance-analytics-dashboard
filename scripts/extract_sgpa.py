"""
Extract current-semester SGPA from ALL PDFs inside results folder.
Saves the output CSV in the data/ folder.
"""

import re
import csv
import sys
import os
from pypdf import PdfReader
from pathlib import Path

# Project root = folder above /scripts. Put result PDFs in data/results/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# =========================
# GET TEXT FROM PDF
# =========================

def get_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# =========================
# SPLIT CONCATENATED SGPAs
# =========================

def split_sgpas(raw):
    return re.findall(r'\d\.\d{3}', raw)


# =========================
# PARSE STUDENTS
# =========================

def parse_students(text, sem_num):

    results = []

    pattern = re.compile(
        r'([A-Z][A-Z ]+?)\s+'                    # NAME
        r'(\d{7})\s+([A-Z]+)\s+([MF])\s+\d\s+'  # ROLL CAT SEX SEM
        r'(\d{6,7})\s+'                         # ENROLMENT
        r'([\d.\s]*)\s*([PFR])',                # SGPAs + RESULT
        re.MULTILINE
    )

    for m in pattern.finditer(text):

        name = m.group(1).strip()
        roll = m.group(2)
        category = m.group(3)
        sex = m.group(4)
        enrolment = m.group(5)
        sgpa_raw = m.group(6)
        result = m.group(7)

        floats = split_sgpas(sgpa_raw)

        current_sgpa = floats[-1] if floats else 'N/A'

        results.append({
            'Name': name,
            'Roll No': roll,
            'Enrolment': enrolment,
            'Category': category,
            'Sex': sex,
            'Semester': f"Sem {sem_num}",
            'SGPA': current_sgpa,
            'Result': result,
        })

    return results


# =========================
# MAIN
# =========================

def main():

    results_folder = DATA_DIR / "results"

    output = DATA_DIR / "sgpa_output.csv"

    pdf_files = [
        f for f in os.listdir(results_folder)
        if f.endswith(".pdf")
    ]

    pdf_files.sort()

    all_rows = []

    # =========================
    # PROCESS PDFs
    # =========================

    for file_name in pdf_files:

        pdf_path = os.path.join(results_folder, file_name)

        sem_match = re.search(
            r'sem(\d+)',
            file_name.lower()
        )

        if sem_match:
            sem = int(sem_match.group(1))
        else:
            continue

        print(f"\nSemester {sem}: {file_name}")

        text = get_text(pdf_path)

        rows = parse_students(text, sem)

        print(f"→ {len(rows)} students extracted")

        all_rows.extend(rows)

    # =========================
    # VALIDATION
    # =========================

    if not all_rows:
        print("No data extracted.")
        sys.exit(1)

    # =========================
    # SAVE CSV
    # =========================

    fieldnames = [
        'Name',
        'Roll No',
        'Enrolment',
        'Category',
        'Sex',
        'Semester',
        'SGPA',
        'Result'
    ]

    with open(output, 'w', newline='', encoding='utf-8') as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(all_rows)

    # =========================
    # FINAL OUTPUT
    # =========================

    print(f"\n✓ {len(all_rows)} records saved to:")
    print(output)


# =========================
# RUN
# =========================

if __name__ == '__main__':
    main()