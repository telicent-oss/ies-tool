python3 -m pip install --upgrade pip
python3 -m pip install pip-tools
python3 -m piptools compile --extra dev -o requirements.txt pyproject.toml
pip3 install -r requirements.txt
pre-commit install
