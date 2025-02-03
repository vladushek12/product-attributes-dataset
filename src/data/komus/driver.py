import undetected_chromedriver as uc
from undetected_chromedriver import Chrome

from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from time import sleep


# TODO context manager


def get_driver() -> Chrome:
    options = uc.ChromeOptions()

    # minimize logs
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('log-level=3')

    # options.add_argument('--headless')

    # disable
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')

    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2  # Отключение загрузки изображений
    })

    return uc.Chrome(options=options)


def load_page(driver: Chrome, link_page: str, wait_element_class: str = None):
    # print(link)
    driver.get(link_page)

    # условие для прогрузки страницы
    if wait_element_class:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, wait_element_class))
        ) 
