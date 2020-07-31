# Weblog

Flask Web 应用「个人博客」。基于 Flask 1.0 编写，主要实现了以下功能：

- 注册、登录

- 邮箱验证

- 个人主页

- 更换邮箱

- 修改密码

- 编辑个人信息

- 编写博客

- 评论博客

- 关注他人

- 管理员管理评论

## 环境要求

操作系统：Ubuntu 14.04+

编程语言：Python 3.5+

开发框架：Flask 1.0+

数据库：MySQL 8.0+

## 部署流程

创建虚拟环境，在项目主目录下执行如下操作。

0、安装项目所需第三方库：

```bash
$ pip install --no-use-pep517 -r requirements.txt
```

需要将 `<b>{{field.label.text|safe}}</b>` 写入 flask_bootstrap.templates.bootstrap.wtf.html 文件的 RadioField 部分的 for 循环前面。

1、创建数据库：

```bash
$ mysql -uroot -e 'CREATE SCHEMA weblog'
```

2、配置环境变量：

```bash
$ export FLASK_DEBUG=1 FLASK_APP=manage.py
$ export MAIL_PASSWORD=asdfasdf  MAIL_USERNAME=xxxx@xxx.com
$ export MYSQL_PWD=xxxx ADMIN_EMAIL=xxxx@xxx.com
```

3、创建数据表：

```bash
$ flask db upgrade
```

4、生成测试数据：

```bash
$ python -m scripts.generate_fake_data
```

5、测试

```bash
$ pytest
```

6、启动应用，方式有多种：

```bash
$ flask run                                 # Flask 启动
$ gunicorn -c etc/gunicorn.py manage:app    # Gunicorn 启动
$ supervisord -c etc/supervisord.conf       # Supervisor 启动
```
