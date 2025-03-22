import time
import json
import os
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


class YandexMenuParser:
    def __init__(self):
        # Настройки браузера
        options = uc.ChromeOptions()
        options.add_argument('--lang=ru')
        options.add_argument('--no-sandbox')

        # Запуск браузера
        self.driver = uc.Chrome(options=options)
        self.results_dir = "results"

        # Папка для результатов
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # Пути к файлам
        self.combined_file = os.path.join(self.results_dir, "all_menus.json")
        self.csv_file = os.path.join(self.results_dir, "menu_items.csv")

        # Загружаем или создаём JSON
        if os.path.exists(self.combined_file):
            with open(self.combined_file, 'r', encoding='utf-8') as f:
                self.all_menus = json.load(f)
        else:
            self.all_menus = {}

        # Создаём CSV с заголовками, если нужно
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'price', 'restaurant_name'])

    def extract_menu(self, url):
        # Получаем ID ресторана из ссылки
        restaurant_id = url.split('/')[-1].split('?')[0]

        # Сопоставляем ID с названием (если не нашли на странице)
        restaurant_name_map = {
            "138220492294": "Pravda Coffee",
            "142576836285": "Surf Coffee"
        }

        # Открываем страницу
        self.driver.get(url)

        # Если появилась капча — отправляется обратно мне - тут пользовалась чатгпт
        if "captcha" in self.driver.current_url:
            input("Обнаружена капча. Реши её и нажми Enter")

        # Пытаемся открыть вкладку с меню
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

        # Получаем название ресторана
        try:
            restaurant_name = self.driver.find_element(By.CSS_SELECTOR,
                                                       ".business-card-title-view__title-link").text
        except:
            restaurant_name = restaurant_name_map.get(restaurant_id, f"Restaurant {restaurant_id}")

        # Делаем скриншот страницы (на всякий случай)
        screenshot_path = os.path.join(self.results_dir, f"{restaurant_id}_screenshot.png")
        try:
            self.driver.save_screenshot(screenshot_path)
        except:
            pass

        # Словарь для меню
        menu_categories = {}
        all_menu_items = []

        try:
            # Ищем все категории меню
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
                        # Название категории
                        category_name = category_element.find_element(By.CSS_SELECTOR,
                                                                      ".business-full-items-grouped-view__title").text

                        # Элементы в категории
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
                                    price = product_view.find_element(By.CSS_SELECTOR,
                                                                      ".related-product-view__price").text
                                except:
                                    pass

                                try:
                                    volume = product_view.find_element(By.CSS_SELECTOR,
                                                                       ".related-product-view__volume").text
                                except:
                                    pass

                                item = {
                                    "name": name,
                                    "description": description,
                                    "price": price,
                                    "volume": volume
                                }
                                menu_items.append(item)
                                all_menu_items.append(item)
                            except:
                                pass

                        if menu_items:
                            menu_categories[category_name] = menu_items
                    except:
                        pass
        except:
            pass

        if not menu_categories:
            print("Меню не найдено")

        # Сохраняем данные по ресторану
        restaurant_data = {
            "name": restaurant_name,
            "url": url,
            "menu": menu_categories
        }

        filename = os.path.join(self.results_dir, f"{restaurant_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(restaurant_data, f, ensure_ascii=False, indent=4)

        # Обновляем общий JSON
        self.all_menus[restaurant_id] = restaurant_data
        with open(self.combined_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_menus, f, ensure_ascii=False, indent=4)

        # Сохраняем в CSV
        self.export_to_csv(all_menu_items, restaurant_name)

        return restaurant_data

    def export_to_csv(self, menu_items, restaurant_name):
        # Добавляем позиции меню в CSV
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for item in menu_items:
                name_with_volume = item['name']
                if item['volume']:
                    name_with_volume = f"{item['name']} ({item['volume']})"

                writer.writerow([
                    name_with_volume,
                    item['price'],
                    restaurant_name
                ])

    def extract_menu_items_from_page(self):
        # Альтернативный способ достать позиции меню без категорий
        selectors = [
            ".related-product-view",
            ".business-full-items-grouped-view__photo-item",
            ".business-features-view__item"
        ]

        for selector in selectors:
            items = []
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                for element in elements:
                    try:
                        name = ""
                        for name_selector in [".related-item-photo-view__title",
                                              ".business-features-view__title"]:
                            try:
                                name = element.find_element(By.CSS_SELECTOR, name_selector).text
                                if name:
                                    break
                            except:
                                pass

                        if not name:
                            continue

                        description = ""
                        price = ""
                        volume = ""

                        for desc_selector in [".related-item-photo-view__description",
                                              ".business-features-view__description"]:
                            try:
                                description = element.find_element(By.CSS_SELECTOR, desc_selector).text
                                if description:
                                    break
                            except:
                                pass

                        for price_selector in [".related-product-view__price"]:
                            try:
                                price = element.find_element(By.CSS_SELECTOR, price_selector).text
                                if price:
                                    break
                            except:
                                pass

                        for vol_selector in [".related-product-view__volume"]:
                            try:
                                volume = element.find_element(By.CSS_SELECTOR, vol_selector).text
                                if volume:
                                    break
                            except:
                                pass

                        items.append({
                            "name": name,
                            "description": description,
                            "price": price,
                            "volume": volume
                        })
                    except:
                        pass

            if items:
                return items

        return []

    def close(self):
        # Закрываем браузер
        self.driver.quit()


def main():
    parser = YandexMenuParser()

    try:
        urls = [
            "https://yandex.ru/maps/org/pravda_kofe/138220492294?si=ptb4ex6crfjmmw9j7x08pnzbb8",
            "https://yandex.ru/maps/org/surf_coffee_x_roma/142576836285?si=ptb4ex6crfjmmw9j7x08pnzbb8"
        ]

        for url in urls:
            parser.extract_menu(url)
    finally:
        parser.close()


if __name__ == "__main__":
    main()
