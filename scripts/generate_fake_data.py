'''
终端命令行执行
python3 -m scripts.generate_fake_data
生成测试数据，该脚本可多次执行
'''

import os
from faker import Faker
from random import randint
from manage import app

# 启动应用的上下文环境
app.app_context().push()

from weblog.models import db, Role, User, Blog


Role.insert_roles()                                         # 创建角色
default_role = Role.query.filter_by(default=True).first()   # 默认角色
fake = Faker('zh-cn')                                       # 创建虚拟数据的工具



def iter_users():
    '''创建 10 个测试用户和 1 个管理员用户'''
    for i in range(10):
        user = User(
                name = fake.name(),
                age = randint(11, 66),
                gender = ['MALE', 'FEMALE'][randint(0, 1)],
                location = fake.city_name(),
                email = fake.email(),
                phone_number = fake.phone_number(),
                role = default_role,
                password = 'SYL123',
                about_me = fake.sentence(nb_words=15),
                confirmed = 1
        )
        user.avatar_hash = user.gravatar()
        yield user

    # 创建 1 个管理员用户
    if not User.query.filter_by(name='Admin').first():
        user = User(name='Admin', age=33, gender='MALE', 
                location=fake.city_name(),
                email=os.environ.get('ADMIN_EMAIL'), 
                phone_number=fake.phone_number(),
                role=Role.query.filter_by(name='Administrator').first(),
                password='admin',
                about_me='沉舟侧畔千帆过，病树前头万木春。',
                confirmed=1)
        yield user


def iter_blogs():
    '''为每个虚拟用户创建数个虚拟博客'''
    for user in iter_users():
        db.session.add(user)
        for i in range(1, 6):
            blog = Blog(
                    author = user,
                    time_stamp = fake.date_time_this_year()
            )
            blog.body = fake.text(max_nb_chars=222)
            yield blog


def run():
    for blog in iter_blogs():
        db.session.add(blog)
    db.session.commit()
    print('OK')


if __name__ == '__main__':
    run()
