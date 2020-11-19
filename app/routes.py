from app import app
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('todos', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, checked, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    return render_template('todos/index.html', posts=posts)


def create_comments(id):
    db = get_db()
    for i in range(3):
        db.execute(
            'INSERT INTO comment (body, post_id)'
            ' VALUES (?, ?)',
            ('Комментарий {} к посту {}'.format(i+1, id), id)
        )
    db.commit()


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor_used = db.execute(
                'INSERT INTO post (title, body, author_id, checked)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], False)
            )
            post_id = cursor_used.lastrowid
            db.commit()
            create_comments(post_id)
            return redirect(url_for('todos.index'))

    return render_template('todos/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, checked, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('todos.index'))

    return render_template('todos/update.html', post=post)


@bp.route('/<int:id>/checked', methods=('POST', ))
@login_required
def checked(id):
    db = get_db()
    db.execute(
        'UPDATE post SET checked = ?'
        ' WHERE id = ?',
        (request.form['checked'], id)
    )
    db.commit()

    return redirect(url_for('todos.index'))


@bp.route('/<int:id>/viewtask', methods=('GET',))
@login_required
def viewtask(id):
    post = get_post(id)
    return render_template('todos/viewtask.html', post=post)


@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('todos.index'))


def get_comments(id, check_author=True):
    comments = get_db().execute(
        'SELECT c.id, c.body, post_id, author_id, username'
        ' FROM comment c JOIN post p ON c.post_id = p.id JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchall()

    if check_author and comments[0]['author_id'] != g.user['id']:
        abort(403)

    return [comment['body'] for comment in comments]

@bp.route('/<int:id>/comments', methods=('GET',))
@login_required
def comments(id):
    comments = get_comments(id)
    return jsonify(result=comments)