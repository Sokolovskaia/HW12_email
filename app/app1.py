import waitress
from flask import Flask, render_template, request, redirect, url_for, session, flash

from app import db
from app.db import validate_user

import os


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

    @app.route('/inbox', methods=('GET', 'POST'))
    def inbox():
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        inbox_result = db.inbox_for_user(search_email)
        count_result = db.counts_for_menu(search_email)
        if request.method == 'POST':       # Удалить все входящие (поместить в корзину)
            db.from_inbox_to_basket(search_email)
            return redirect(url_for('inbox'))
        return render_template('inbox.html', mails=inbox_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='inbox')

    @app.route('/outbox')
    def outbox():
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        outbox_result = db.outbox_for_user(search_email)
        count_result = db.counts_for_menu(search_email)
        return render_template('inbox.html', mails=outbox_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='outbox')

    @app.route('/drafts', methods=('GET', 'POST'))
    def drafts():
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        drafts_result = db.drafts_for_user(search_email)
        count_result = db.counts_for_menu(search_email)
        if request.method == 'POST':       # Удалить все черновики (поместить в корзину)
            db.from_drafts_to_basket(search_email)
            return redirect(url_for('drafts'))
        return render_template('inbox.html', mails=drafts_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='drafts')

    @app.route('/basket', methods=('GET', 'POST'))
    def basket():
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        basket_result = db.basket_for_user(search_email)
        count_result = db.counts_for_menu(search_email)
        if request.method == 'POST':       # Очистить корзину
            db.clear_basket(search_email)
            return redirect(url_for('basket'))
        return render_template('inbox.html', mails=basket_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='basket')

    @app.route('/letter/<letter_id>')
    def letter(letter_id):
        letter_result = db.full_letter(letter_id)
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        count_result = db.counts_for_menu(search_email)
        return render_template('letter.html', mails=letter_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='letter')

    @app.route('/chain_full/<letter_id>')
    def chain_full(letter_id):
        chain_full_result = db.chain_of_letters(letter_id)
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        count_result = db.counts_for_menu(search_email)
        return render_template('chain_full.html', mails=chain_full_result, inbox_count=count_result,
                               user_email=user_email,
                               user_surname=user_surname, active_index='letter')

    @app.route('/create_letter', methods=('GET', 'POST'))
    def create_letter():
        letter_result = None
        search_email = session['id']
        user_email = session['login']
        user_surname = session['last_name']
        count_result = db.counts_for_menu(search_email)

        if request.method == 'POST':
            topic = request.form['topic']
            body = request.form['body']
            date = request.form['date']
            draft = request.form['draft']
            if 'letterid' in request.args.keys():
                let = request.args.get('letterid')
                db.update(let, topic, body, date, draft)
            else:
                recipient = request.form['recipient']
                db.create(search_email, recipient, topic, body, date, draft)

            return redirect(url_for('inbox'))

        if 'letterid' in request.args.keys():
            let = request.args.get('letterid')
            letter_result = db.full_letter(let)

        return render_template('new_letter.html', mails=letter_result, inbox_count=count_result, user_email=user_email,
                               user_surname=user_surname, active_index='create_letter')

    @app.route('/statistics')
    def statistics():
        stat1 = db.statistics_who_writes_to_whom()  # кто с кем переписывается
        stat2 = db.most_letters()  # Кто с кем больше всего переписывается (кол-во отправленных/полученных)
        stat3 = db.ignored_users()  # Кто кого игнорирует (не отвечает на письма)
        stat4 = db.statistics_who_writes_to_whom_by_units()  # Кто с кем переписывается разрезе отделов (unit'ов)
        stat5 = db.most_letters_by_units()  # Кто с кем переписывается разрезе отделов (unit'ов)
        stat6 = db.ignored_users_by_units()  # Кто кого игнорирует (не отвечает на письма) разрезе отделов (unit'ов)
        stat7 = db.length_of_longest_chain()  # Длина самой большой цепочки
        return render_template('statistics.html', result_statistics1=stat1, result_statistics2=stat2,
                               result_statistics3=stat3, result_statistics4=stat4, result_statistics5=stat5,
                               result_statistics6=stat6, result_statistics7=stat7)

    if os.getenv('APP_ENV') == 'PROD' and os.getenv('PORT'):
        waitress.serve(app, port=os.getenv('PORT'))
    else:
        app.run(port=9873, debug=True)


if __name__ == '__main__':
    start()
