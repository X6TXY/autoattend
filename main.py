import os

from handlers.attend_handler import attend_loop

if __name__ == "__main__":
    portal = os.getenv("PORTAL", "wsp").strip().lower()
    if portal not in {"wsp", "pge"}:
        portal = "wsp"
    attend_loop(portal)
