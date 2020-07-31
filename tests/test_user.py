from flask import url_for

from weblog.models import db, User, Blog
from .base import PASSWORD, login


class TestUser:
    '''测试 user 蓝图下的视图函数
    '''

    def test_unconfirmd_user_and_resend_confirm_email(self, client):
        data = {'name': 'Test', 'email': '2734067994@qq.com',
                'password': PASSWORD, 'repeat_password': PASSWORD}
        client.post(url_for('main.register'), data=data,
                headers={'Content-Type': 'multipart/form-data'})
        data = {'email': '2734067994@qq.com', 'password': PASSWORD}
        resp = client.post(url_for('main.login'), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        assert b'You have not confirmed your account yet.' in resp.data
        resp = client.get(url_for('user.resend_confirm_email'))
        assert resp.status_code == 302
        assert b'<title>Redirecting...</title>' in resp.data
        user = User.query.filter_by(name='Test').first()
        db.session.delete(user)
        db.session.commit()

    @login
    def test_index(self, client, user):
        resp = client.get(url_for('user.index', name=user.name))
        assert resp.status_code == 200
        assert 'User - {}'.format(user.name) in resp.data.decode()


    @login
    def test_edit_profile_get(self, client, user):
        resp = client.get(url_for('user.edit_profile'),
                follow_redirects=True)
        assert resp.status_code == 200
        assert user.name in resp.data.decode()

    @login
    def test_change_password_get(self, client, user):
        resp = client.get(url_for('user.change_password'),
                follow_redirects=True)
        assert resp.status_code == 200
        assert b'<title>Change Password</title>' in resp.data

    @login
    def test_change_password_post(self, client, user):
        data = {'old_password': PASSWORD,
                'password': PASSWORD,
                'repeat_password': PASSWORD}
        resp = client.post(url_for('user.change_password'), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        assert 'User - {}'.format(user.name) in resp.data.decode()
        assert '你已经登录成功，{}！'.format(user.name) in resp.data.decode()

    def test_before_reset_password_get(self, client, user):
        resp = client.get(url_for('user.before_reset_password'))
        assert resp.status_code == 200
        assert b'<title>Reset Password</title>' in resp.data

    def test_before_reset_password_post(self, client, user):
        data = {'email': user.email}
        resp = client.post(url_for('user.before_reset_password'), data=data,
                headers={'Content-Type': 'multipart/form-data'})
        assert resp.status_code == 200
        flash_info = '已经发送一封带有确认指令的邮件到你的邮箱，请注意查收'
        assert flash_info in resp.data.decode()

    def test_reset_password_get(self, client, user):
        name = user.name
        token = user.generate_confirm_user_token()
        resp = client.get(
                url_for('user.reset_password', name=name, token=token))
        assert resp.status_code == 200
        flash_info = '邮箱已确认，请重置密码。'
        assert flash_info in resp.data.decode()

    def test_reset_password_post(self, client, user):
        data = {'password': PASSWORD, 'repeat_password': PASSWORD}
        name = user.name
        token = user.generate_confirm_user_token()
        url = url_for('user.reset_password', name=name, token=token)
        resp = client.post(url, data=data, follow_redirects=True,
                headers={'Content-Type': 'multipart/form-data'})
        assert resp.status_code == 200
        assert '密码已重置。' in resp.data.decode()
        
    @login
    def test_change_email_get(self, client, user):
        resp = client.get(url_for('user.change_email'))
        assert resp.status_code == 200
        assert b'<title>Change Email</title>' in resp.data

    @login
    def test_change_email_post_and_confirm_change_email(self, client, user):
        old_email = user.email
        new_email = 'x' + old_email
        data = {'email': new_email,
                'repeat_email': new_email,
                'password': PASSWORD}
        resp = client.post(url_for('user.change_email'), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        flash_info = '已经发送一封带有确认指令的邮件到你的邮箱，请注意查收'
        assert flash_info in resp.data.decode()
        user.email = old_email
        token = user.generate_confirm_user_token()
        db.session.add(user)
        db.session.commit()
        client.get(url_for('user.confirm_change_email', token=token))

    @login
    def test_edit_blog_get(self, client, user):
        blog = user.blogs[0]
        resp = client.get(url_for('user.edit_blog', id=blog.id))
        assert resp.status_code == 200
        assert blog.body in resp.data.decode()

    @login
    def test_edit_blog_get(self, client, user):
        blog = user.blogs[0]
        old_body = blog.body
        new_body = old_body + '\n OK.'
        data = {'body': new_body}
        resp = client.post(url_for('user.edit_blog', id=blog.id), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        assert new_body in resp.data.decode()
        blog.body = old_body
        db.session.add(blog)
        db.session.commit()

    @login
    def test_follow(self, client, user):
        name = User.query.get(4).name
        resp = client.get(url_for('user.follow', name=name))
        resp = client.get(url_for('user.unfollow', name=name),
                follow_redirects=True)
        assert resp.status_code == 200
        assert 'User - {}'.format(name) in resp.data.decode()
        assert '成功取关此用户' in resp.data.decode()
        resp = client.get(url_for('user.follow', name=name),
                follow_redirects=True)
        assert resp.status_code == 200
        assert 'User - {}'.format(name) in resp.data.decode()
        assert '成功关注此用户' in resp.data.decode()
