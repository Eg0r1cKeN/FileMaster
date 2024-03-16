from requests import get, post, put, delete

# Проверка получения всех новостей
# response = get('http://localhost:8080/api/news').json()
# print(response)

# if response and 'news' in response:
#     print(response['news'][0]['title'])

# Проверка получения всех одной новости
# response = get('http://localhost:8080/api/news/1').json()
# print(response)

# if response and 'news' in response:
#     print(response['news']['title'])

# Проверка на создание новости

# print(post('http://localhost:8080/api/news', json={}).json())

# print(post('http://localhost:8080/api/news',
#            json={'title': 'Заголовок'}).json())

response = post('http://localhost:8080/api/news',
           json={'title': 'Заголовок',
                 'content': 'Текст новости',
                 'user_id': 1,
                 'is_private': False}).json()
print(response)
if response:
    if 'id' in response:
        print(get(f'http://localhost:8080/api/news/{response["id"]}').json())

# Проверка на изменение новости
response = put(f'http://localhost:8080/api/news/{response["id"]}',
           json={'title': 'Заголовок Измененный'}).json()
print(response)
if response:
    if 'id' in response:
        print(get(f'http://localhost:8080/api/news/{response["id"]}').json())

# Проверка на удаление новости
response = delete(f'http://localhost:8080/api/news/{response["id"]}').json()
print(response)