from flask import Flask, render_template, request, redirect, url_for, session, flash

from app import db
from app.db import validate_user

DATABASE_URL = 'data/db.sqlite'

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='Marina_secret_key',
)


@app.route('/', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        val = validate_user(username, password)

        if val['success']:
            session.clear()
            session['id'] = val['id']
            session['login'] = val['login']
            session['first_name'] = val['first_name']
            session['last_name'] = val['last_name']

            return redirect(url_for('inbox', username=session['id']))

        flash(val['error'])

    return render_template('login.html')


@app.route('/inbox')
def inbox():
    search_email = session['id']
    inbox_result = db.inbox_for_user(DATABASE_URL, search_email)
    return render_template('inbox.html', mails=inbox_result)


if __name__ == '__main__':
    app.run()
