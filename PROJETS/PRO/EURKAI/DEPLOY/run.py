
# run.py
# Minimal runtime entrypoint

import sys
from pathlib import Path
from bootstrap import Bootstrap


def main():
    if len(sys.argv) > 1:
        catalogs_root = Path(sys.argv[1]).resolve()
    else:
        catalogs_root = Path(__file__).parent / "erk_bootstrap_catalogs"

    bootstrap = Bootstrap(catalogs_root)
    fractal = bootstrap.run()

    print("BOOTSTRAP_OK")
    print("Catalogs loaded:", list(fractal.catalogs.keys()))
    print("Indexed elements:", len(fractal.index))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
