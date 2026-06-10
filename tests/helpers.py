from pathlib import Path
from uuid import uuid4


def temp_db_path() -> str:
    output = Path(".test-output")
    output.mkdir(exist_ok=True)
    return str(output / f"{uuid4().hex}.db")

