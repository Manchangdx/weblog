from flask import url_for

from weblog.models import db, User
from .base import PASSWORD, login


class TestMain:
    '''测试 main 蓝图下的视图函数
    '''

    def test_register_get(self, client):
        resp = client.get(url_for('main.register'))
        assert resp.status_code == 200
        assert b'<title>Register</title>' in resp.data


    def test_register_post(self, client):
        data = {'name': 'Test', 'email': '2734067994@qq.com', 
                'password': PASSWORD, 'repeat_password': PASSWORD}
        resp = client.post(url_for('main.register'), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        db.session.delete(User.query.filter_by(name='Test').first())
        db.session.commit()
        assert resp.status_code == 200
        assert b'<title>Login</title>' in resp.data

    def test_login_get(self, client):
        resp = client.get(url_for('main.login'))
        assert resp.status_code == 200
        assert b'<title>Login</title>' in resp.data

    def test_login_post(self, client, user):
        data = {'email': user.email, 'password': PASSWORD}
        resp = client.post(url_for('main.login'), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        assert b'<title>Weblog</title>' in resp.data

        self.cookie = resp.headers['Set-Cookie']

    def test_index(self, client):
        resp = client.get(url_for('main.index'))
        assert resp.status_code == 200
        assert '记录你的想法'.encode() in resp.data

    @login
    def test_index_after_login(self, client, user):
        resp1 = client.get(url_for('main.show_followed_blogs'), 
                follow_redirects=True)
        assert resp1.status_code == 200
        assert '查看全部'.encode() in resp1.data
        resp2 = client.get(url_for('main.show_all_blogs'),
                follow_redirects=True)
        assert resp2.status_code == 200
        assert '查看全部'.encode() in resp2.data

    @login
    def test_confirm_user(self, client, user):
        token = user.generate_confirm_user_token()
        resp = client.get(url_for('main.confirm_user', token=token),
                follow_redirects=True)
        assert resp.status_code == 200
        assert b'<title>Weblog</title>' in resp.data

    @login
    def test_logout(self, client, user):
        resp = client.get(url_for('main.logout'), follow_redirects=True)
        assert resp.status_code == 200
        print(resp.data.decode())
        assert '记录你的想法'.encode() in resp.data
        assert '查看全部'.encode() not in resp.data
