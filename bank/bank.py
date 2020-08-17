import json
import random
import asyncio
import discord
import sqlite3 as sqlite
from chowder import chowder

with open("chowder/chowder_config.json", "r") as read_file:
    config = json.load(read_file)

def create_db():
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    c.execute("""CREATE TABLE accounts
                (id text NOT NULL PRIMARY KEY, name text, balance integer)""")
    c.execute("""CREATE TABLE transactions
                (receiver_id text NOT NULL, amount integer, sender_id text,
                FOREIGN KEY(receiver_id) REFERENCES accounts(id))""")
    c.execute("INSERT INTO accounts VALUES ('1', 'BANK', 1)")
    conn.commit()
    conn.close()

def new_account(id, name, balance=0):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    c.execute(f"INSERT INTO accounts('id', 'name', 'balance') VALUES ('{id}', '{name}', 0)")
    conn.commit()
    conn.close()

"""Use this method to get the current balance of any user, based on id"""
def get_balance(id):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    query = f"SELECT balance FROM accounts WHERE id = {id}"
    bal = c.execute(query).fetchone()
    conn.close()
    if (bal == None):
        return None
    else:
        return int(bal[0])

"""Updates the balance of both sender and receiver and leaves a record in transactions."""
def transfer(send_id, rec_id, amount):
    if (rec_id == 1):
        #transfer to or from nothing
        update_balance(send_id, amount=amount)
    else:
        update_balance(send_id, -1*amount)
        update_balance(rec_id, amount)
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    c.execute(f"INSERT INTO TRANSACTIONS (receiver_id, amount, sender_id) \
                    VALUES ({rec_id}, {amount}, {send_id})")
    conn.commit()
    conn.close()
    return 1

"""Update user's balance by 'x' amount. 'x' can be positive or negative"""
def update_balance(send_id, amount, rec_id=None):
    conn = sqlite.connect(config["DATABASE"])
    c = conn.cursor()
    new_bal = get_balance(send_id) + amount
    c.execute(f"UPDATE accounts SET balance = {new_bal} where id = {send_id}")
    conn.commit()
    conn.close()
