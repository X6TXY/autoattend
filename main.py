import os
import time

import sentry_sdk

from handlers.attend_handler import attend_loop


def init_sentry():
    dsn = os.getenv(
        "SENTRY_DSN",
        "https://0219066adb71910fbdb45a7730251d96@o4511030016278528.ingest.de.sentry.io/4511030017523792",
    ).strip()
    if dsn.lower() in {"", "off", "false", "0"}:
        print("Sentry отключен")
        return

    sentry_sdk.init(
        dsn=dsn,
        send_default_pii=True,
    )
    print("Sentry инициализирован")


if __name__ == "__main__":
    init_sentry()

    portal = os.getenv("PORTAL", "wsp").strip().lower()
    if portal not in {"wsp", "pge"}:
        portal = "wsp"

    restart_delay = max(1, int(os.getenv("RESTART_DELAY_SEC", "5")))
    restart_max_delay = max(restart_delay, int(os.getenv("RESTART_MAX_DELAY_SEC", "60")))
    current_delay = restart_delay

    while True:
        try:
            attend_loop(portal)
            print("attend_loop завершился, перезапуск...")
        except KeyboardInterrupt:
            print("Остановка по Ctrl+C")
            break
        except Exception as e:
            print("Критическая ошибка:", e)
            sentry_sdk.capture_exception(e)

        print(f"Перезапуск через {current_delay} сек...")
        time.sleep(current_delay)
        current_delay = min(current_delay * 2, restart_max_delay)
