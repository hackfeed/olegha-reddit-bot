import mongoengine as me
from datetime import datetime


class Post(me.Document):
    """
        Модель для поста в базе данных.
    """

    title = me.StringField(required=True, default="", max_length=500)
    topic = me.StringField(required=True, default="", max_length=25)
    description = me.StringField(required=True, default="", max_length=400)
    link = me.URLField(required=True)
    author = me.StringField(required=True, default="Anonymous", max_length=30)
    # date = me.DateTimeField(required=True, default=datetime.utcnow)


class User(me.Document):
    """
        Модель пользователя в базе данных.
    """

    user_id = me.IntField(required=True, default=-1)
    bookmarks = me.ListField(me.StringField(), default=[])
