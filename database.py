import sqlite3


DB_FILE = "blackwhite.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        VALUES (?, ?, ?, ?, ?)
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
        WHERE list_type = ?
        ORDER BY registered_name COLLATE NOCASE
    """, (list_type,)).fetchall()

    conn.close()

    return rows


def delete_player(player_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM players
        WHERE id = ?
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
            registered_name = ?,
            lounge_id = ?,
            reason = ?
        WHERE id = ?
    """, (
        registered_name,
        lounge_id,
        reason,
        player_id
    ))

    conn.commit()
    conn.close()