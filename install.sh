# 1. Ensure venv active
source venv/bin/activate

# 2. Repair pip
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# 3. Install requirements PROPERLY
python -m pip install -r requirements.txt

# 4. Verify Streamlit
python -m streamlit --version