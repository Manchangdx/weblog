import json
import re
from flask import url_for
from flask_login import login_user, current_user
from base64 import b64encode

from weblog.models import db, User, Role, Blog, Comment
from .base import PASSWORD, login


class TestApi:
    '''测试 api 蓝图下的视图函数
    '''

    @property
    def get_api_headers(self):
        user = User.query.get(1)
        s = b64encode(f'{user.name}:{PASSWORD}'.encode()).decode()
        return {
            'Authorization': f'Basic {s}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_get_user(self, client, user):
        resp = client.get(
                url_for('api.get_user', id=user.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'blogs_count' in d
        assert 'url' in d

    def test_get_user_blogs(self, client, user):
        resp = client.get(
                url_for('api.get_user_blogs', id=user.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'author_url' in d
        assert 'body' in d

    def test_get_user_followed_blogs(self, client, user):
        resp = client.get(
                url_for('api.get_user_followed_blogs', id=user.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'blogs' in d

    def test_get_blogs(self, client):
        resp = client.get(
                url_for('api.get_blogs'),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'blogs' in d
        assert 'author_url' in d
        assert 'count' in d

    def test_get_blog(self, client, blog):
        resp = client.get(
                url_for('api.get_blog', id=blog.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'author_url' in d
        assert 'body' in d
        assert 'comments_count' in d

    def test_new_blog(self, client):
        body = '''HOST 变量是空白的，这是对 bind 方法的标识，
                表示它可以使用任何可用的地址。'''
        resp = client.post(
                url_for('api.new_blog'), 
                data=json.dumps({'body': body}),
                headers=self.get_api_headers
        )
        assert resp.status_code == 201
        d = json.loads(resp.data.decode())
        id = d['url'].split('/')[-1]
        blog = Blog.query.get(id)
        assert blog.body == body
        db.session.delete(blog)
        db.session.commit()

    def test_edit_blog(self, client, user):
        blog = user.blogs[0]
        old_body = blog.body
        new_body = '''HOST 变量是空白的，这是对 bind 方法的标识，
                表示它可以使用任何可用的地址。'''
        resp = client.put(
                url_for('api.edit_blog', id=blog.id), 
                data=json.dumps({'body': new_body}),
                headers=self.get_api_headers
        )
        d = json.loads(resp.data.decode())
        blog.body = old_body
        db.session.add(blog)
        db.session.commit()
        assert resp.status_code == 200
        assert url_for('api.get_user', id=user.id) == d['author_url']

    def test_get_comments(self, client):
        resp = client.get(
                url_for('api.get_comments'),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = resp.data.decode()
        assert 'comments' in d
        assert 'count' in d

    def test_get_comment(self, client, comment):
        resp = client.get(
                url_for('api.get_comment', id=comment.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = json.loads(resp.data.decode())
        assert comment.body == d['body']

    def test_get_blog_comments(self, client, comment):
        resp = client.get(
                url_for('api.get_blog_comments', id=comment.blog.id),
                headers=self.get_api_headers
        )
        assert resp.status_code == 200
        d = json.loads(resp.data.decode())
        assert 'count' in d
        assert isinstance(d['comments'], list) is True

    def test_add_blog_comment(self, client, user):
        blog = user.blogs[0]
        body = 'HOST 变量是空白的，这是对 bind 方法的标识'
        resp = client.post(
                url_for('api.add_blog_comment', id=blog.id),
                data=json.dumps({'body': body}),
                headers=self.get_api_headers
        )
        assert resp.status_code == 201
        d = json.loads(resp.data.decode())
        assert body == d['body']
        comment = Comment.query.get(d['url'].split('/')[-1])
        db.session.delete(comment)
        db.session.commit()
