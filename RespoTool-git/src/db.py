# -*- coding: utf-8 -*-
# !python3

import datetime
from enum import auto

from peewee import CharField, Model, IntegerField, DateTimeField, BooleanField, ForeignKeyField
from playhouse.sqlite_ext import AutoIncrementField, SqliteExtDatabase

import utils

pragmas = {
    "journal_mode": "wal",
    "foreign_keys": 1
}

if __name__ == '__main__':
    database = SqliteExtDatabase("../db/respotool.sqlite", pragmas=pragmas)
else:
    database = SqliteExtDatabase("db/respotool.sqlite", pragmas=pragmas)


class EnumField(CharField):
    def __init__(self, choices, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        self.choices = choices
        self.max_length = 255

    def db_value(self, value):
        return value.value

    def python_value(self, value):
        value_type = type(list(self.choices)[0].value)
        return self.choices(value_type(value))


class BaseModel(Model):
    class Meta:
        database = database
        legacy_table_names = False


class Respomap(Model):
    name = CharField()


class Flag(BaseModel):
    id = AutoIncrementField()
    name = CharField()


class Report(BaseModel):
    id = AutoIncrementField()
    date = DateTimeField()
    author = CharField()
    code = CharField()
    flag = ForeignKeyField(Flag, backref="signalements")
    description = CharField()
    added_at = DateTimeField()
    added_by = CharField()




class Server(BaseModel):
    id = AutoIncrementField()
    discord_id = IntegerField(unique=True)
    name = CharField()
    prefix = CharField()
    joined_at = DateTimeField(default=datetime.datetime.now)
    feed_orga = IntegerField(null=True)
    feed_player = IntegerField(null=True)
    role_orga = IntegerField(null=True)
    role_player = IntegerField(null=True)
    active = BooleanField(default=True)


class Session(BaseModel):
    class SessionStatus(utils.AutoName):
        CREATED = auto()
        OPENED = auto()
        STARTED = auto()
        ENDED = auto()

    id = AutoIncrementField()
    server = ForeignKeyField(Server, backref="sessions")
    name = CharField()
    show_progress = BooleanField()
    status = EnumField(choices=SessionStatus)
    created_at = DateTimeField()
    opened_at = DateTimeField(null=True)
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)


class Team(BaseModel):
    id = AutoIncrementField()
    session = ForeignKeyField(Session, backref="teams")
    name = CharField()
    channel = IntegerField()
    role = IntegerField()
    created_at = DateTimeField()

    class Meta:
        indexes = (
            (("session", "name"), True),
        )


class Player(BaseModel):
    id = AutoIncrementField()
    discord_id = IntegerField(unique=True)
    name = CharField()


class Membership(BaseModel):
    id = AutoIncrementField()
    team = ForeignKeyField(Team, backref="players")
    player = ForeignKeyField(Player, backref="teams")
    joined_at = DateTimeField()
    leader = BooleanField()

    class Meta:
        indexes = (
            (("team", "player"), True),
        )


class Riddle(BaseModel):
    id = AutoIncrementField()
    session = ForeignKeyField(Session, backref="riddles")
    position = IntegerField(index=True)
    content = CharField()
    answer = CharField()
    title = CharField(null=True)
    avatar = CharField(null=True)

    class Meta:
        indexes = (
            (("session", "answer"), True),
        )


class Clue(BaseModel):
    id = AutoIncrementField()
    riddle = ForeignKeyField(Riddle, backref="clues")
    position = IntegerField(index=True)
    content = CharField()
    wait_time = IntegerField()


class Progress(BaseModel):
    id = AutoIncrementField()
    team = ForeignKeyField(Team, backref="progress")
    riddle = ForeignKeyField(Riddle, backref="progress")
    answered_by = ForeignKeyField(Player, null=True, backref="progress")
    started_at = DateTimeField()
    answered_at = DateTimeField(null=True)
    clues_used = IntegerField(default=0)


MODELS = [Server, Session, Team, Player, Membership, Riddle, Clue, Progress]


def create_tables():
    with database:
        database.drop_tables(MODELS)
        database.create_tables(MODELS)


if __name__ == '__main__':
    create_tables()
