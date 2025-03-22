import json
import os
import requests
import csv

# Получаем данные меню из API Cofix
def get_menu_data():
    api_url = "https://cofix.global/api/v1/menu?city=moscow"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        items = extract_items_from_api(data)

        if items:
            save_to_csv(items, filename="cofix_menu.csv")

        return items

    except Exception as e:
        print("Ошибка при получении данных:", e)
        return []

# Достаём название и цену каждого товара
def extract_items_from_api(api_data):
    if not api_data or not isinstance(api_data, dict):
        return []

    all_items = []

    for category_data in api_data.values():
        if not isinstance(category_data, dict) or 'items' not in category_data:
            continue

        for item in category_data['items']:
            try:
                name = item.get('title', '')
                price = ""
                price_table = item.get('priceTable', {})

                if isinstance(price_table, dict) and 'body' in price_table:
                    if isinstance(price_table['body'], list) and len(price_table['body']) > 0:
                        price_text = price_table['body'][0]
                        price = price_text.split('₽')[0].strip()

                if name and price:
                    all_items.append({
                        "name": name,
                        "price": price
                    })
            except:
                pass  # просто пропускаем, если какая-то ошибка в товаре

    return all_items

# Сохраняем всё в CSV-файл
def save_to_csv(menu_items, filename='cofix_menu.csv'):
    if not menu_items:
        return

    fieldnames = ['name', 'price']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in menu_items:
            writer.writerow({field: item.get(field, "") for field in fieldnames})

# Запуск скрипта
if __name__ == "__main__":
    menu_items = get_menu_data()
