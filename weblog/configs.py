import os


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asdfasdf'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BLOGS_PER_PAGE = 10
    USERS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10
    WHOOSHEE_MIN_STRING_LEN = 2
    # 如果所有需要登录的页面都免登录即可访问，就设置这个
    # LOGIN_DISABLED = True


class DevConfig(BaseConfig):
    '''开发模式配置类
    '''

    url = 'mysql://root:{}@localhost/weblog?charset=utf8'
    SQLALCHEMY_DATABASE_URI = url.format(os.environ.get('MYSQL_PWD'))

    # SERVER 和 PORT 是需要网上查的，各家的邮箱都不同
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 25
    # USERNAME 是发信人的邮箱，PASSWORD 是从邮箱那里获得的授权码
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')     
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class TestConfig(DevConfig):
    '''测试模式配置类
    '''

    WTF_CSRF_ENABLED = False


configs = {
    'dev': DevConfig,
    'test': TestConfig
}
