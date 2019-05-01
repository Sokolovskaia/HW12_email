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
            'SELECT id, surname, name, email FROM users LIMIT :limit OFFSET :offset',
            {'limit': limit, 'offset': offset}
        ).fetchall()
        return user_name

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
