"""Run the reproducible N5 vocabulary-example completion against the local DB."""

from database import connect
from n5_vocabulary_examples import ensure_n5_vocabulary_examples


def main() -> None:
    with connect() as db:
        completed = ensure_n5_vocabulary_examples(db)
    print(f"Completed {completed} N5 vocabulary examples.")


if __name__ == "__main__":
    main()
