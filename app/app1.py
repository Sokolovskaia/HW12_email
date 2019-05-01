from flask import Flask, render_template, redirect, url_for

from app import db

DATABASE_URL = 'data/db.sqlite'

app = Flask(__name__)


@app.route('/')
def index():
    user_name = db.get_name(DATABASE_URL)
    return render_template('index.html', user_name=user_name)


# @app.route('/<id>/remove', methods=['POST'])
# def remove(id):
#     db.remove_note_by_id(DATABASE_URL, id)
#     return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
