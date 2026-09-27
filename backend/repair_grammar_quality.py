"""Apply kana-reading and reviewed-translation repairs to grammar examples."""

from database import connect
from grammar_quality import ensure_grammar_quality


def main() -> None:
    with connect() as db:
        result = ensure_grammar_quality(db)
    print(f"Filled {result['readings']} readings; corrected {result['translations']} Vietnamese translations.")


if __name__ == "__main__":
    main()
