import time
import csv
import re
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

class SimpleHHParser:
    def __init__(self, url="https://hh.ru/vacancies/barista", max_pages=8):
        self.url = url
        self.max_pages = max_pages
        self.data = []
        self.driver = None

    def run(self):
        #Основная функция для запуска парсера
        try:
            # Настраиваем браузер
            options = uc.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            print("Браузер успешно запущен")

            # Открываем сайт
            self.driver.get(self.url)
            print(f"Открыли: {self.url}")

            # Ждём, если появится капча
            print("\n" + "="*50)
            print("Пройди капчу")
            print("="*50)
            input()

            # Обрабатываем страницы
            current_page = 1
            while current_page <= self.max_pages:

                # Получаем все вакансии на текущей странице
                vacancies = self._parse_vacancies()
                if not vacancies:
                    break

                print(f"Найдено {len(vacancies)} вакансий на странице {current_page}") #оставила для отслеживания работы кода
                self.data.extend(vacancies)

                # переходим на следующую страницу
                current_page += 1
                if current_page <= self.max_pages:
                    next_url = f"{self.url}?page={current_page-1}"
                    self.driver.get(next_url)
                    time.sleep(2)

            # Сохраняем данные в CSV, если они есть
            if self.data:
                self._save_to_csv("vacancies.csv")
                print(f"Сохранено {len(self.data)} вакансий")
            else:
                print("Данных нет")

            return self.data

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def _save_to_csv(self, filename):
        #Сохраняем данные в CSV
        if not self.data:
            return

        keys = self.data[0].keys()

        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.data)

    def _salary_in_range(self, salary_str):
        #Тут чищу зарплаты, потому что они указаны по-разному. Беру 12-часовой рабочий день и зарплату только за месяц
        # Если зарплата не указана, оставляем вакансию
        if salary_str == "Не указана":
            return True

        #Заменяем неразрывные пробелы на обычные пробелы
        salary_cleaned = salary_str.replace("\xa0", " ")
        # Ищем все числа в строке зарплаты (например, "от 70 000 до 100 000 руб.")
        numbers = re.findall(r'\d[\d\s]*\d', salary_cleaned)

        try:
            numbers = [int(num.replace(" ", "")) for num in numbers if num.strip() != ""]
        except Exception as e:
            print(f"Ошибка конвертации зарплаты '{salary_str}': {e}")
            return True

        if not numbers:
            return True  # Если не нашли чисел, оставляем вакансию

        lower_limit = 50000
        upper_limit = 150000
        salary_str_lower = salary_cleaned.lower()

        # Если зарплата указана как диапазон "от ... до ..."
        if "от" in salary_str_lower and "до" in salary_str_lower:
            if len(numbers) >= 2:
                min_sal = numbers[0]
                max_sal = numbers[1]
                return (min_sal >= lower_limit and max_sal <= upper_limit)
            else:
                return False
        # Если указана зарплата "от ..."
        elif "от" in salary_str_lower:
            min_sal = numbers[0]
            return (min_sal >= lower_limit and min_sal <= upper_limit)
        # Если указана зарплата "до ..."
        elif "до" in salary_str_lower:
            max_sal = numbers[0]
            return (max_sal >= lower_limit and max_sal <= upper_limit)
        else:
            # Если зарплата указана одним числом, проверяем его
            sal = numbers[0]
            return (sal >= lower_limit and sal <= upper_limit)

    def _parse_vacancies(self):

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Находим ссылки на вакансии
        vacancy_links = soup.select("a[data-qa='serp-item__title'], a[href*='/vacancy/']")

        if not vacancy_links:
            return []

        vacancies = []

        for link in vacancy_links:
            # Для каждой вакансии переходим на страницу с подробностями
            title = link.text.strip()
            href = link.get("href", "")

            # Пропускаем, если ссылка кривая или заголовок пустой
            if not href or title in ["", "На карте"]:
                continue

            vacancy = {"title": title, "link": href}

            try:
                # Заходим на страницу вакансии
                print(f"Заходим на вакансию: {title}") #аналогично оставила для отслеживания
                self.driver.get(href)
                time.sleep(2)

                # Парсим подробности вакансии
                page_html = self.driver.page_source
                detail_soup = BeautifulSoup(page_html, 'html.parser')

                # Получаем зарплату
                # Тут я использовала чатгпт в процессе дебагинга
                salary_element = detail_soup.select_one("[data-qa='vacancy-salary'], [data-qa*='salary']")
                if salary_element:
                    vacancy["salary"] = salary_element.text.strip()
                else:
                    vacancy["salary"] = "Не указана"

                # Фильтруем вакансии по зарплате
                if not self._salary_in_range(vacancy["salary"]):
                    print(f"Пропускаем {title} из-за неподходящей зарплаты: {vacancy['salary']}")
                    continue

                # Вынимаем название компании
                company_element = detail_soup.select_one("[data-qa*='employer-name']")
                if company_element:
                    vacancy["company"] = company_element.text.strip()
                else:
                    vacancy["company"] = "Не указана"

                # Вынимаем описание вакансии
                description_element = detail_soup.select_one("[data-qa='vacancy-description']")
                if description_element:
                    vacancy["description"] = description_element.text.strip()
                else:
                    vacancy["description"] = ""

                vacancies.append(vacancy)

            except Exception as e:
                print(f"Ошибка при обработке вакансии {title}: {e}")

        return vacancies

if __name__ == "__main__":
    parser = SimpleHHParser()
    parser.run()
