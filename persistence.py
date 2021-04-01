
import os
import ssl

from dotenv import load_dotenv
from gino import Gino

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

db = Gino()


class Rating(db.Model):
    __tablename__ = "cgr"
    id = db.Column(db.BigInteger)
    game = db.Column(db.String)
    rating = db.Column(db.Integer)
    games_played = db.Column(db.Integer)
    _pk = db.PrimaryKeyConstraint("id", "game")


class Coin(db.Model):
    __tablename__ = "coin"
    id = db.Column(db.BigInteger, primary_key=True)
    balance = db.Column(db.Numeric)


class Items(db.Model):
    __tablename__ = "items"
    id = db.Column(db.BigInteger)
    item = db.Column(db.String)
    _pk = db.PrimaryKeyConstraint("id", "item")


async def initialize():
    ctx = ssl.create_default_context(cafile="")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    await db.set_bind(DATABASE_URL, echo=True, ssl=ctx)
    await db.gino.create_all()
