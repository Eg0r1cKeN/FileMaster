import json
import sqlite3
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

js = json.load(open('magic_smile.json'))

db = js['filename']
trans = tuple(js['trans'].split(', '))
smile = int(js['smile'])

sqlite_connection = sqlite3.connect(db)
cursor = sqlite_connection.cursor()

sqlite_select_query = f'SELECT * from Witches where "in_whom_turn_into" in {trans} and exist_smile = {smile}'
cursor.execute(sqlite_select_query)
records = cursor.fetchall()

lst = []

for row in records:
    lst.append({
        "witch": row[1],
        "who": row[2],
        "in whom": row[3]
    })


@app.route('/smile')
def smile():
    return json.dumps(lst)


lst.sort(key=lambda x: x['witch'])

app.run(port=5000, host='127.0.0.1')
