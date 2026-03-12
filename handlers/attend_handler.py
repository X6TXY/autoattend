import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import LOGIN, PASSWORD, get_portal_urls
from services.selenium import get_driver
from models.card import Card

def parse_card(card_element):
    try:
        label_bold = card_element.find_element(By.XPATH, ".//div[contains(@class, 'v-label-bold')]")
        inner_html = label_bold.get_attribute("innerHTML")
        lines = [l.strip() for l in inner_html.split('<br>') if l.strip()]
        subject = lines[0] if len(lines) > 0 else "-"
        teacher = lines[1] if len(lines) > 1 else "-"
        lesson_time = lines[2] if len(lines) > 2 else "-"
    except Exception:
        subject = teacher = lesson_time = "-"
    return Card(subject, teacher, lesson_time)

def attend_loop(portal: str):
    driver = get_driver()
    LOGIN_URL, ATTEND_URL = get_portal_urls(portal)
    try:
        driver.get(LOGIN_URL)
        time.sleep(2)
        
        # Устанавливаем cookie для русского языка
        driver.add_cookie({
            'name': 'r5-locale',
            'value': 'ru',
            'domain': 'pge.kbtu.kz' if portal != "wsp" else 'wsp.kbtu.kz',
            'path': '/'
        })
        print("Cookie r5-locale=ru установлен")
        
        driver.refresh()
        wait = WebDriverWait(driver, 120)
        login_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Вход']/ancestor::div[contains(@class, 'v-button')]")
        ))
        login_btn.click()
        print("Кнопка 'Вход' нажата.")
        time.sleep(3)
        driver.get(ATTEND_URL)
        print(f"Перешли на страницу: {ATTEND_URL}")

        while True:
            WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'v-verticallayout-card')]")
                          or d.find_elements(By.XPATH, "//div[contains(@class, 'v-label') and contains(text(), 'Нет доступных дисциплин')]")
            )
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-verticallayout-card') and .//div[contains(@class,'v-label-bold')]]")

            if cards:
                for card in cards:
                    try:
                        btn = card.find_element(
                            By.XPATH,
                            ".//span[contains(@class, 'v-button-caption') and text()='Отметиться']/ancestor::div[contains(@class, 'v-button') and not(contains(@class, 'v-disabled'))]"
                        )
                        btn.click()
                        status = "Успешно нажата"
                    except Exception:
                        try:
                            btn = card.find_element(
                                By.XPATH,
                                ".//span[contains(@class, 'v-button-caption') and text()='Отмечен']/ancestor::div[contains(@class, 'v-button') and contains(@class, 'v-disabled')]"
                            )
                            status = "Успешно нажата (уже отмечено)"
                        except Exception:
                            status = "Нет кнопки 'Отметиться' или 'Отмечен'"

                    c = parse_card(card)
                    print("-" * 40)
                    print(f"Предмет: {c.subject}")
                    print(f"Преподаватель: {c.teacher}")
                    print(f"Время: {c.lesson_time}")
                    print(f"Статус: {status}")

            else:
                try:
                    msg = driver.find_element(By.XPATH, "//div[contains(@class, 'v-label') and contains(text(), 'Нет доступных дисциплин')]")
                    print("-" * 40)
                    print("Нет доступных дисциплин для отметки")
                except Exception as e:
                    print("-" * 40)
                    print("Не удалось найти ни одной карточки или сообщения о дисциплинах.")
                    print("Возможная причина: забыл указать логин/пароль в конфигах.")
                    raise RuntimeError("Страница не содержит карточки и сообщение о доступных дисциплинах") from e

            time.sleep(10)
            driver.get(ATTEND_URL)
    finally:
        driver.quit()
