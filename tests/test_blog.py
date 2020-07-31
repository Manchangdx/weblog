from flask import url_for

from .base import login
from weblog.models import db, Comment


class TestBlog:
    '''测试 blog 蓝图下的视图函数
    '''

    def test_index_get(self, client, blog):
        resp = client.get(url_for('blog.index', id=blog.id))
        assert resp.status_code == 200
        assert blog.body in resp.data.decode()

    @login
    def test_index_post(self, client, user, blog, comment):
        data = {'body': comment.body}
        resp = client.post(url_for('blog.index', id=blog.id), data=data,
                headers={'Content-Type': 'multipart/form-data'},
                follow_redirects=True)
        assert resp.status_code == 200
        assert comment.body in resp.data.decode()
        for comment in Comment.query.filter_by(
                author_id=user.id, blog_id=blog.id):
            print('comment:', comment)
            db.session.delete(comment)
        db.session().commit()
