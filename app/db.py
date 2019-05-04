import sqlite3


def open_db(db_url):
    db = sqlite3.connect(db_url)
    db.row_factory = sqlite3.Row
    return db


def get_name(db_url, page=1):
    with open_db(db_url) as db:
        limit = 50
        offset = limit * (page - 1)
        user_name = db.cursor().execute(
            'SELECT id, surname, name, email, password FROM users LIMIT :limit OFFSET :offset',
            {'limit': limit, 'offset': offset}
        ).fetchall()
        return user_name


def search_email_user(db_url, search_email):
    with open_db(db_url) as db:
        search = db.cursor().execute(
            'SELECT u.surname, u.email, l.topic, l.letter_date, l.recipient_id FROM letters l, users u WHERE l.recipient_id = :search_email AND l.sender_id = u.id ORDER BY l.letter_id DESC LIMIT 20', {'search_email': search_email}).fetchall()
        return search
















# search = request.args.get('search')
#         if search:
#             products = product_manager.search_by_name(search)
#         else:
#             products = product_manager.items
#             search=''


#
# def search_notes(db_url, name):
#     pass
#
#
# def add_note(db_url, note):
#     pass
#
#
# def update_note(db_url, note):
#     pass
#
#
# def remove_note_by_id(db_url, note_id):
#     with open_db(db_url) as db:
#         db.cursor().execute(
#             'DELETE FROM notes WHERE id = :id',
#             {'id': note_id}
#         )
#         db.commit()
#
#
# def like_note_by_id(db_url, note_id):
#     pass
#
#
# def dislike_note_by_id(db_url, note_id):
#     pass
