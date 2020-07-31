import os
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_pagedown import PageDown

from .configs import configs
from .models import whooshee, db, Role, User, Blog, Comment
from .api import api
from .main import main
from .user import user
from .blog import blog
from .admin import admin


blueprint_list = [api, main, user, blog, admin]


def register_blueprints(app):
    for bp in blueprint_list:
        app.register_blueprint(bp)


def register_extensions(app):
    bootstrap = Bootstrap(app)
    moment = Moment(app)
    whooshee.init_app(app)
    # 在应用初始化的时候，app 设置了一个 extensions 属性，属性值是空字典
    # 下面这步操作的结果之一是向 app.extensions 里添加一组键值对
    # 键是 'sqlalchemy' ，值是 flask_sqlalchemy.__init__._SQLAlchemyState 类的实例
    # 该实例的 db 属性值就是这个 db ，connectors 属性值是空字典
    db.init_app(app)
    Migrate(app, db)
    PageDown(app)
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def user_loader(id):
        # 只有主键才可以使用 query.get 方法查询
        # 此方法定义在 sqlalchemy.orm.query 模块中
        # 它会调用其它同模块中的方法查询 User 实例并返回
        # 参数 id 的数据类型为字符串
        # 我们使用的 MySQL 数据库容错率极高，会将其转换成 int 再查寻
        return User.query.get(id)

    # 未登录状态下，访问需要登录后才能访问的页面时，自动跳转到此路由
    login_manager.login_view = 'main.login'
    # 未登录状态访问需要登录的页面时给出的提示信息的内容和类型
    login_manager.login_message = '你需要登录之后才能访问该页面'
    login_manager.login_message_category = 'warning'


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(configs.get(config))
    register_extensions(app)    # 注册扩展
    register_blueprints(app)    # 注册蓝图

    return app
