from flask import redirect, request, render_template, current_app, url_for
from flask_login import login_required

from . import admin
from .forms import AdminProfileForm
from .decorators import admin_required, moderate_required
from ..models import db, User, Comment


@admin.route('admin-edit-profile/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_profile(id):
    '''管理员编辑用户的个人信息'''
    user = User.query.get(id)
    form = AdminProfileForm(user, obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.add(user)
        db.session.commit()
        flash('个人信息已更改', 'success')
        return redirect(url_for('.index', name=user.name))
    return render_template('user/edit_profile.html', form=form)


@admin.route('/moderate_comments')
@moderate_required
def moderate_comments():
    '''管理评论'''
    page = request.args.get('page', default=1, type=int)
    pagination = Comment.query.order_by(Comment.time_stamp.desc()).paginate(
            page,
            per_page = current_app.config['COMMENTS_PER_PAGE'],
            error_out = False
    )
    comments = pagination.items
    return render_template('moderate_comments.html', comments=comments,
            page=page, pagination=pagination)


@admin.route('/comment/disable/<int:id>')
@moderate_required
def disable_comment(id):
    '''管理员封禁评论'''
    comment = Comment.query.get_or_404(id)
    comment.disable = 1
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate_comments'))


@admin.route('/comment/enable/<int:id>')
@moderate_required
def enable_comment(id):
    '''管理员解封评论'''
    comment = Comment.query.get_or_404(id)
    comment.disable = 0
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate_comments'))
