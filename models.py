"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.orm import validates

bcrypt = Bcrypt()
db = SQLAlchemy()

DEFAULT_IMAGE_URL = "/static/images/default-pic.png"
DEFAULT_HEADER_IMAGE_URL = "/static/images/warbler-hero.jpg"


class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default=DEFAULT_IMAGE_URL,
    )

    header_image_url = db.Column(
        db.Text,
        default=DEFAULT_HEADER_IMAGE_URL,
    )

    bio = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    location = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    authored_messages = db.relationship('Message', backref="author")

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id),
        backref="following"
    )

    # liked_messages secondary relationship to messages liked by this user

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url=DEFAULT_IMAGE_URL):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [
            user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [
            user for user in self.following if user == other_user]
        return len(found_user_list) == 1


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    __table_args__ = (
        CheckConstraint('char_length(text) > 0', name='text_min_length'),
    )

    @validates('text')
    def validate_some_string(self, key, text) -> str:
        if len(text) == 0:
            raise ValueError('some_string too short')
        return text

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    text = db.Column(
        db.String(140),
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # author = backref relationship to user that wrote message

    users_who_liked = db.relationship(
        'User',
        secondary='likes',
        backref='liked_messages')


class Like(db.Model):
    """Messages liked by Users"""

    __tablename__ = "likes"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='CASCADE'),
        nullable=False
    )

def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    app.app_context().push()
    db.app = app
    db.init_app(app)
