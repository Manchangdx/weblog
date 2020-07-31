from flask import url_for, redirect, flash, request, render_template
from flask import current_app
from flask_login import current_user

from . import blog
from .forms import CommentForm
from ..models import db, Permission, Blog, Comment



@blog.route('/<int:id>', methods=['GET', 'POST'])
def index(id):
    '''每篇博客的单独页面，便于分享'''
    blog = Blog.query.get_or_404(id)
    # 页面提供评论输入框
    form = CommentForm()
    if request.method == 'POST':
        if not current_user:
            flash('登录后才能评论', 'warning')
            redirect(url_for('main.login'))
        if form.validate_on_submit():
            comment = Comment(body=form.body.data, blog=blog, 
                    author=current_user)
            db.session.add(comment)
            db.session.commit()
            flash('评论成功。', 'success')
            return redirect(url_for('.index', id=id))
    page = request.args.get('page', default=1, type=int)
    pagination = blog.comments.order_by(Comment.time_stamp.desc()).paginate(
            page,
            per_page = current_app.config['COMMENTS_PER_PAGE'],
            error_out = False
    )
    comments = pagination.items
    # hidebloglink 在博客页面中隐藏博客单独页面的链接
    # noblank 在博客页面中点击编辑按钮不在新标签页中打开
    return render_template('blog.html', blogs=[blog], hidebloglink=True,
            noblank=True, form=form, pagination=pagination,
            comments=comments, Permission=Permission)
