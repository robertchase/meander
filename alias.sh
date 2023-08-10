_PYTHON="PYTHONPATH=$(make pythonpath) $(make venvdir)/bin/python"

alias akk="${_PYTHON} akk.py"
alias black="$(make venvdir)/bin/black"
alias pylint="$(make venvdir)/bin/pylint"
alias pytest="$(make venvdir)/bin/pytest"

unset _PYTHON

alias un-alias="unalias akk black pylint pytest"
