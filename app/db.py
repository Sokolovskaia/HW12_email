import sqlite3

from werkzeug.security import check_password_hash

DATABASE_URL = 'data/db.sqlite'


def open_db(db_url):
    db = sqlite3.connect(db_url)
    db.row_factory = sqlite3.Row
    return db


def validate_user(login, password):
    with open_db(DATABASE_URL) as db:
        result = {'success': False}
        user = db.execute('SELECT * FROM users WHERE email = :login', {'login': login}).fetchone()

        if user is None:
            result['error'] = 'Пользователь не найден'
        elif not user['password'] == password:
            result['error'] = 'Неверный пароль'
        else:
            result['id'] = user['id']
            result['login'] = user['email']
            result['first_name'] = user['name']
            result['last_name'] = user['surname']
            result['success'] = True

        return result


def inbox_for_user(db_url, search_email):
    with open_db(db_url) as db:
        result = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.recipient_id FROM letters l, users u WHERE l.recipient_id = :search_email AND l.sender_id = u.id ORDER BY l.letter_id DESC LIMIT 20',
            {'search_email': search_email}).fetchall()
        return result
