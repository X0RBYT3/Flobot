import os

# Because I'm too stubborn to use dotenv.
env_file = "secrets.env"
with open(env_file) as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        if "export" not in line:
            continue
        key, value = line.replace("export ", "", 1).strip().split("=", 1)
        os.environ[key] = value  # Load to local environ

VERSION = "0.1.0"
TOKEN = os.environ["FLOBOT_API"]
PREFIX = "!"
AUTHOR = "Florence"

OWNER_ID = 24239825185524942
BOT_ID = 867582351436546070
