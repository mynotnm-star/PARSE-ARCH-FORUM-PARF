from bs4 import BeautifulSoup
import time
import requests
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor  # <-- Наш ускоритель

ua = UserAgent()
UAR = {'User-Agent': ua.random}

# 1. Выносим парсинг ОДНОЙ страницы в функцию
def parse_page(forum_id, pagination):
    url2 = f'https://bbs.archlinux.org/viewforum.php?id={forum_id}&p={pagination}'
    
    # У каждого потока должна быть своя сессия или просто прямой запрос, чтобы не делить один сокет
    try:
        response2 = requests.get(url2, headers=UAR, timeout=10)
        if response2.status_code != 200:
            return
            
        soup2 = BeautifulSoup(response2.text, 'lxml')
        main2 = soup2.select_one('div.punwrap')
        
        if not main2:
            return
            
        name2 = main2.select('div.tclcon div a')
        author = main2.select('div.tclcon div span.byuser')
        replies = main2.select('td.tc2')
        views = main2.select('td.tc3')
        
        # Чтобы потоки не дрались за файл, собираем строки в массив и пишем за один раз
        lines_to_write = []
        for i2 in range(len(name2)):
            text_name2 = name2[i2].text.strip()
            try:
                text_author = author[i2].text.strip()
            except IndexError:
                text_author = "Unknown"
            try:
                text_replies = replies[i2].text.strip()
            except IndexError:
                text_replies = "0"
            try:
                text_views = views[i2].text.strip()
            except IndexError:
                text_views = '0'
                
            lines_to_write.append(f'Форум ID:{forum_id} | Стр:{pagination} | Тема: {text_name2} | Автор: {text_author} | Ответов: {text_replies} | Просмотров: {text_views}\n')
        
        # Быстрая дозапись в файл
        if lines_to_write:
            with open('forumarch_parsing.txt', 'a', encoding='utf-8') as f:
                f.writelines(lines_to_write)
                
    except Exception:
        # Если какой-то запрос отвалился по таймауту — просто игнорим, чтобы скрипт не падал
        pass

# 2. А теперь запускаем мега-движок
if __name__ == '__main__':
    print("[+] Готовим список задач...")
    
    # Генерируем список всех комбинаций (forum_id, pagination)
    tasks = []
    for id_forum in range(1, 50):
        for pagination in range(1, 2766):
            tasks.append((id_forum, pagination))
            
    print(f"[+] Всего задач на парсинг: {len(tasks)}")
    print("[+] Запуск многопоточного движка в 20 потоков...")
    
    start_time = time.time()
    
    # max_workers=20 означает, что Python будет делать 20 запросов ОДНОВРЕМЕННО
    with ThreadPoolExecutor(max_workers=20) as executor:
        # executor.submit отправляет задачу в работу
        for forum_id, pagination in tasks:
            executor.submit(parse_page, forum_id, pagination)
            
    end_time = time.time()
    print(f"[+] Парсинг окончен за {round((end_time - start_time) / 60, 2)} минут!")
