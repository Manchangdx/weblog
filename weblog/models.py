from flask import current_app, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_whooshee import Whooshee
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature
from datetime import datetime
from markdown import markdown
import enum
import hashlib
import bleach


whooshee = Whooshee()
db = SQLAlchemy()


class Permission:
    '''权限类'''

    FOLLOW = 1              # 关注他人
    WRITE = 2               # 写博客
    COMMENT = 4             # 评论博客
    MODERATE = 8            # 审核评论
    ADMINISTER = 2 ** 7     # 管理网站


class Role(db.Model):
    '''角色映射类'''

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    # 创建角色数据表之后添加几个角色，相对其它数据表，角色是比较稳定的
    # 这个方法需要单独手动执行，这是一个静态方法，亦可写在类的外部
    @staticmethod
    def insert_roles():
        # 设置三个角色：普通用户（默认角色）、协管员、管理员
        # 字典的 key 是角色的 name 属性值，value 是各个权限之和
        roles = {
            'User': Permission.FOLLOW | Permission.COMMENT | Permission.WRITE,
            'Moderator': Permission.FOLLOW | Permission.COMMENT |
                    Permission.WRITE | Permission.MODERATE,
            'Administrator': Permission.FOLLOW | Permission.COMMENT |
                    Permission.WRITE | Permission.MODERATE | Permission.ADMINISTER
        }
        # 用户的默认角色的 name 属性值
        default_role_name = 'User'
        for r, v in roles.items():
            # 查询角色数据表中是否有此数据，如果没有就新建一个实例
            # 如果有的话，or 后面的代码不会执行
            role = Role.query.filter_by(name=r).first() or Role(name=r)
            role.permissions = v
            # 如果用户的 name 属性值为 'User' ，则其 default 属性值为 True
            # 否则 default 属性值为 False
            role.default = True if role.name == default_role_name else False
            db.session.add(role)
        db.session.commit()


class Gender(enum.Enum):
    '''性别类，Roel 类中的 gender 属性要用到此类'''

    MALE = '男性'
    FEMALE = '女性'


class Follow(db.Model):
    '''存储用户关注信息的双主键映射类'''

    __tablename__ = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
            primary_key=True)   # 关注者 ID 
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), 
            primary_key=True)   # 被关注者 ID
    time_stamp = db.Column(db.DateTime, default=datetime.now)


