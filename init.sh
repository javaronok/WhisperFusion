rm -rf .venv/
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -v .
