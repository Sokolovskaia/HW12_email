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
            '''SELECT l.letter_id, l.topic, u.surname, u.email, l.letter_date, l.letter_body 
                FROM letters l LEFT JOIN users u ON l.recipient_id = u.id 
                WHERE l.letter_id = :letter_id''',
            {'letter_id': search_letter}).fetchone()
        return result


def chain_of_letters(search_letter):  # ----Посмотреть всю цепочку писем
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''WITH RECURSIVE p1 AS (
      SELECT letter_id
           , parent_letter_id
           , 0 AS level
           , topic
           , letter_body
           , letter_date
        FROM letters
       WHERE letter_id = :letter_id
   UNION ALL
      SELECT l.letter_id
           , l.parent_letter_id
           , p1.level - 1
           , l.topic
           , l.letter_body
           , l.letter_date
      FROM letters l
      JOIN p1 ON p1.parent_letter_id=l.letter_id
    ), p2 AS (
      SELECT letter_id
           , parent_letter_id
           , level
           , topic
           , letter_body
           , letter_date
        FROM p1
       UNION
      SELECT l.letter_id
           , l.parent_letter_id
           , p2.level + 1
           , l.topic
           , l.letter_body
           , l.letter_date
        FROM letters l
        JOIN p2 ON l.parent_letter_id=p2.letter_id
        )
      SELECT *
        FROM p2
    ORDER BY level''',
            {'letter_id': search_letter}).fetchall()
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


def create(search_email, recipient, topic, body, date, draft):
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''INSERT INTO letters (sender_id, recipient_id, topic, letter_body, letter_date, draft) 
               VALUES (:search_email, :recipient, :topic, :body, :date, :draft)''',
            {'search_email': search_email, 'recipient': recipient, 'topic': topic, 'body': body,
             'date': date, 'draft': draft})
        db.commit()
    return result


def statistics_who_writes_to_whom():
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT DISTINCT l.sender_id, group_concat(DISTINCT l.recipient_id) recipients
            FROM letters l
            WHERE l.draft = 0
            GROUP BY l.sender_id''').fetchall()
        return result


def most_letters():
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT CASE WHEN l.sender_id <= l.recipient_id then l.sender_id else l.recipient_id end person1
                    , CASE WHEN l.sender_id <= l.recipient_id then l.recipient_id else l.sender_id end person2
                    , count (0) num_letters
                 FROM letters l
                WHERE l.draft = 0
                GROUP BY person1, person2
                ORDER BY num_letters DESC
                LIMIT 10''').fetchall()
        return result


def ignored_users():
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT CASE WHEN l.sender_id <= l.recipient_id then l.sender_id else l.recipient_id end person1
                    , CASE WHEN l.sender_id <= l.recipient_id then l.recipient_id else l.sender_id end person2
                    , coalesce (sum (CASE WHEN l.sender_id <= l.recipient_id then 1 else 0 end), 0) sent_by_person1
                    , coalesce (sum (CASE WHEN l.sender_id <= l.recipient_id then 0 else 1 end), 0) sent_by_person2
                 FROM letters l
                WHERE l.draft = 0
             GROUP BY person1, person2
         HAVING 0 IN (sent_by_person1, sent_by_person2)''').fetchall()
        return result


def statistics_who_writes_to_whom_by_units():  # Кто с кем переписывается разрезе отделов (unit'ов)
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT u1.unit    
                    , l.sender_id
                    , group_concat(DISTINCT l.recipient_id) recipients
                 FROM letters l
                 JOIN users u1
                   ON l.sender_id = u1.id
                 JOIN users u2
                   ON l.recipient_id = u2.id
                WHERE u1.unit = u2.unit
                  AND l.draft = 0
             GROUP BY l.sender_id''').fetchall()
        return result


def most_letters_by_units():  # Кто с кем больше всего переписывается (кол-во отправленных/полученных) разрезе отделов (unit'ов)
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT CASE WHEN l.sender_id <= l.recipient_id then l.sender_id else l.recipient_id end person1   ----Кто с кем больше всего переписывается (кол-во отправленных/полученных) разрезе отделов (unit'ов)
                    , CASE WHEN l.sender_id <= l.recipient_id then l.recipient_id else l.sender_id end person2
                    , count (0) num_letters
                              , u1.unit
                           FROM letters l
                           JOIN users u1
                             ON l.sender_id = u1.id
                           JOIN users u2
                             ON l.recipient_id = u2.id
                          WHERE u1.unit = u2.unit
                            AND l.draft = 0
                       GROUP BY person1, person2
                       ORDER BY num_letters DESC
                          LIMIT 10''').fetchall()
        return result


def ignored_users_by_units():  # Кто кого игнорирует (не отвечает на письма) разрезе отделов (unit'ов)
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''SELECT CASE WHEN l.sender_id <= l.recipient_id then l.sender_id else l.recipient_id end person1
                     , CASE WHEN l.sender_id <= l.recipient_id then l.recipient_id else l.sender_id end person2
                               , coalesce(sum(CASE WHEN l.sender_id <= l.recipient_id then 1 else 0 end), 0)      sent_by_person1
                               , coalesce(sum(CASE WHEN l.sender_id <= l.recipient_id then 0 else 1 end), 0)      sent_by_person2
                               , u1.unit
                            FROM letters l
                            JOIN users u1
                              ON l.sender_id = u1.id
                            JOIN users u2
                              ON l.recipient_id = u2.id
                           WHERE u1.unit = u2.unit
                             AND l.draft = 0
                        GROUP BY person1
                               , person2
                    having 0 in (sent_by_person1, sent_by_person2)''').fetchall()
        return result


def length_of_longest_chain():  # Длина самой большой цепочки
    with open_db(DATABASE_URL) as db:
        result = db.cursor().execute(
            '''WITH RECURSIVE p1 AS (
      SELECT letter_id first_id
           , letter_id
        FROM letters
       WHERE parent_letter_id ISNULL
   UNION ALL
      SELECT p1.first_id
           , l.letter_id
        FROM letters l
  JOIN p1 ON p1.letter_id=l.parent_letter_id
  )
      SELECT first_id
  , count(*) num_letter
  FROM p1
    GROUP BY first_id
    ORDER BY num_letter DESC
       LIMIT 1''').fetchall()
        return result
