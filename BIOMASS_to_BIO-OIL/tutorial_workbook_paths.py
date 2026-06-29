"""Workbook path selection for tutorial.py.

Choose one key (path1/path2/path3) and paste your Excel paths below.
"""

from pathlib import Path

# Resolve paths relative to this file so the project runs from any location.
_HERE = Path(__file__).resolve().parent

WORKBOOK_PATHS: dict[str, str] = {
    # You can use different paths if you are testing or editing the reference data.
    "path1": str(_HERE / "Feedstock_reference" / "Feedstock_table - USE THIS ONE.xlsx"),
    #"path2":
    #"path3":
}

# Set this to one of: path1, path2, path3, and it will be run when used in the tutorial.py script.
ACTIVE_WORKBOOK_PATH_KEY = "path1"


def get_selected_workbook_path() -> Path:
    """Return the configured workbook path from the selected key."""

    selected_key = ACTIVE_WORKBOOK_PATH_KEY.strip().lower()
    if selected_key not in WORKBOOK_PATHS:
        valid = ", ".join(sorted(WORKBOOK_PATHS.keys()))
        raise ValueError(
            f"Invalid ACTIVE_WORKBOOK_PATH_KEY '{ACTIVE_WORKBOOK_PATH_KEY}'. Expected one of: {valid}."
        )

    workbook_path = WORKBOOK_PATHS[selected_key].strip()
    if not workbook_path:
        raise ValueError(
            f"No path set for key '{selected_key}'. Set WORKBOOK_PATHS['{selected_key}'] in tutorial_workbook_paths.py."
        )

    return Path(workbook_path)
