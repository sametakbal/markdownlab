# PyInstaller entry point (so relative imports inside the package work)
import sys

from markdownlab.__main__ import main

sys.exit(main())
