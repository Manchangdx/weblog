from flask import url_for

from .base import login


class TestAdmin:
    '''测试 admin 蓝图下的视图函数
    '''

    @login
    def test_admin_edit_profile(self, client, admin, user):
        resp = client.get(url_for('admin.admin_edit_profile', id=user.id))
        assert resp.status_code == 200
        assert user.name in resp.data.decode()

    @login
    def test_moderate_comments(self, client, admin, comment):
        resp = client.get(url_for('admin.moderate_comments'))
        assert resp.status_code == 200
        assert b'<title>Moderate Comments</title>' in resp.data

    @login
    def test_disable_comment(self, client, admin, comment):
        resp = client.get(url_for('admin.disable_comment', id=comment.id), 
                follow_redirects=True)
        assert resp.status_code == 200
        assert comment.disable == 1
        assert b'<title>Moderate Comments</title>' in resp.data
    
    @login
    def test_enable_comment(self, client, admin, comment):
        resp = client.get(url_for('admin.enable_comment', id=comment.id), 
                follow_redirects=True)
        assert resp.status_code == 200
        assert comment.disable == 0
        assert b'<title>Moderate Comments</title>' in resp.data