# UserMixin 是在 flask_login.mixins 模块中定义的类
# 该类为 User 类的实例增加了 is_authenticated 、is_active 、is_anonymous 等属性
# 以及 get_id 等方法
#
# is_authenticated 为 True
# is_anonymous 与之正相反
# is_active 属性默认值为 True ，可以用来封禁用户 
# 
# User 类的实例的 get_id 的返回值为 str(self.id) ，即 id 属性值的字符串
class User(db.Model, UserMixin):
    '''用户映射类'''

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64), unique=True, index=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum(Gender))
    phone_number = db.Column(db.String(32), unique=True)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    _password = db.Column('password', db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))
    avatar_hash = db.Column(db.String(128))
    # 没有参数的方法，例如 db.DateTime、datetime.utcnow 写不写括号均可
    created_at = db.Column(db.DateTime, default=datetime.now())
    # 最近操作时间，「操作」包括登录请求和登录后的任何请求
    last_seen = db.Column(db.DateTime, default=datetime.now)
    # 是否已通过邮箱验证，注册后验证前该值为 False
    confirmed = db.Column(db.Boolean, default=False)
    # 此属性为「我关注了谁」，属性值为查询对象，里面是 Follow 类的实例
    # 参数 foreign_keys 意为查询 User.id 值等于 Follow.follower_id 的数据
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
            # 反向查询接口 follower 定义的是 Follow 实例的属性，创建实例用得上
            # 该属性指向关注关系中的「关注者」，对应 Follow().follower_id 属性
            # User 实例使用 followers 属性获得 Follow 实例的时候
            # 这些 Follow 实例顺便使用 follower 属性获得对应的 User 实例
            # 也就是「关注者」
            # 因为 lazy='joined' 模式可以实现立即从联结查询中加载相关对象
            # 例如，如果某个用户关注了 100 个用户
            # 调用 user.followed.all() 后会返回一个列表
            # 其中包含 100 个 Follow 实例
            # 每一个实例的 follower 和 followed 回引属性都指向相应的用户
            # 设定为 lazy='joined' 模式，即可在一次数据库查询中完成这些操作
            # 如果把 lazy 设为默认值 select
            # 那么首次访问 follower 和 followed 属性时才会加载对应的用户
            # 而且每个属性都需要一个单独的查询
            # 这就意味着获取全部被关注用户时需要增加 100 次额外的数据库查询操作
            backref=db.backref('follower', lazy='joined'),
            # cascade 表示如果该 User 对象被删除，顺便删除全部相关的 Follow 对象
            # cascade 参数的值是一组由逗号分隔的层叠选项
            # all 表示启用所有默认层叠选项，delete-orphan 表示删除所有孤儿记录
            # lazy='dynamic' 表示仅获得查询结果，不把数据从数据库加载到内存
            cascade='all, delete-orphan', lazy='dynamic')
    # 此属性可获得数据库中「谁关注了我」的查询结果，它是 Follow 实例的列表
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
            backref=db.backref('followed', lazy='joined'), 
            cascade='all, delete-orphan', lazy='dynamic')

    def __init__(self, **kw):
        '''初始化实例，给用户增加默认角色'''
        # 先调用父类的初始化方法
        super().__init__(**kw)
        # 给实例的 role 属性赋值
        self.role = kw.get('role') or Role.query.filter_by(default=True).first()

    def is_following(self, user):
        '''判断 self 用户是否关注了 user 用户'''
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        '''判断 self 用户是否被 user 用户关注'''
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        '''关注 user 用户，即向 follows 数据表中添加一条数据'''
        if not self.is_following(user):
            f = Follow(follower_id=self.id, followed_id=user.id)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        '''取关 user 用户，即移除 follows 数据表中的一条数据'''
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    @property
    def followed_posts(self):
        '''我关注的所有用户的全部博客'''
        # query.join 为联表查询或者联结查询
        # 查询 Follow 实例中被关注者 ID 等于 Post.author_id 的 Post 实例
        # Follow 实例指的是哪些呢？关注者 ID 等于 self.id 的
        return Blog.query.join(Follow, Follow.followed_id==Blog.author_id
                ).filter(Follow.follower_id==self.id)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        self._password = generate_password_hash(pwd)

    def verify_password(self, pwd):
        '''验证用户密码'''
        return check_password_hash(self._password, pwd)

    def ping(self):
        '''用户登录时，自动执行此方法刷新最近操作时间'''
        self.last_seen = datetime.now()
        db.session.add(self)
        db.session.commit()

    @property
    def serializer(self, expires_in=3600):
        '''创建令牌生成器'''
        # Serializer 类的实例即为令牌生成器
        # 创建该类实例，须提供一个字符串和一个过期时间
        # 过期时间指的是令牌生成器生成的令牌的有效期
        # 令牌也叫加密签名，是一串复杂的字符串
        # 令牌生成器的 dumps 方法的参数是字典，返回值是令牌
        # 将令牌作为令牌生成器的 loads 方法的参数可以获得字典
        return Serializer(current_app.config['SECRET_KEY'], expires_in)

    def generate_confirm_user_token(self):
        '''生成确认用户的令牌并返回'''
        return self.serializer.dumps({'confirm_user': self.id})

    def confirm_user(self, token):
        '''验证确认用户的令牌'''
        try:
            data = self.serializer.loads(token)
        except BadSignature:
            return False
        if data.get('confirm_user') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def generate_confirm_auth_token(self):
        '''生成验证 api 相关请求的令牌并返回'''
        return self.serializer.dumps({'confirm_user': self.id})

    def verify_api_token(self, token):
        '''验证 api 相关请求中携带的令牌'''
        try:
            data = self.serializer.loads(token)
        except BadSignature:
            return None
        return self.__class__.query.get(data['id'])

    @property
    def is_administrator(self):
        '''判断用户是不是管理员'''
        return self.role.permissions & Permission.ADMINISTER

    @property
    def is_moderator(self):
        '''判断用户是不是协管员'''
        return self.role.permissions & Permission.MODERATE

    def has_permission(self, permission):
        '''判断用户是否有某种权限'''
        return self.role.permissions & permission

    def gravatar(self, size=256, default='identicon', rating='g'):
        '''创建 Gravatar URL 的方法，其返回值就是一个头像图片的地址'''
        # 参数：size 图片大小，default 创建默认图片的方法，算是固定写法
        # rating 图片级别：
        # G 大众级，所有人可以看
        # PG 大众级，所有人可以看，建议儿童在父母陪伴下观看（非强制）
        # R 限制级，17 岁以下须在父母陪伴下观看（强制）
        url = 'https://cn.gravatar.com/avatar'
        # 这步生成 MD5 散列值，这是 CPU 密集型操作
        hash = hashlib.md5(self.email.encode()).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url=url, hash=hash, size=size, default=default, rating=rating)

    @property
    def followed_blogs(self):
        return Blog.query.join(Follow, Follow.followed_id == Blog.author_id)\
            .filter(Follow.follower_id == self.id)

    def to_json(self):
        '''将 User 实例转换成字典对象并返回'''
        result = {
                'url': url_for('api.get_user', id=self.id),
                'name': self.name,
                'created_at': self.created_at,
                'last_seen': self.last_seen,
                'blogs_url': url_for('api.get_user_blogs', id=self.id),
                'blogs_count': self.blogs.count()
        }
        return result
        

    def __repr__(self):
        return '<User: {}>'.format(self.name)


