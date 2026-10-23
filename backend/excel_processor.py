import pandas as pd
import os


# Required columns for certificate generation
REQUIRED_COLUMNS = [
    "Name",
    "Event",
    "Organization",
    "Date",
    "Achievement"
]


def read_excel(file_path):
    """
    Read Excel or CSV file and convert it into
    a list of dictionaries.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    # Remove accidental spaces from column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # Convert empty cells to empty strings
    df = df.fillna("")

    # Convert all values to strings
    df = df.astype(str)

    # Remove extra spaces from cell values
    for column in df.columns:
        df[column] = df[column].str.strip()

    return df.to_dict(orient="records")


def validate_columns(records):
    """
    Check whether all required columns exist.
    """

    if not records:
        return [
            "The Excel file does not contain any records."
        ]

    actual_columns = set(records[0].keys())

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in actual_columns
    ]

    if missing_columns:
        return [
            f"Missing column: {column}"
            for column in missing_columns
        ]

    return []


def validate_data(records):
    """
    Validate required data in every row.
    """

    errors = []

    for index, record in enumerate(records):

        row_number = index + 2

        for column in REQUIRED_COLUMNS:

            value = str(
                record.get(column, "")
            ).strip()

            if not value:

                errors.append(
                    f"Row {row_number}: {column} is empty"
                )

    return errors