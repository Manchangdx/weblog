from flask import jsonify, request, current_app, g, url_for

from . import api
from .decorators import comment_required
from ..models import db, Blog, Comment


@api.route('/comments')
def get_comments():
    '''获取全部评论
    '''
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.time_stamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comments/<int:id>')
def get_comment(id):
    '''获取某个评论
    '''
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/blogs/<int:id>/comments/')
def get_blog_comments(id):
    '''获取某篇博客的全部评论
    '''
    blog = Blog.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = blog.comments.order_by(Comment.time_stamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_blog_comments', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_blog_comments', id=id, page=page+1)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/blogs/<int:id>/add_comment/', methods=['POST'])
@comment_required
def add_blog_comment(id):
    '''为某篇博客添加评论
    '''
    blog = Blog.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.blog = blog
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
        {'Location': url_for('api.get_comment', id=comment.id)}
