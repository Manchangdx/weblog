from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from flask_login import login_user

from . import api
from .errors import unauthorized, forbidden
from ..models import db, User


# 创建 flask_httpauth.HTTPBasicAuth 类（基础验证类)的实例
basic_auth = HTTPBasicAuth()


@basic_auth.verify_password
# basic_auth.login_required 装饰器会调用这个函数验证请求中的用户信息
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User().verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter(
        db.or_(
            User.name==email_or_token.lower(),
            User.email==email_or_token.lower()
        )
    ).first()
    #print('【weblog.api.authentication.verify_password】user:', user)
    if not user:
        return False
    # g 是一个应用上下文对象，但它的生存周期是一个请求的处理过程
    g.current_user = user
    g.token_used = False
    if user.verify_password(password):
        login_user(user)
        return True


@basic_auth.error_handler
def auth_error():
    return unauthorized('invalid credentials')


# 服务器收到 api 蓝图相关请求时，首先执行被此装饰器装饰的函数
@api.before_request     
# 浏览器发出的请求经过 Werkzeug 处理后，将数据存储在一个字典对象里
# 这个字典对象就是 flask.Flask.wsgi_app 的 environ 参数
# 如果字典对象里有 HTTP_AUTHORIZATION 字段
# 该字段值通常是类似这样的字符串 'Basic YWJjOmFiY2Rl'
# 空格前面的 Basic 是验证类型
# 后面是由 base64 加密的字段，可以轻松解密获得用户名和密码
# 在 Flask 框架处理请求过程中
# 解密得到的用户名和密码被存储在请求对象 request 的 authorization 属性中
# 该属性值是 werkzeug.datastructures.Authorization 的实例，它是类字典对象
# 这个类字典对象有两个属性 username 和 password 
# 分别对应请求头中 HTTP_AUTHORIZATION 字段携带的用户名和密码信息
# 还有一个 type 属性，对应的是验证类型，basic_auth 的验证类型就是 'Basic'
#
# 下面这个装饰器的作用是获取请求对象 request 的 authentication 属性值
# 然后验证用户名和密码，验证通过后调用被装饰的函数
@basic_auth.login_required
def before_request():
    if not g.current_user.confirmed:
        return forbidden('unconfirmed account')
