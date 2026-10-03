import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL が .env に設定されていません。"
        )

    return psycopg.connect(DATABASE_URL)


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            list_type TEXT NOT NULL,
            registered_name TEXT NOT NULL,
            lounge_id TEXT NOT NULL,
            reason TEXT,
            registered_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_player(
    list_type,
    registered_name,
    lounge_id,
    reason,
    registered_date
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO players
        (
            list_type,
            registered_name,
            lounge_id,
            reason,
            registered_date
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        list_type,
        registered_name,
        lounge_id,
        reason,
        registered_date
    ))

    conn.commit()
    conn.close()


def get_players(list_type):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            id,
            registered_name,
            lounge_id,
            reason,
            registered_date
        FROM players
        WHERE list_type = %s
        ORDER BY registered_name
    """, (list_type,)).fetchall()

    conn.close()

    return rows


def delete_player(player_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM players
        WHERE id = %s
    """, (player_id,))

    conn.commit()
    conn.close()


def update_player(
    player_id,
    registered_name,
    lounge_id,
    reason
):
    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET
            registered_name = %s,
            lounge_id = %s,
            reason = %s
        WHERE id = %s
    """, (
        registered_name,
        lounge_id,
        reason,
        player_id
    ))

    conn.commit()
    conn.close()