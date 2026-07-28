from __future__ import annotations

import os
import sys

import pytest


def main() -> None:
    """Run pytest and exit before third-party Qt shutdown destructors run.

    On Windows, PySide/Qt can report 0xC0000374 during CPython interpreter
    teardown after pytest has already completed successfully.  This harness
    does not hide crashes during a test: a native failure before pytest returns
    still terminates the process with that failure.  It only preserves the
    actual pytest result after pytest.main() has returned.
    """

    code = int(pytest.main(sys.argv[1:]))
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    finally:
        os._exit(code)


if __name__ == "__main__":
    main()
