# APAC CSFLE Demo

## Setup

Roughly:

```
# In bash, from the checked out directory
python -m venv .
source ./bin/activate
pip install -r requirements.txt

# Set credentials
cp example.env .env
vim .env

# Update server URI and path to crypt_shared
vim your_credentials.py
```

## Usage

Having setup as above, run the `[0-9]_*.py` scripts in order to see what happens:
```
python 0_make_data_key.py
```
