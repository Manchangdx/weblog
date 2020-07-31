from flask import abort, redirect, url_for, flash, render_template
from flask import request, current_app
from flask_login import login_required, login_user, current_user

from . import user
from .forms import ProfileForm, ChangePasswordForm, ChangeEmailForm
from .forms import BeforeResetPasswordForm, ResetPasswordForm
from ..main.forms import BlogForm
from ..models import db, User, Role, Blog, Permission
from ..email import send_email


# 未通过验证的用户登录时或者登录后后发起 POST 请求时
# main.before_request 函数会调用此函数来处理请求
# 浏览器会收到带有「重发确认邮件按钮」的页面
@user.route('/unconfirmed_user')
@login_required
def unconfirmed_user():
    '''未确认用户页面'''
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('.index'))
    return render_template('user/confirm.html')


# 接上一个视图函数，浏览器上点击「重发确认邮件按钮」后，由此函数来处理
@user.route('/repeat_confirm')
@login_required
def resend_confirm_email():
    '''重新发送验证邮件'''
    token = current_user.generate_confirm_user_token()
    send_email(current_user, current_user.email, 'confirm_user', token)
    flash('已经发送一封带有确认指令的邮件到你的邮箱，请注意查收。', 'info')
    return redirect(url_for('main.index'))


@user.route('/<name>/index')
def index(name):
    '''用户的个人主页'''
    user = User.query.filter_by(name=name).first()
    if not user:
        abort(404)
    blogs = user.blogs.order_by(Blog.time_stamp.desc())
    return render_template('user/index.html', user=user, blogs=blogs,
            Permission=Permission)


@user.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''用户编辑自己的个人信息'''
    # obj 参数可以预先把现有的用户信息填到表单中
    form = ProfileForm(current_user, obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.add(current_user)
        db.session.commit()
        flash('个人信息已更改', 'success')
        return redirect(url_for('.index', name=current_user.name))
    return render_template('user/edit_profile.html', form=form)


@user.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    '''登录后修改密码'''
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.add(current_user)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('.index', name=current_user.name))
    return render_template('user/change_password.html', form=form)


@user.route('/before-reset-password', methods=['GET', 'POST'])
def before_reset_password():
    '''忘记密码时利用邮箱重置密码，首先填写邮箱'''
    form = BeforeResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token = user.generate_confirm_user_token()
        send_email(user, user.email, 'reset_password', token)
        flash('已经发送一封带有确认指令的邮件到你的邮箱，请注意查收。', 'info')
    return render_template('user/reset_password.html', form=form)


@user.route('/reset-password/<name>/<token>', methods=['GET', 'POST'])
def reset_password(name, token):
    '''重置密码时，点击验证邮件中的链接时，用此视图函数处理'''
    user = User.query.filter_by(name=name).first()
    if user and user.confirm_user(token):
        # 这是填写新密码的表单
        form = ResetPasswordForm()
        if request.method == 'GET':
            flash('邮箱已确认，请重置密码。', 'success')
            return render_template('user/reset_password.html', form=form)
        if form.validate_on_submit():
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flash('密码已重置。', 'success')
            return redirect(url_for('.index', name=user.name))
    else:
        flash('你这链接不对呀！', 'danger')
    return redirect(url_for('user.index'))


@user.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    '''已登录用户变更邮箱'''
    form = ChangeEmailForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.confirmed = 0
        db.session.add(current_user)
        db.session.commit()
        token = current_user.generate_confirm_user_token()
        send_email(current_user, current_user.email, 'change_email', token)
        flash('已经发送一封带有确认指令的邮件到你的邮箱，请注意查收。', 'info')
    return render_template('user/change_email.html', form=form)


@user.route('/change-email/<token>')
@login_required
def confirm_change_email(token):
    '''变更邮箱时，邮件中的链接用此视图函数处理'''
    if current_user.confirm_user(token):
        current_user.confirmed = 1
        db.session.add(current_user)
        db.session.commit()
        flash('成功变更邮箱！', 'success')
        return redirect(url_for('.index', name=current_user.name))
    flash('你这链接不对呀！', 'danger')
    return redirect(url_for('user.index'))


@user.route('/edit-blog/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_blog(id):
    '''用户编写博客'''
    blog = Blog.query.get_or_404(id)
    # 如果当前登录用户既不是作者又不是管理员，则没有编辑权限，返回 403
    if current_user != blog.author and not current_user.is_administrator:
        abort(403)
    form = BlogForm(obj=blog)
    if form.validate_on_submit():
        form.populate_obj(blog)
        db.session.add(blog)
        db.session.commit()
        flash('博客已经更新', 'success')
        return redirect(url_for('blog.index', id=blog.id))
    return render_template('edit_blog.html', form=form)


@user.route('/follow/<name>')
@login_required
def follow(name):
    '''关注用户'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('该用户不存在。', 'warning')
        return redirect(url_for('user.index'))
    if current_user.is_following(user):
        flash('在此操作之前，你已经关注了该用户。', 'info')
    else:
        current_user.follow(user)
        flash('成功关注此用户。', 'success')
    return redirect(url_for('.index', name=name))


@user.route('/unfollow/<name>')
@login_required
def unfollow(name):
    '''取关用户'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('该用户不存在。', 'warning')
        return redirect(url_for('user.index'))
    if not current_user.is_following(user):
        flash('你并未关注此用户。', 'info')
    else:
        current_user.unfollow(user)
        flash('成功取关此用户。', 'success')
    return redirect(url_for('.index', name=name))


@user.route('/<name>/followed')
def followed(name):
    '''【user 关注了哪些用户】的页面'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('用户不存在。', 'warning')
        return redirect(url_for('user.index'))
    page = request.args.get('page', default=1, type=int)
    pagination = user.followed.paginate(
            page,
            per_page = current_app.config['USERS_PER_PAGE'],
            error_out = False
    )
    follows = [{'user': f.followed, 'time_stamp': f.time_stamp}
            for f in pagination.items]
    # 这个模板是「关注了哪些用户」和「被哪些用户关注了」共用的模板
    return render_template('user/follow.html', user=user, title='我关注的人',
            endpoint='user.followed', pagination=pagination, follows=follows)


@user.route('/<name>/followers')
def followers(name):
    '''【user 被哪些用户关注了】的页面'''
    user = User.query.filter_by(name=name).first()
    if not user:
        flash('用户不存在。', 'warning')
        return redirect(url_for('user.index'))
    page = request.args.get('page', default=1, type=int)
    pagination = user.followers.paginate(
            page,
            per_page = current_app.config['USERS_PER_PAGE'],
            error_out = False
    )
    follows = [{'user': f.follower, 'time_stamp': f.time_stamp}
            for f in pagination.items]
    return render_template('user/follow.html', user=user, title='关注我的人',
            endpoint='user.followers', pagination=pagination, follows=follows)
