from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
import random

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    api_key = db.Column(db.Text(20), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    # device = db.relationship('Device', backref="user")
    # main_sensor = db.relationship('MainSensor', backref="user")

    def __repr__(self) -> str:
        return 'User>>> {self.username}'

    def generate_api_key(self):
        characters = string.digits + string.ascii_letters
        picked_chars = ''.join(random.choices(characters, k=16))

        api = self.query.filter_by(api_key=picked_chars).first()

        if api:
            self.generate_api_key()
        else:
            return picked_chars

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.api_key = self.generate_api_key()
        self.status = 1


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Text, nullable=True)
    device_name = db.Column(db.Text, nullable=False)
    device_status = db.Column(db.Boolean, nullable=True, default=True)
    device_switch = db.Column(db.Boolean, nullable=True, default=True)
    status = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    # device = db.relationship('Device', backref="user")

    def __repr__(self) -> str:
        return 'Device>>> {self.id}'


class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(20))
    voltage = db.Column(db.Float, nullable=True)
    ampere = db.Column(db.Float, nullable=True)
    kw_sec = db.Column(db.Float(10, 10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return 'SensorDate>>> {self.id}'


class MainSensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Text, nullable=True)
    voltage = db.Column(db.Text, nullable=True)
    ampere = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, onupdate=datetime.now())

    def __repr__(self) -> str:
        return 'MainSensor>>> {self.id}'


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return 'Admin>>> {self.id}'

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), unique=True, nullable=False)