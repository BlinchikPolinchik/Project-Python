import time
import os
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


class YandexMenuParser:
    def __init__(self):
        # Настраиваю опции для Chrome
        options = uc.ChromeOptions()
        options.add_argument('--lang=ru')
        options.add_argument('--no-sandbox')

        # Запускаю драйвер Chrome
        self.driver = uc.Chrome(options=options)
        self.results_dir = "results"

        # Создаю папку для результатов
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        self.csv_file = os.path.join(self.results_dir, "menu_items.csv")

        # CSV файл с заголовками, если он не существует
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'price', 'restaurant_name'])

    def extract_menu(self, url):
        #Парсинг меню с карт для ресторана
        restaurant_id = url.split('/')[-1].split('?')[0]

        # Мапа для названий ресторанов по их ID
        restaurant_name_map = {
            "138220492294": "Pravda Coffee",
            "142576836285": "Surf Coffee"
        }

        # Открываю страницу ресторана
        self.driver.get(url)

        # Если появляется капча, возвращает мне, я решаю - тут использовала гпт как помощь
        print(f"Текущий URL: {self.driver.current_url}")
        if "captcha" in self.driver.current_url:
            print("Капча. Реши")
            input("Нажми Enter")

        # Ищу вкладку с меню
        try:
            # Жду, чтобы страница прогрузилась
            time.sleep(2)

            # Пробую разные селекторы для вкладки меню
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
                print("Вкладка меню найдена. Кликаю по ней...")
                menu_tab.click()
                print("Жду загрузки содержимого меню...")
                time.sleep(3)  # Жду загрузки меню
            else:
                print("Вкладку меню не удалось найти, пробую найти элементы меню напрямую.")
        except Exception as e:
            print(f"Ошибка при клике по вкладке меню: {e}")

        # Получаю название ресторана
        try:
            restaurant_name = self.driver.find_element(By.CSS_SELECTOR,
                                                       ".business-card-title-view__title-link").text
        except:
            # Если не нашла, беру из мапы, либо ставлю имя по умолчанию
            restaurant_name = restaurant_name_map.get(restaurant_id, f"Ресторан {restaurant_id}")
            print(f"Не удалось получить название ресторана, использую: {restaurant_name}")

        print(f"Начинаю извлечение меню для: {restaurant_name}")

        # Извлекаю категории меню и пункты
        menu_categories = {}
        # Список всех пунктов меню для экспорта в CSV
        all_menu_items = []

        try:
            # Ищу элементы категорий меню
            category_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                          ".business-full-items-grouped-view__category")

            if not category_elements:
                print("Категории меню не найдены. Пробую найти пункты меню без категорий...")

                #Пробую извлечь пункты меню напрямую
                menu_items = self.extract_menu_items_from_page()
                if menu_items:
                    menu_categories["Меню"] = menu_items
                    all_menu_items.extend(menu_items)
            else:
                print(f"Найдено {len(category_elements)} категорий меню")
                #Обрабатываю каждую категорию
                for category_element in category_elements:
                    try:
                        # Получаю название категории
                        category_name = category_element.find_element(By.CSS_SELECTOR,
                                                                      ".business-full-items-grouped-view__title").text
                        print(f"Обрабатываю категорию: {category_name}")

                        # Извлекаю пункты меню из этой категории
                        items_container = category_element.find_element(By.CSS_SELECTOR,
                                                                        ".business-full-items-grouped-view__items")
                        item_elements = items_container.find_elements(By.CSS_SELECTOR,
                                                                      ".business-full-items-grouped-view__item")

                        #Обрабатываю пункты меню
                        menu_items = []
                        for item_element in item_elements:
                            try:
                                # Ищу элемент с информацией о продукте
                                product_view = item_element.find_element(By.CSS_SELECTOR, ".related-product-view")

                                # Получаю название блюда
                                name = product_view.find_element(By.CSS_SELECTOR,
                                                                 ".related-item-photo-view__title").text

                                # Пробую получить описание, цену и объем
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

                                # Добавляю пункт меню в список
                                item = {
                                    "name": name,
                                    "description": description,
                                    "price": price,
                                    "volume": volume
                                }
                                menu_items.append(item)
                                all_menu_items.append(item)
                            except Exception as e:
                                print(f"Ошибка при обработке пункта меню: {e}")

                        print(f"Найдено {len(menu_items)} пунктов в категории '{category_name}'")

                        # Если пункты меню есть, добавляю их в словарь категорий
                        if menu_items:
                            menu_categories[category_name] = menu_items
                    except Exception as e:
                        print(f"Ошибка при обработке категории: {e}")
        except Exception as e:
            print(f"Ошибка при извлечении меню: {e}")

        # Если пункты меню не найдены, вывожу сообщение (оно нужно было в процессе, когда что-то шло не так, сейчас тоже решила оставить для детектинга ошибок)
        if not menu_categories:
            print("Пункты меню не найдены.")

        # Собираю данные ресторана
        restaurant_data = {
            "name": restaurant_name,
            "url": url,
            "menu": menu_categories
        }

        # Экспорт пунктов меню в CSV
        self.export_to_csv(all_menu_items, restaurant_name)

        return restaurant_data

    def export_to_csv(self, menu_items, restaurant_name):
        #Экспорт пунктов меню в CSV файл
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for item in menu_items:
                # Если есть объем, добавляю его к названию
                name_with_volume = item['name']
                if item['volume']:
                    name_with_volume = f"{item['name']} ({item['volume']})"

                writer.writerow([
                    name_with_volume,
                    item['price'],
                    restaurant_name
                ])

    def extract_menu_items_from_page(self):
        #Пробую разные селекторы для поиска пунктов меню на странице
        selectors = [
            ".related-product-view",
            ".business-full-items-grouped-view__photo-item",
            ".business-features-view__item"
        ]

        for selector in selectors:
            items = []
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Найдено {len(elements)} элементов с селектором '{selector}'")
                for element in elements:
                    try:
                        # Пробую извлечь название пункта разными способами
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

                        # Пробую получить описание, цену и объем
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

                        # Добавляю пункт меню в список
                        items.append({
                            "name": name,
                            "description": description,
                            "price": price,
                            "volume": volume
                        })
                    except Exception as e:
                        print(f"Ошибка при извлечении деталей пункта меню: {e}")

            if items:
                return items

        return []

    def close(self):
        #Закрываю браузер
        self.driver.quit()


def main():
    parser = YandexMenuParser()

    try:
        # Список URL ресторанов для парсинга
        urls = [
            "https://yandex.ru/maps/org/pravda_kofe/138220492294?si=ptb4ex6crfjmmw9j7x08pnzbb8",
            "https://yandex.ru/maps/org/surf_coffee_x_roma/142576836285?si=ptb4ex6crfjmmw9j7x08pnzbb8"
        ]

        # Обрабатываю каждый url
        for url in urls:
            print(f"\nОбрабатываю: {url}")
            parser.extract_menu(url)
            print("Меню успешно извлечено\n")
    finally:
        parser.close()


if __name__ == "__main__":
    main()
