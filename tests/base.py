from flask import url_for
from functools import wraps

from weblog.app import create_app, User


PASSWORD = 'SYL123'


def login(func):
    '''为测试蓝图类的方法增加登录装饰器
    '''
    @wraps(func)
    def wrapper(*args, **kw):
        client = kw['client']
        user = kw.get('admin') or kw.get('user')
        password = 'admin' if user.name == 'Admin' else PASSWORD
        data = {'email': user.email, 'password': password}
        client.post(url_for('main.login'), data=data,
                headers={'Content-Type': 'multipart/form-data'})
        return func(*args, **kw)
    return wrapper
            


"""
def get_user_cookie():
    '''获取普通用户登录后的 Cookie
    '''

    app = create_app('test')

    with app.app_context():
        db = app.extensions['sqlalchemy'].db
        # 因为在创建测试数据的时候会向用户表中插入 10 条数据
        # 这里随便选择其中一条普通用户的数据，仅为得到响应的 Cookie 
        user = db.session.query(User).get(3)

        with app.test_client() as client:
            user_data = {'email': user.email, 'password': 'shiyanlou'}
            user_resp = client.post(
                    'http://localhost:5000/login', 
                    data=user_data,
                    headers={'Content-Type': 'multipart/form-data'})
            return user_resp.headers['Set-Cookie']


USER_COOKIE = get_user_cookie()

"""
