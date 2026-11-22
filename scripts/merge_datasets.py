import pandas as pd
from pathlib import Path

# Project root = folder above /scripts. Put result PDFs in data/results/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# =========================
# LOAD CSV FILES
# =========================

sgpa_df = pd.read_csv(
    DATA_DIR / "sgpa_output.csv"
)

subjects_df = pd.read_csv(
    DATA_DIR / "subjects_dataset.csv"
)

# =========================
# CLEAN COLUMN NAMES
# =========================

sgpa_df.columns = sgpa_df.columns.str.strip()
subjects_df.columns = subjects_df.columns.str.strip()

# =========================
# CLEAN TEXT FIELDS
# =========================

sgpa_df["Name"] = (
    sgpa_df["Name"]
    .astype(str)
    .str.upper()
    .str.strip()
)

subjects_df["StudentName"] = (
    subjects_df["StudentName"]
    .astype(str)
    .str.upper()
    .str.strip()
)

# =========================
# SEMESTER FORMAT MATCH
# =========================

subjects_df["Semester"] = (
    "Sem " + subjects_df["Semester"].astype(str)
)

# =========================
# CLEAN ROLL NUMBERS
# =========================

sgpa_df["Roll No"] = (
    sgpa_df["Roll No"]
    .astype(str)
    .str.strip()
)

subjects_df["RollNo"] = (
    subjects_df["RollNo"]
    .astype(str)
    .str.strip()
)

# =========================
# MERGE DATASETS
# =========================

master_df = pd.merge(
    subjects_df,
    sgpa_df,
    left_on=["RollNo", "Semester"],
    right_on=["Roll No", "Semester"],
    how="left"
)

# =========================
# REMOVE DUPLICATE COLUMNS
# =========================

master_df = master_df.drop(
    columns=["Name", "Roll No"],
    errors="ignore"
)

# =========================
# SAVE MASTER DATASET
# =========================

output_path = (
    DATA_DIR / "master_dataset.csv"
)

master_df.to_csv(output_path, index=False)

# =========================
# PREVIEW
# =========================

print("\n==============================")
print(master_df.head())

print("\nTotal rows:", len(master_df))

print("\nColumns:")
print(master_df.columns.tolist())

print("\nMaster dataset created!")

print("\nSaved at:")
print(output_path)