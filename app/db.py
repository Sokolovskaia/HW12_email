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
            '''SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id 
            FROM letters l, users u 
            WHERE l.recipient_id = :search_email 
            AND l.sender_id = u.id 
            AND l.deleted = 0 
            AND l.draft = 0 
            ORDER BY l.letter_id 
            DESC LIMIT 20''',
            {'search_email': search_email}).fetchall()
        return result


def outbox_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id 
                FROM letters l, users u 
                WHERE l.sender_id = :search_email 
                AND l.recipient_id = u.id 
                AND l.deleted = 0 
                AND l.draft = 0 
                ORDER BY l.letter_id 
                DESC LIMIT 20''',
            {'search_email': search_email}).fetchall()
        return result


def drafts_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id 
                FROM letters l LEFT JOIN users u ON l.recipient_id = u.id 
                WHERE l.sender_id = :search_email 
                AND l.deleted = 0 
                AND l.draft = 1 
                ORDER BY l.letter_id 
                DESC LIMIT 20''',
            {'search_email': search_email}).fetchall()
        return result


def basket_for_user(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT u.surname, u.email, l.topic, l.letter_date, l.letter_id 
                FROM letters l LEFT JOIN users u ON l.recipient_id = u.id 
                WHERE :search_email IN (l.sender_id, l.recipient_id) 
                AND l.deleted = 1 
                AND l.draft = 0 
                ORDER BY l.letter_id 
                DESC LIMIT 20''',
            {'search_email': search_email}).fetchall()
        return result


def full_letter(search_letter):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT l.topic, u.surname, u.email, l.letter_date, l.letter_body 
                FROM letters l LEFT JOIN users u ON l.recipient_id = u.id 
                WHERE l.letter_id = :letter_id''',
            {'letter_id': search_letter}).fetchone()
        return result


def count_inbox_for_menu(search_email):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT SUM (inbox)                                                     count_for_inbox
                    , SUM (inbox_unread)                                              count_for_inbox_unread
                    , SUM (outbox)                                                    count_for_outbox
                    , SUM (draft)                                                     count_for_draft
                    , SUM (basket)                                                    count_for_basket
                FROM (
                   SELECT COUNT(*)                                                    inbox
                        , COALESCE(SUM(CASE WHEN l.reading_status = 0 THEN 1 END), 0) inbox_unread
                        , 0                                                           outbox
                        , 0                                                           draft
                        , 0                                                           basket
                   FROM letters l
                   WHERE l.recipient_id = :search_email
                     AND l.draft = 0
                     AND l.deleted = 0
                   UNION
                   SELECT 0                                                           inbox
                        , 0                                                           inbox_unread
                        , COALESCE(SUM(CASE WHEN l.draft = 0 THEN 1 END), 0)          outbox
                        , COALESCE(SUM(CASE WHEN l.draft = 1 THEN 1 END), 0)          draft
                        , 0                                                           basket
                   FROM letters l
                   WHERE l.sender_id = :search_email
                     AND l.deleted = 0
                   UNION
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


def create(search_email, recipient, topic, body, date):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''INSERT INTO letters (sender_id, recipient_id, topic, letter_body, letter_date) 
               VALUES (:search_email, :recipient, :topic, :body, :date)''',
            {'search_email': search_email, 'recipient': recipient, 'topic': topic, 'body': body,
             'date': date})
        db.commit()
    return result
