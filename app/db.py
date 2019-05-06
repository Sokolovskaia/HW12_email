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


def inbox_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id FROM letters l, users u WHERE l.recipient_id = :search_email AND l.sender_id = u.id AND l.deleted = 0 AND l.draft = 0 ORDER BY l.letter_id DESC LIMIT 20',
            {'search_email': search_email}).fetchall()
        return result


def outbox_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id FROM letters l, users u WHERE l.sender_id = :search_email AND l.recipient_id = u.id AND l.deleted = 0 AND l.draft = 0 ORDER BY l.letter_id DESC LIMIT 20',
            {'search_email': search_email}).fetchall()
        return result


def drafts_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id FROM letters l LEFT JOIN users u ON l.recipient_id = u.id WHERE l.sender_id = :search_email AND l.deleted = 0 AND l.draft = 1 ORDER BY l.letter_id DESC LIMIT 20',
            {'search_email': search_email}).fetchall()
        return result


def basket_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id FROM letters l LEFT JOIN users u ON l.recipient_id = u.id WHERE :search_email IN (l.sender_id, l.recipient_id) AND l.deleted = 1 AND l.draft = 0 ORDER BY l.letter_id DESC LIMIT 20',
            {'search_email': search_email}).fetchall()
        return result


def full_letter(search_letter):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            'SELECT l.topic, u.surname, u.email, l.letter_date, l.letter_body FROM letters l LEFT JOIN users u ON l.recipient_id = u.id WHERE l.letter_id = :letter_id',
            {'letter_id': search_letter}).fetchone()
        return result


def count_inbox_for_menu(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''select sum (inbox) count_for_inbox
                    , sum (inbox_unread) count_for_inbox_unread
                    , sum (outbox) count_for_outbox
                    , sum (draft) count_for_draft
                    , sum (basket) count_for_basket
  from (
           SELECT COUNT(*)                                                    inbox
                , coalesce(SUM(case when l.reading_status = 0 then 1 END), 0) inbox_unread
                , 0                                                           outbox
                , 0                                                           draft
                , 0                                                           basket
           FROM letters l
           WHERE l.recipient_id = :search_email
             AND l.draft = 0
             AND l.deleted = 0
           union
           SELECT 0                                                           inbox
                , 0                                                           inbox_unread
                , coalesce(SUM(case when l.draft = 0 then 1 END), 0)          outbox
                , coalesce(SUM(case when l.draft = 1 then 1 END), 0)          draft
                , 0                                                           basket
           FROM letters l
           WHERE l.sender_id = :search_email
             AND l.deleted = 0
           union
           SELECT 0                                                           inbox
                , 0                                                           inbox_unread
                , 0                                                           outbox
                , 0                                                           draft
                , COUNT(*)                                                    basket
           FROM letters l
           WHERE :search_email IN (l.sender_id, l.recipient_id)
             AND l.deleted = 1
       )''',
            {'search_email': search_email}).fetchone()
        return result
