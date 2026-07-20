#!/bin/bash

set -eu -o pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

# Prefer an installed expandvars; otherwise use a local develop fork with ExpandParser.
ensure_expandvars() {
  if python -c "from expandvars import ExpandParser" 2>/dev/null; then
    return 0
  fi

  local candidate
  for candidate in \
    "${EXPANDVARS_PATH:-}" \
    "${ROOT}/../../python-expandvars_fork" \
    "${ROOT}/../../../bench_paasify/work__v4/python-expandvars"
  do
    if [[ -n "$candidate" && -f "${candidate}/expandvars.py" ]]; then
      if PYTHONPATH="${candidate}:${PYTHONPATH:-}" \
        python -c "from expandvars import ExpandParser" 2>/dev/null; then
        export PYTHONPATH="${candidate}:${PYTHONPATH:-}"
        echo "Using expandvars from: ${candidate}"
        return 0
      fi
    fi
  done

  echo "ERROR: expandvars with ExpandParser not found." >&2
  echo "Install: pip install git+https://github.com/mrjk/python-expandvars.git@develop" >&2
  echo "Or set EXPANDVARS_PATH to a local checkout of the develop branch." >&2
  return 1
}

main_tests () {
  ensure_expandvars
  if python -m pytest tests/ "$@"; then
    echo "OK"
  else
    echo "FAILED"
    return 2
  fi
}

main_tests "$@"
