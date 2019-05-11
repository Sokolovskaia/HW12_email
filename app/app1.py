import waitress
from flask import Flask, render_template, request, redirect, url_for, session, flash

from app import db
from app.db import validate_user

import os

DATABASE_URL = 'data/db.sqlite'


def start():
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
        user_email = session['login']
        user_surname = session['last_name']
        inbox_result = db.inbox_for_user(search_email)
        count_result = db.count_inbox_for_menu(search_email)
        return render_template('inbox.html', mails=inbox_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname)

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
        search_email = session['id']
        count_result = db.count_inbox_for_menu(search_email)
        return render_template('letter.html', mails=letter_result, inbox_count=count_result)

    @app.route('/create_letter', methods=('GET', 'POST'))
    def create_letter():
        search_email = session['id']
        count_result = db.count_inbox_for_menu(search_email)
        if request.method == 'POST':
            recipient = request.form['recipient']
            topic = request.form['topic']
            body = request.form['body']
            date = request.form['date']
            draft = request.form['draft']
            db.create(search_email, recipient, topic, body, date, draft)

            return redirect(url_for('inbox'))

        return render_template('new_letter.html', inbox_count=count_result)

    @app.route('/statistics')
    def statistics():
        stat1 = db.statistics_who_writes_to_whom()  # кто с кем переписывается
        stat2 = db.most_letters()  # Кто с кем больше всего переписывается (кол-во отправленных/полученных)
        stat3 = db.ignored_users()  # Кто кого игнорирует (не отвечает на письма)
        stat4 = db.statistics_who_writes_to_whom_by_units()    # Кто с кем переписывается разрезе отделов (unit'ов)
        stat5 = db.most_letters_by_units()    # Кто с кем переписывается разрезе отделов (unit'ов)
        stat6 = db.ignored_users_by_units()    # Кто кого игнорирует (не отвечает на письма) разрезе отделов (unit'ов)
        return render_template('statistics.html', result_statistics1=stat1, result_statistics2=stat2,
                               result_statistics3=stat3, result_statistics4=stat4, result_statistics5=stat5, result_statistics6=stat6)

    if os.getenv('APP_ENV') == 'PROD' and os.getenv('PORT'):
        waitress.serve(app, port=os.getenv('PORT'))
    else:
        app.run(port=9873, debug=True)


if __name__ == '__main__':
    start()
