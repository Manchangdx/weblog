from flask import jsonify, request, current_app, url_for, g

from . import api
from .decorators import write_required
from ..models import db, User, Blog, Comment


@api.route('/blogs/')
def get_blogs():
    '''获取全部博客
    '''
    page = request.args.get('page', 1, type=int)
    pagination = Blog.query.paginate(
        page, per_page=current_app.config['BLOGS_PER_PAGE'],
        error_out=False)
    blogs = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_blogs', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_blogs', page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/blogs/<int:id>')
def get_blog(id):
    '''获取某篇博客
    '''
    blog = Blog.query.get_or_404(id)
    return jsonify(blog.to_json())


@api.route('/blogs', methods=['POST'])
@write_required
def new_blog():
    blog = Blog.from_json(request.json)
    blog.author = g.current_user
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json()), 201, \
        {'Location': url_for('api.get_blog', id=blog.id)}


@api.route('/blogs/<int:id>', methods=['PUT'])
@write_required
def edit_blog(id):
    blog = Blog.query.get_or_404(id)
    if g.current_user != blog.author:
        return forbidden('Insufficient permissions')
    blog.body = request.json.get('body', blog.body)
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_json())
