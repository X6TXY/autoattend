import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
UPDATE_INTERVAL = 60  # time in seconds on how often to update the page
WAIT_TIME = 10  # time in seconds to wait for target element to appear, if it doesn't appear, the function will return
SHOW_UI = True  # if True, the browser instance will be open. If False, it will be headless, which requires less cpu


def create_unique_user_data_dir():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_data_dir = f'/tmp/chrome-data_{timestamp}'
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    return user_data_dir


def try_to_attend(selenium_driver):
    print("Checking for attendance buttons...")
    wait = WebDriverWait(selenium_driver, WAIT_TIME)
    page_source = selenium_driver.page_source
    if 'Нет доступных дисциплин' in page_source:
        print("No available disciplines found")
        return

    try:
        print("Looking for attendance buttons...")
        button_divs = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[span/span[@class='v-button-caption' and text()='Отметиться']]")
            )
        )

        print(f"Found {len(button_divs)} attendance buttons")
        for i, button_div in enumerate(button_divs, 1):
            if button_div is not None:
                print(f"Clicking attendance button {i}/{len(button_divs)}")
                button_div.click()
                time.sleep(1)
    except TimeoutException:
        print("No attendance buttons found")
        return
    except Exception as e:
        print(f"Error while trying to attend: {e}")
        try_to_attend(driver)


def main(selenium_driver):
    print("Starting main loop...")
    selenium_driver.get("https://wsp.kbtu.kz/RegistrationOnline")

    while True:
        time.sleep(1)
        page_source = selenium_driver.page_source
        if 'Вход в систему' in page_source:
            print("Login required, attempting to log in...")
            login(selenium_driver)

        try_to_attend(selenium_driver)
        print(f"Waiting {UPDATE_INTERVAL} seconds before next check...")
        time.sleep(UPDATE_INTERVAL)
        print("Refreshing page...")
        selenium_driver.refresh()


def login(selenium_driver):
    print("Starting login process...")
    wait = WebDriverWait(selenium_driver, WAIT_TIME)

    print("Looking for username input...")
    username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))
    if username_input is not None:
        print("Entering username...")
        username_input.clear()
        username_input.send_keys(USERNAME)

    time.sleep(1)

    print("Looking for password input...")
    password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
    if password_input is not None:
        print("Entering password...")
        password_input.send_keys(PASSWORD)

    print("Looking for checkbox...")
    checkbox = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@type="checkbox"]')
        )
    )
    parent_element = selenium_driver.execute_script("return arguments[0].parentElement;", checkbox)
    if parent_element is not None:
        print("Clicking checkbox...")
        parent_element.click()

    print("Looking for submit button...")
    submit_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@role="button" and contains(@class, "v-button-primary")]')
        )
    )
    if submit_button is not None:
        print("Clicking submit button...")
        submit_button.click()
    print("Login process completed")


if __name__ == "__main__":
    print("Initializing Chrome driver...")
    options = webdriver.ChromeOptions()

    if not SHOW_UI:
        print("Running in headless mode")
        options.add_argument('--headless=new')
    temp_dir = create_unique_user_data_dir()
    print(f"Using temporary directory: {temp_dir}")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument(f'--user-data-dir={temp_dir}')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    try:
        print("Creating Chrome service...")
        service = Service()
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(service=service, options=options)
        print("Starting bot...")
        main(driver)
    except Exception as e:
        print(f"Fatal error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Shutting down Chrome driver...")
        if 'driver' in locals():
            driver.quit()
        # Clean up temporary directory
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")
