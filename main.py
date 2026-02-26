import os
import shutil
import time
import uuid
import logging
from datetime import datetime

import psutil
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

USERNAME = os.getenv("USERNAME", "b_toleu")
PASSWORD = os.getenv("PASSWORD", "Baha7201")
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "30"))  # time in seconds on how often to update the page
WAIT_TIME = 10  # time in seconds to wait for target element to appear, if it doesn't appear, the function will return
SHOW_UI = False


def kill_chrome_processes():
    for proc in psutil.process_iter():
        if proc.name() == 'chrome.exe':
            proc.kill()


def try_to_attend(selenium_driver, consecutive_timeouts=[0]):
    wait = WebDriverWait(selenium_driver, WAIT_TIME)
    page_source = selenium_driver.page_source
    if 'Нет доступных дисциплин' in page_source:
        logger.info("Нет доступных дисциплин")
        consecutive_timeouts[0] = 0  # Сброс счетчика при успехе
        return

    try:
        button_divs = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[span/span[@class='v-button-caption' and text()='Отметиться']]")
            )
        )

        buttons_clicked = 0
        for button_div in button_divs:
            if button_div is not None:
                try:
                    button_div.click()
                    buttons_clicked += 1
                    logger.info(f"✅ Кнопка 'Отметиться' нажата (всего: {buttons_clicked})")
                    time.sleep(1)
                except Exception as click_error:
                    logger.warning(f"Ошибка при нажатии кнопки: {click_error}")
        
        if buttons_clicked > 0:
            logger.info(f"📊 Успешно отмечено: {buttons_clicked} кноп(ки/ок)")
            # Отправляем уведомление в Telegram об успешной отметке
            try:
                from telegram_bot import telegram_bot
                import asyncio
                # Создаем новый event loop для уведомления
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(telegram_bot.send_attendance_success(buttons_clicked))
                loop.close()
            except Exception as telegram_error:
                logger.warning(f"Не удалось отправить уведомление в Telegram: {telegram_error}")
        
        consecutive_timeouts[0] = 0  # Сброс счетчика при успехе
    except TimeoutException:
        consecutive_timeouts[0] += 1
        logger.warning(f"⏰ Таймаут ожидания кнопок отметки (последовательный: {consecutive_timeouts[0]})")
        
        # Если слишком много таймаутов подряд, сбрасываем счетчик и продолжаем
        if consecutive_timeouts[0] >= 3:
            logger.warning("🔄 Слишком много таймаутов подряд. Сброс счетчика и продолжение работы.")
            consecutive_timeouts[0] = 0
        return
    except Exception as e:
        logger.error(f"❌ Ошибка при попытке отметиться: {e}")
        consecutive_timeouts[0] = 0
        try_to_attend(driver, consecutive_timeouts)


def main(selenium_driver):
    selenium_driver.get("https://wsp.kbtu.kz/RegistrationOnline")

    while True:
        time.sleep(1)
        page_source = selenium_driver.page_source
        if 'Вход в систему' in page_source:
            login(selenium_driver)

        try_to_attend(selenium_driver)
        time.sleep(UPDATE_INTERVAL)
        selenium_driver.refresh()


def attend_bot(username, password):
    kill_chrome_processes()
    options = webdriver.ChromeOptions()
    session_id = f"chrome_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    session_dir = os.path.join(os.getcwd(), "chrome_sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)
    logger.info(f"Создана директория сессии: {session_dir}")
    options.add_argument(f'--user-data-dir={session_dir}')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    if not SHOW_UI:
        logger.info("Запуск в headless режиме")
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')

    driver = None
    try:
        logger.info("Создание Chrome service...")
        service = Service(ChromeDriverManager().install())
        logger.info("Инициализация Chrome driver...")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://wsp.kbtu.kz/RegistrationOnline")
        logger.info("Бот запущен")

        consecutive_timeouts = [0]  # Используем список для мутабельности
        
        while True:
            time.sleep(1)
            page_source = driver.page_source
            if 'Вход в систему' in page_source:
                logger.info("Требуется вход в систему")
                login_with_credentials(driver, username, password)

            try_to_attend(driver, consecutive_timeouts)
            time.sleep(UPDATE_INTERVAL)
            driver.refresh()
            logger.info("Страница обновлена")

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise  # Перебрасываем исключение для обработки в backend
    finally:
        logger.info("Завершение работы Chrome driver...")
        if driver is not None:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Ошибка при закрытии driver: {e}")
        kill_chrome_processes()
        try:
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                logger.info(f"Удалена директория сессии: {session_dir}")
        except Exception as e:
            logger.error(f"Не удалось удалить директорию сессии: {e}")


def login_with_credentials(selenium_driver, username, password):
    wait = WebDriverWait(selenium_driver, WAIT_TIME)

    username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))
    if username_input is not None:
        username_input.clear()
        username_input.send_keys(username)

    time.sleep(1)

    password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
    if password_input is not None:
        password_input.send_keys(password)

    checkbox = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@type="checkbox"]')
        )
    )
    parent_element = selenium_driver.execute_script("return arguments[0].parentElement;", checkbox)
    if parent_element is not None:
        parent_element.click()

    submit_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@role="button" and contains(@class, "v-button-primary")]')
        )
    )
    if submit_button is not None:
        submit_button.click()


def login(selenium_driver):
    wait = WebDriverWait(selenium_driver, WAIT_TIME)

    username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))
    if username_input is not None:
        username_input.clear()
        username_input.send_keys(USERNAME)

    time.sleep(1)

    password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
    if password_input is not None:
        password_input.send_keys(PASSWORD)

    checkbox = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@type="checkbox"]')
        )
    )
    parent_element = selenium_driver.execute_script("return arguments[0].parentElement;", checkbox)
    if parent_element is not None:
        parent_element.click()

    submit_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@role="button" and contains(@class, "v-button-primary")]')
        )
    )
    if submit_button is not None:
        submit_button.click()


if __name__ == "__main__":
    logger.info("Инициализация Chrome driver...")
    kill_chrome_processes()
    options = webdriver.ChromeOptions()
    session_id = f"chrome_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    session_dir = os.path.join(os.getcwd(), "chrome_sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)
    logger.info(f"Создана директория сессии: {session_dir}")
    options.add_argument(f'--user-data-dir={session_dir}')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    if not SHOW_UI:
        logger.info("Запуск в headless режиме")
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    try:
        logger.info("Создание Chrome service...")
        service = Service(ChromeDriverManager().install())
        logger.info("Инициализация Chrome driver...")
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Запуск бота...")
        main(driver)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Завершение работы Chrome driver...")
        if 'driver' in locals():
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Ошибка при закрытии driver: {e}")
        kill_chrome_processes()
        try:
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                logger.info(f"Удалена директория сессии: {session_dir}")
        except Exception as e:
            logger.error(f"Не удалось удалить директорию сессии: {e}")
