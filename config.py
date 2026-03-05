import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

LOGIN = os.getenv("KBTU_LOGIN", "")
PASSWORD = os.getenv("KBTU_PASSWORD", "")

def get_portal_urls(portal: str):
    if portal == "wsp":
        base = "wsp.kbtu.kz"
    else:
        base = "pge.kbtu.kz"
    login_url = f"https://{base}/?login={urllib.parse.quote(LOGIN)}&password={urllib.parse.quote(PASSWORD)}"
    attend_url = f"https://{base}/RegistrationOnline"
    return login_url, attend_url