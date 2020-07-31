'''
页面请求预处理，网站首页、注册、登录、错误处理
'''

from flask import url_for, redirect, flash, request, render_template
from flask import current_app, make_response, jsonify
from flask_login import login_required, login_user, logout_user, current_user

from . import main
from .forms import RegisterForm, LoginForm, BlogForm
from ..models import db, User, Blog


# 由 before_app_request 所装饰的视图函数
# 会在所有请求（包括视图函数不在这个蓝图下的请求）被处理之前执行
# 相当于服务器收到任何请求后，先经过此函数进行预处理
@main.before_app_request
def before_request():
    '''页面请求预处理'''
    # current_user 默认为匿名用户，其 is_authenticated 属性值为 False
    # 用户登录后，current_user 为登录用户，is_authenticated 属性值为 True
    if current_user.is_authenticated:
        # 那么执行此方法刷新「用户最近操作时间」
        current_user.ping()
        # 未验证的用户登录后要发出 POST 请求的话，让用户先通过验证
        # 如果用户未通过邮箱确认身份，且为 POST 请求
        if not current_user.confirmed and request.method == 'POST':
            # 那么把请求交给 user.unconfirmed_user 函数处理
            return redirect(url_for('user.unconfirmed_user'))


@main.route('/', methods=['GET', 'POST'])
def index():
    '''网站首页'''
    # 首页可以展示全部博客或用户关注者的博客
    # 默认展示全部博客，这里定义一个变量来控制此事
    show_followed = False
    form = BlogForm()
    # 凡是登录成功的用户，就有写博客的权限
    if current_user.is_authenticated:
        show_followed = request.cookies.get('show_followed')
        if form.validate_on_submit():
            blog = Blog()
            form.populate_obj(blog)
            blog.author = current_user
            db.session.add(blog)
            db.session.commit()
            flash('成功发布博客。', 'success')
            # 把博客存入数据库，发送 flash 消息
            # 然后重定向到 index 视图函数，使用 GET 方法再次运行这个函数
            return redirect(url_for('.index'))
    # 根据 show_followed 变量获取查询对象
    query = Blog.query if not show_followed else current_user.followed_posts
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Blog.time_stamp.desc()).paginate(
            page,
            per_page = current_app.config['BLOGS_PER_PAGE'],
            error_out = False
    )
    blogs = pagination.items
    return render_template('index.html', form=form, blogs=blogs, 
            show_followed=show_followed, pagination=pagination)


@main.route('/show-all-blogs')
@login_required
def show_all_blogs():
    '''展示所有用户的博客'''
    # 创建 make_response 对象，该对象的 set_cookie 方法可以创建 Cookie 键值对
    # 当浏览器收到响应后，会存储 Cookies 到本地
    # 下次再发送请求的时候会带上 Cookies 
    # 视图函数可以使用 request.cookies.get 方法获取之
    resp = make_response(redirect(url_for('.index')))
    # 三个参数依次为 key 、value 、过期时间
    # 如果不设置第三个参数，浏览器关闭后键值对就消失
    resp.set_cookie('show_followed', '', max_age=24*3600)
    return resp


@main.route('/show-followed-blogs')
@login_required
def show_followed_blogs():
    '''展示关注的用户的博客'''
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=24*3600)
    return resp


@main.route('/register', methods=['POST', 'GET'])
def register():
    '''用户注册'''
    form = RegisterForm()
    if form.validate_on_submit():
        # 创建新用户并存入数据库，发送验证邮件
        form.create_user()
        flash('你已经注册成功，请登录', 'success')
        # 重定向到登录页面
        return redirect(url_for('.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['POST', 'GET'])
def login():
    '''用户登录'''
    if current_user.is_authenticated:
        flash('你已经处于登录状态。', 'info')
        return redirect(url_for('.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # 这个函数会根据请求对象设置 session ，其中包括：
        # _user_id 字段值为 user 的 id 属性值的字符串
        # _id 字段值为根据 IP 地址和浏览器的用户代理字符串生成的哈希值字符串
        # _remember 字段值为 form.remember_me.data 
        # 此外还会将请求对象的 user 属性值设置为 user
        # 这样 current_user 就指向了 user
        login_user(user, form.remember_me.data)
        flash('你已经登录成功，{}！'.format(user.name), 'success')
        # 如果当前用户未验证，登录后由此视图函数处理
        if not user.confirmed:
            return redirect(url_for('user.unconfirmed_user'))
        # 重定向时，URL 中会提供一个 next 参数，参数值为前一个页面的相对路由
        next_url = request.args.get('next')
        # 如果路由字符串以 / 开头，说明这是一个可信任的相对路由
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('.index'))
    return render_template('login.html', form=form)


# 用户注册之后，先在浏览器上登录，然后使用邮件确认账户的邮箱是否准确
# 新注册用户收到验证邮件后，通过点击邮件中提供的地址请求验证
@main.route('/confirm-user/<token>')
@login_required
def confirm_user(token):
    '''验证用户的邮箱'''
    if current_user.confirmed:
        flash('你的账号已经验证过了', 'info')
    elif current_user.confirm_user(token):
        flash('你的账号验证成功！', 'success')
    else:
        flash('你的账号验证失败，这是一个无效的链接', 'danger')
    return redirect(url_for('.index'))


@main.route('/logout')
def logout():
    '''退出登录'''
    logout_user()
    flash('你已经退出登录', 'info')
    return redirect(url_for('.index'))


@main.route('/search')
def search():
    form = BlogForm()
    show_followed = request.cookies.get('show_followed')
    search_str = request.args.get('search').strip()
    pagination = Blog.query.filter_by(id=0).paginate()

    if len(search_str) < 2:
        flash('搜索内容不能为空或少于两个字符。', 'warning')
        return render_template('index.html', form=form, blogs=[],
                show_followed=show_followed, pagination=pagination)
        return redirect(request.referrer)

    page = request.args.get('page', 1, type=int)
    pagination = Blog.query.whooshee_search(search_str).order_by(
        Blog.time_stamp.desc()).paginate(
            page,
            per_page = current_app.config['BLOGS_PER_PAGE'],
            error_out = False
        )
    blogs = pagination.items

    if pagination.total == 0:
        flash(f'没有搜索到任何包含 "{search_str}" 的结果。', 'warning')
    else:
        flash(f'搜索 "{search_str}" 结果如下。', 'success')

    return render_template('index.html', form=form, blogs=blogs,
            show_followed=show_followed, pagination=pagination)


# 之前的 errorhandler 装饰器只对 main 蓝图自身所属的视图函数有效
# 这里使用的是 app_errorhandler ，它使得该函数对全应用中的视图函数均有效

@main.app_errorhandler(403)
def forbidden(e):
    '''发起请求的用户权限不足'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403

@main.app_errorhandler(404)
def page_not_found(e):
    '''路由错误，不存在该页面'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def inter_server_error(e):
    '''服务器内部错误'''
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
