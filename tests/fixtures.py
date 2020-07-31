import pytest
from flask import url_for

from weblog.app import create_app, db, User, Blog, Comment


@pytest.fixture
def app():
    '''应用对象'''

    app = create_app('test')
    return app


@pytest.yield_fixture
def client(app):
    '''客户端'''

    # 这里使用 with 关键字是为了保证测试结束后清除 client
    with app.test_client() as client:
        yield client


@pytest.fixture
def user(app):
    '''普通用户'''

    return User.query.get(1)


@pytest.fixture
def admin(app):
    '''管理员用户'''

    return User.query.filter_by(name='Admin').first()

@pytest.fixture
def blog(app):
    '''ID 为 1 的博客实例'''

    return Blog.query.get(1)


@pytest.fixture
def comment(app, blog):
    '''ID 为 1 的评论实例'''
    author = blog.author
    comment = Comment.query.filter_by(
            author_id=author.id, blog_id=blog.id).first()
    if comment:
        return comment
    comment = Comment(body='今天天气不错', author=author, blog=blog)
    db.session.add(comment)
    db.session.commit()
    return comment
