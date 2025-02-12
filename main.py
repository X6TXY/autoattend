import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

USERNAME = ""
PASSWORD = ""
UPDATE_INTERVAL = 60  # time in seconds on how often to update the page
WAIT_TIME = 10  # time in seconds to wait for target element to appear, if it doesn't appear, the function will return
SHOW_UI = True  # if True, the browser instance will be open. If False, it will be headless, which requires less cpu


def try_to_attend(selenium_driver):
    wait = WebDriverWait(selenium_driver, WAIT_TIME)
    page_source = selenium_driver.page_source
    if 'Нет доступных дисциплин' in page_source:
        return

    try:
        button_divs = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[span/span[@class='v-button-caption' and text()='Отметиться']]")
            )
        )

        for button_div in button_divs:
            if button_div is not None:
                button_div.click()
                time.sleep(1)
    except TimeoutException:
        return
    except Exception as e:
        print(e)
        try_to_attend(driver)


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
    options = webdriver.ChromeOptions()

    if not SHOW_UI:
        options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    try:
        main(driver)
    except Exception as e:
        print(e)
    finally:
        driver.quit()
