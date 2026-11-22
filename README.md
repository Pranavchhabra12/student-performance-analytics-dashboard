# Student Performance Analytics Dashboard

An end-to-end analytics pipeline that turns a college's semester result PDFs into an interactive Power BI dashboard for tracking student performance.

**Stack:** Python (pdfplumber, pypdf, regex, pandas) · Excel · Power BI · DAX

> The result data belongs to the institution and was used with permission. Raw PDFs, the datasets and the `.pbix` file are not included, and neither is the institution's name.

## Pipeline

```
Result PDFs ──► extract_sgpa.py ──► sgpa_output.csv ─────┐
(4 semesters,                                            ├─► merge_datasets.py ──► master_dataset.csv ──► Power BI
 2 programmes) ─► extract_results.py ─► subjects_dataset.csv ┘
```

| Step | Script | What it does |
|---|---|---|
| 1 | `scripts/extract_sgpa.py` | Parses each student's record (name, roll no., category, sex, enrolment, SGPA, result) from the consolidated result charts with `pypdf` + regex. It also splits SGPA values that come out of the PDF stuck together. |
| 2 | `scripts/extract_results.py` | Uses `pdfplumber` layout mode to read subject-level rows (subject code, internal grade, external grade, grade point) from multi-line student blocks. Handles codes glued to numbers, absent (`ABS`) entries and repeated page headers, then maps credits per semester. |
| 3 | `scripts/merge_datasets.py` | Cleans names, roll numbers and semester labels, then left-joins subject rows to SGPA rows on roll number + semester to build the master dataset. |

**Output:** around 5,300 subject-level records covering 120+ students, 55 subjects, 4 semesters and 2 B.Com programmes.

## Power BI model

All DAX is in [`dax/model.dax`](dax/model.dax).

- **Calculated table** `Student_SGPA`: one row per student per semester, used for trends and ranking
- **Calculated columns:** `Section` (A/B by roll-number range), `SemesterOrder`, `Result Status`, `SemesterKey`
- **Measures:** `Total Students`, `Passed Students`, `Pass Percentage` (ignores the result slicer), `Student Result`, `Student Rank` (dense SGPA rank among passed students in the same semester and section), `RankPoolCount`

## Dashboard

**Page 1 – Overview:** total students, overall pass rate, average SGPA, result distribution (donut), average grade point by subject, and a filterable student records table. Slicers for semester, section and result.

**Page 2 – Student Analysis:** pick a student to see their SGPA, result, class rank, SGPA trend across semesters and performance across subjects.

<!-- Add anonymised screenshots to /images and link them here -->

## Run it

```bash
pip install -r requirements.txt
# put result PDFs in data/results/, named with the semester, e.g. sem1_mains.pdf
python scripts/extract_sgpa.py
python scripts/extract_results.py
python scripts/merge_datasets.py
```

Then load `data/master_dataset.csv` into Power BI and add the DAX from `dax/model.dax`.

> The regex patterns and credit maps are written for one specific result-chart format. Other formats will need adjustments.
