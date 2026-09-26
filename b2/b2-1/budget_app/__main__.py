"""`python -m budget_app` 진입점.

조립 지점이므로 cli.app 외에는 의존하지 않는다.
"""

import sys

from budget_app.cli.app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