@whooshee.register_model('body')
class Blog(db.Model):
    '''博客映射类'''

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.Integer, 
            db.ForeignKey('user.id', ondelete='CASCADE'))
    author = db.relationship('User', backref=db.backref('blogs', lazy='dynamic',
            cascade='all, delete-orphan'))

    # 该方法为静态方法，可以写在类外部，Blog().body 有变化时自动运行
    # target 为 Blog 类的实例，value 为实例的 body 属性值
    # old_value 为数据库中 Blog.body_html 的值，initiator 是一个事件对象
    # 后两个参数为事件监听程序调用此函数时固定要传入的值，在函数内部用不到
    @staticmethod
    def on_changed_body(target, value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        # bleach.linkify 方法将 <a> 标签转换为链接
        # bleach.clean 方法清洗 HTML 数据
        target.body_html = bleach.linkify(bleach.clean(
                # markdown 方法将 Markdown 文本转换为 HTML 
                markdown(value, output_format='html'),
                tags=allowed_tags, 
                strip=True
        ))

    def to_json(self):
        '''将 Blog 实例转换成字典对象并返回'''
        result = {
                'url': url_for('api.get_blog', id=self.id),
                'body': self.body,
                'body_html': self.body_html,
                'time_stamp': self.time_stamp,
                'author_url': url_for('api.get_user', id=self.author_id),
                'comments_url': url_for('api.get_blog_comments', id=self.id),
                'comments_count': self.comments.count()
        }
        return result

    @classmethod
    def from_json(cls, json_data):
        '''利用字典对象创建 Blog 类的实例并返回'''
        body = json_data.get('body')
        if not body:
            raise ValidationError('Blog does not have body.')
        return cls(body=body)


# db.event.listen 设置 SQLAlchemy 的 'set' 事件监听程序
# 当 Blog.body 的值发生变化，该事件监听程序会自动运行
# 高效地修改 Blog.body_html 字段的值并存入数据表
db.event.listen(Blog.body, 'set', Blog.on_changed_body)


class Comment(db.Model):
    '''评论映射类'''

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    time_stamp = db.Column(db.DateTime, index=True, default=datetime.now)
    disable = db.Column(db.Boolean)
    author_id = db.Column(db.Integer,
            db.ForeignKey('user.id', ondelete='CASCADE'))
    author = db.relationship('User', backref=db.backref('comments',
            lazy='dynamic', cascade='all, delete-orphan'))
    blog_id = db.Column(db.Integer,
            db.ForeignKey('blog.id', ondelete='CASCADE'))
    blog = db.relationship('Blog', backref=db.backref('comments',
            lazy='dynamic', cascade='all, delete-orphan'))

    def to_json(self):
        '''将 Comment 实例转换成字典对象并返回'''
        result = {
                'url': url_for('api.get_comment', id=self.id),
                'body': self.body,
                'blog_url': url_for('api.get_blog', id=self.blog_id),
                'time_stamp': self.time_stamp,
                'author_url': url_for('api.get_user', id=self.author_id)
        }
        return result

    @classmethod
    def from_json(cls, json_data):
        '''利用字典对象创建 Comment 类的实例并返回'''
        body = json_data.get('body')
        if not body:
            raise ValidationError('Comment does not have body.')
        return cls(body=body)
