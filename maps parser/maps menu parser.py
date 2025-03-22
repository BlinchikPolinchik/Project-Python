import time
import json
import os
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


class YandexMenuParser:
    def __init__(self):
        # Настройки для запуска браузера
        options = uc.ChromeOptions()
        options.add_argument('--lang=ru')
        options.add_argument('--no-sandbox')
        self.driver = uc.Chrome(options=options)

        # Папка для сохранения результатов
        self.results_dir = "results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # Пути к JSON и CSV файлам
        self.combined_file = os.path.join(self.results_dir, "all_menus.json")
        self.csv_file = os.path.join(self.results_dir, "menu_items.csv")

        # Загружаем старые данные или создаём новые
        if os.path.exists(self.combined_file):
            with open(self.combined_file, 'r', encoding='utf-8') as f:
                self.all_menus = json.load(f)
        else:
            self.all_menus = {}

        # CSV с заголовками (если ещё нет)
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'price', 'restaurant_name'])

    def extract_menu(self, url):
        # Получаем ID ресторана из ссылки
        restaurant_id = url.split('/')[-1].split('?')[0]

        # Названия по ID, если не найдём на странице
        restaurant_name_map = {
            "138220492294": "Pravda Coffee",
            "142576836285": "Surf Coffee"
        }

        self.driver.get(url)

        # Если капча — ждём, пока пользователь решит
        if "captcha" in self.driver.current_url:
            input("Обнаружена капча. Реши её")

        # Пробуем найти вкладку с меню и кликнуть
        time.sleep(2)
        menu_tab_selectors = [
            ".tabs-select-view__title._name_menu",
            "div[aria-label='Меню, ']",
            ".tabs-select-view__title[aria-label='Меню, ']",
            "a.tabs-select-view__label[href*='/menu/']"
        ]

        menu_tab = None
        for selector in menu_tab_selectors:
            try:
                menu_tab = self.driver.find_element(By.CSS_SELECTOR, selector)
                if menu_tab:
                    break
            except:
                continue

        if menu_tab:
            menu_tab.click()
            time.sleep(3)

        # Пытаемся получить название ресторана
        try:
            restaurant_name = self.driver.find_element(By.CSS_SELECTOR, ".business-card-title-view__title-link").text
        except:
            restaurant_name = restaurant_name_map.get(restaurant_id, f"Restaurant {restaurant_id}")

        # Делаем скриншот страницы
        screenshot_path = os.path.join(self.results_dir, f"{restaurant_id}_screenshot.png")
        try:
            self.driver.save_screenshot(screenshot_path)
        except:
            pass

        menu_categories = {}
        all_menu_items = []

        try:
            category_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                          ".business-full-items-grouped-view__category")

            if not category_elements:
                menu_items = self.extract_menu_items_from_page()
                if menu_items:
                    menu_categories["Menu"] = menu_items
                    all_menu_items.extend(menu_items)
            else:
                for category_element in category_elements:
                    try:
                        category_name = category_element.find_element(By.CSS_SELECTOR,
                                                                      ".business-full-items-grouped-view__title").text
                        items_container = category_element.find_element(By.CSS_SELECTOR,
                                                                        ".business-full-items-grouped-view__items")
                        item_elements = items_container.find_elements(By.CSS_SELECTOR,
                                                                      ".business-full-items-grouped-view__item")

                        menu_items = []
                        for item_element in item_elements:
                            try:
                                product_view = item_element.find_element(By.CSS_SELECTOR, ".related-product-view")
                                name = product_view.find_element(By.CSS_SELECTOR,
                                                                 ".related-item-photo-view__title").text

                                description = ""
                                price = ""
                                volume = ""

                                try:
                                    description = product_view.find_element(By.CSS_SELECTOR,
                                                                            ".related-item-photo-view__description").text
                                except:
                                    pass
                                try:
                                    price = product_view_
