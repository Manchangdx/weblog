from flask import jsonify, request, current_app

from . import api
from ..models import User, Blog


@api.route('/users/<int:id>')
def get_user(id):
    '''获取某个用户信息
    '''
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/<int:id>/blogs/')
def get_user_blogs(id):
    '''获取某个用户的全部博客信息
    '''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.blogs.order_by(Blog.time_stamp.desc()).paginate(
        page, per_page=current_app.config['BLOGS_PER_PAGE'],
        error_out=False)
    blogs = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_blogs', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_blogs', id=id, page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/<int:id>/followed_blogs/')
def get_user_followed_blogs(id):
    '''获取某个用户关注的其他用户的全部博客信息
    '''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_blogs.order_by(Blog.time_stamp.desc()).paginate(
        page, per_page=current_app.config['BLOGS_PER_PAGE'],
        error_out=False)
    blogs = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_blogs', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_blogs', id=id, page=page+1)
    return jsonify({
        'blogs': [blog.to_json() for blog in blogs],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
