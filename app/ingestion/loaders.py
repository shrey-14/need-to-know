# Per-source-type loaders: markdown docs (header-aware) and hr_data.csv (row-based). Ingestion phase.
from pathlib import Path
from langchain_core.documents import Document
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

def row_to_sentence(row) -> str:
    return (
        f"{row['full_name']} (employee ID {row['employee_id']}) works as a "
        f"{row['role']} in the {row['department']} department (manager ID {row['manager_id']}), based in {row['location']}. "
        f"Their personal details includes their email address: {row['email']}, and their date of birth is {row['date_of_birth']}. "
        f"They joined on {row['date_of_joining']} and earn a salary of "
        f"₹{row['salary']:,.2f}. They have leave balance of {row['leave_balance']} days "
        f"and have taken {row['leaves_taken']} leaves so far, with an attendance rate of "
        f"{row['attendance_pct']}%. Their latest performance rating is "
        f"{row['performance_rating']}, last reviewed on {row['last_review_date']}."
    )


def load_documents() -> list[Document]:

    all_documents = []

    for category_folder in DATA_DIR.iterdir():
        if Path(category_folder).is_dir():
            category = category_folder.name
            for file in category_folder.iterdir():
                if Path(file).is_file():
                    if file.suffix in [".md", ".txt"]:
                        text = file.read_text(encoding="utf-8")
                        doc = Document(page_content=text, metadata={"source": str(file), "category": category})
                        all_documents.append(doc)

                    elif file.suffix == ".csv":
                        df = pd.read_csv(file)
                        for _, row in df.iterrows():
                            sentence = row_to_sentence(row)
                            doc = Document(
                                page_content=sentence,
                                metadata={"category": category, "source": str(file), "employee_id": row["employee_id"]},
                            )
                            all_documents.append(doc)

                    else:
                        continue

    return all_documents

