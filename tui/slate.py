#!/opt/homebrew/bin/python3
"""Slate, a kanban issue tracker on mock data, in a character terminal.

python3 tui/slate.py --profile <name> --address <address> --harness
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terminal import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
