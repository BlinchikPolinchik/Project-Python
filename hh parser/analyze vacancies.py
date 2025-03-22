import pandas as pd
import matplotlib.pyplot as plt
import re
import os

# Разбираем зарплату: достаём мин, макс и среднюю (только рубли)
def parse_salary(salary_text):
    if not salary_text or salary_text == "Не указана":
        return None, None, None

    # Ищем числа в тексте (убираем пробелы и неразрывные пробелы) - тут пользовалась помощью чатгпт
    numbers = re.findall(r'\d+[\s\xa0]*\d*', salary_text)
    numbers = [int(num.replace('\xa0', '').replace(' ', '')) for num in numbers]

    if len(numbers) >= 2:
        min_salary = numbers[0]
        max_salary = numbers[1]
        avg_salary = (min_salary + max_salary) / 2
    elif len(numbers) == 1:
        min_salary = max_salary = avg_salary = numbers[0]
    else:
        return None, None, None

    return min_salary, max_salary, avg_salary

# Ищем обязанности по ключевым словам
def detect_functions(description):
    if not isinstance(description, str):
        return {}

    description = description.lower()

    main_functions = {
        "coffee_making": ["приготовление кофе", "заваривать кофе", "работа с кофемашиной", "варить кофе", "эспрессо", "кофе", "бариста"],
        "customer_service": ["общение с гостями", "обслуживание гостей", "обслуживание клиентов", "работа с гостями", "обслуживание", "клиент", "гость", "покупатель"],
        "cash_register": ["работа с кассой", "кассовые операции", "расчет гостей", "прием оплаты", "касса", "деньги"],
        "food_prep": ["приготовление еды", "приготовление блюд", "готовить сэндвичи", "приготовление десертов", "готовить", "блюдо", "сэндвич", "десерт"],
        "cleaning": ["уборка", "чистота", "чистк", "помыть", "мыть посуду", "поддержание чистоты", "мыть", "посуда", "уборка зала"],
        "inventory": ["работа с товаром", "приемка товара", "заказ товара", "инвентаризация", "товар", "склад", "приемка", "инвентарь"],
        "opening_closing": ["открытие кофейни", "закрытие кофейни", "открытие смены", "закрытие смены", "смена", "открытие", "закрытие"]
    }

    result = {}
    for function, keywords in main_functions.items():
        result[function] = any(keyword in description for keyword in keywords)

    return result

# Ищем бонусы по описанию
def detect_benefits(description):
    if not isinstance(description, str):
        return {}

    description = description.lower()

    benefits_keywords = {
        "free_food": ["бесплатное питание", "питание на смене", "еда на смене", "питание за счет компании", "питание", "обед"],
        "expired_products": ["списанная продукция", "забирать остатки", "можно забирать", "продукция с витрины", "списание", "остатки"],
        "flexible_schedule": ["гибкий график", "удобный график", "составляем график", "подбираем график", "гибкий", "удобный график"],
        "training": ["обучение", "стажировка", "профессиональное развитие", "обучаем с нуля", "научим", "стажируем"],
        "career_growth": ["карьерный рост", "возможность роста", "развитие в компании", "перспектива роста", "карьер", "рост", "повышение"],
        "discounts": ["скидки", "скидки на продукцию", "корпоративные скидки", "скидка на еду", "скидка"],
        "bonuses": ["премии", "бонусы", "мотивация", "вознаграждение", "премиальная часть", "премия", "бонус"],
        "transport_compensation": ["компенсация проезда", "оплата проезда", "оплата такси", "оплата транспорта", "проезд", "такси"],
        "uniform": ["форма", "униформа", "рабочая одежда", "предоставляем форму", "одежда"]
    }

    result = {}
    for benefit, keywords in benefits_keywords.items():
        result[benefit] = any(keyword in description for keyword in keywords)

    return result

# Строим гистограмму зарплат
def generate_salary_histogram(df, output_file="salary_histogram.png"):
    salaries = []
    for _, row in df.iterrows():
        if 'salary' in row:
            _, _, avg = parse_salary(row['salary'])
            if avg:
                salaries.append(avg)

    if not salaries:
        print("Нет данных для построения графика зарплат")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(salaries, bins=10, color='skyblue', edgecolor='black')
    plt.title('Распределение зарплат вакансий бариста', fontsize=14)
    plt.xlabel('Зарплата (руб.)', fontsize=12)
    plt.ylabel('Количество вакансий', fontsize=12)
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"График зарплат сохранён как {output_file}")

# Диаграмма по обязанностям
def generate_functions_chart(df, output_file="main_functions.png"):
    function_names = {
        "coffee_making": "Приготовление кофе",
        "customer_service": "Обслуживание клиентов",
        "cash_register": "Работа с кассой",
        "food_prep": "Приготовление еды",
        "cleaning": "Уборка",
        "inventory": "Инвентаризация",
        "opening_closing": "Открытие/закрытие"
    }

    functions_count = {fn: 0 for fn in function_names}
    total = 0

    for _, row in df.iterrows():
        if 'description' in row and row['description']:
            total += 1
            functions = detect_functions(row['description'])
            for fn in functions:
                if functions[fn]:
                    functions_count[fn] += 1

    if total == 0:
        print("Нет данных об обязанностях")
        return

    percentages = {fn: (count / total) * 100 for fn, count in functions_count.items()}

    plt.figure(figsize=(12, 6))
    plt.bar(
        [function_names[f] for f in functions_count.keys()],
        [percentages[f] for f in functions_count.keys()],
        color='lightblue'
    )
    plt.title('Основные обязанности бариста', fontsize=14)
    plt.xlabel('Обязанность', fontsize=12)
    plt.ylabel('% вакансий', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"График обязанностей сохранён как {output_file}")

# Диаграмма по бонусам
def generate_benefits_chart(df, output_file="benefits.png"):
    benefit_names = {
        "free_food": "Бесплатное питание",
        "expired_products": "Списанная продукция",
        "flexible_schedule": "Гибкий график",
        "training": "Обучение",
        "career_growth": "Карьерный рост",
        "discounts": "Скидки",
        "bonuses": "Премии",
        "transport_compensation": "Компенсация проезда",
        "uniform": "Униформа"
    }

    benefits_count = {bn: 0 for bn in benefit_names}
    total = 0

    for _, row in df.iterrows():
        if 'description' in row and row['description']:
            total += 1
            benefits = detect_benefits(row['description'])
            for bn in benefits:
                if benefits[bn]:
                    benefits_count[bn] += 1

    if total == 0:
        print("Нет данных по бонусам")
        return

    percentages = {bn: (count / total) * 100 for bn, count in benefits_count.items()}

    plt.figure(figsize=(12, 6))
    plt.bar(
        [benefit_names[b] for b in benefits_count.keys()],
        [percentages[b] for b in benefits_count.keys()],
        color='lightgreen'
    )
    plt.title('Неденежные бонусы в вакансиях бариста', fontsize=14)
    plt.xlabel('Тип бонуса', fontsize=12)
    plt.ylabel('% вакансий', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"График бонусов сохранён как {output_file}")

# Запускаем анализ
def analyze_data():
    csv_file = "vacancies.csv"
    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден. Сначала запусти парсер.")
        return

    try:
        df = pd.read_csv(csv_file)
        print(f"Загружено {len(df)} вакансий из {csv_file}")
    except Exception as e:
        print(f"Ошибка при загрузке CSV: {e}")
        return

    generate_salary_histogram(df)
    generate_functions_chart(df)
    generate_benefits_chart(df)

if __name__ == "__main__":
    analyze_data()
