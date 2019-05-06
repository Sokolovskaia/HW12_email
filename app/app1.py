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
    inbox_result = db.inbox_for_user(search_email)
    count_result = db.count_inbox_for_menu(search_email)
    return render_template('inbox.html', mails=inbox_result, inbox_count=count_result)



@app.route('/outbox')
def outbox():
    search_email = session['id']
    outbox_result = db.outbox_for_user(search_email)
    count_result = db.count_inbox_for_menu(search_email)
    return render_template('outbox.html', mails=outbox_result, inbox_count=count_result)

@app.route('/drafts')
def drafts():
    search_email = session['id']
    drafts_result = db.drafts_for_user(search_email)
    count_result = db.count_inbox_for_menu(search_email)
    return render_template('drafts.html', mails=drafts_result, inbox_count=count_result)

@app.route('/basket')
def basket():
    search_email = session['id']
    basket_result = db.basket_for_user(search_email)
    count_result = db.count_inbox_for_menu(search_email)
    return render_template('basket.html', mails=basket_result, inbox_count=count_result)


@app.route('/letter/<letter_id>')
def letter(letter_id):
    letter_result = db.full_letter(letter_id)
    return render_template('letter.html', mails=letter_result)







if __name__ == '__main__':
    app.run()
