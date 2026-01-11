import sqlite3
import os


class ChessDatabase:
    def __init__(self, db_name="chess_repertoire.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS repertoires (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, color TEXT CHECK(color IN ('White', 'Black')) NOT NULL)")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS positions (id INTEGER PRIMARY KEY AUTOINCREMENT, fen TEXT UNIQUE NOT NULL)")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS moves (id INTEGER PRIMARY KEY AUTOINCREMENT, repertoire_id INTEGER, from_position_id INTEGER, to_position_id INTEGER, uci TEXT NOT NULL, comment TEXT, FOREIGN KEY(repertoire_id) REFERENCES repertoires(id), FOREIGN KEY(from_position_id) REFERENCES positions(id), FOREIGN KEY(to_position_id) REFERENCES positions(id))")
        self.conn.commit()

    def get_or_create_position(self, fen):
        fen_parts = fen.split(" ")
        clean_fen = " ".join(fen_parts[:4])
        self.cursor.execute("SELECT id FROM positions WHERE fen = ?", (clean_fen,))
        row = self.cursor.fetchone()
        if row: return row['id']

        self.cursor.execute("INSERT INTO positions (fen) VALUES (?)", (clean_fen,))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_repertoire(self, name, color):
        self.cursor.execute("INSERT INTO repertoires (name, color) VALUES (?, ?)", (name, color))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete_repertoire(self, repertoire_id):
        self.cursor.execute("DELETE FROM moves WHERE repertoire_id = ?", (repertoire_id,))
        self.cursor.execute("DELETE FROM repertoires WHERE id = ?", (repertoire_id,))
        self.conn.commit()

    def get_repertoires(self):
        self.cursor.execute("SELECT * FROM repertoires")
        return self.cursor.fetchall()

    def get_repertoire_color(self, repertoire_id):
        self.cursor.execute("SELECT color FROM repertoires WHERE id = ?", (repertoire_id,))
        row = self.cursor.fetchone()
        return row['color'] if row else 'White'

    def delete_move(self, move_id):
        self.cursor.execute("SELECT to_position_id, repertoire_id FROM moves WHERE id = ?", (move_id,))
        row = self.cursor.fetchone()
        if not row: return
        to_pos_id = row['to_position_id']
        rep_id = row['repertoire_id']
        self.cursor.execute("SELECT id FROM moves WHERE repertoire_id = ? AND from_position_id = ?",
                            (rep_id, to_pos_id))
        children = self.cursor.fetchall()
        for child in children:
            self.delete_move(child['id'])
        self.cursor.execute("DELETE FROM moves WHERE id = ?", (move_id,))
        self.conn.commit()

    def get_move_by_id(self, move_id):
        self.cursor.execute("SELECT p.fen FROM moves m JOIN positions p ON m.to_position_id = p.id WHERE m.id = ?",
                            (move_id,))
        row = self.cursor.fetchone()
        return row['fen'] if row else None

    # --- NEW HELPER FOR SMART BACK BUTTON ---
    def get_parent_fen(self, repertoire_id, current_fen):
        """Finds the position that occurred immediately before the current one."""
        clean_fen = " ".join(current_fen.split(" ")[:4])
        self.cursor.execute("SELECT id FROM positions WHERE fen = ?", (clean_fen,))
        row = self.cursor.fetchone()
        if not row: return None

        current_pos_id = row['id']

        # Find a move in this repertoire that LEADS to this position
        self.cursor.execute("""
                            SELECT p.fen
                            FROM moves m
                                     JOIN positions p ON m.from_position_id = p.id
                            WHERE m.repertoire_id = ?
                              AND m.to_position_id = ? LIMIT 1
                            """, (repertoire_id, current_pos_id))

        parent = self.cursor.fetchone()
        return parent['fen'] if parent else None

    # ----------------------------------------

    def add_move(self, repertoire_id, from_fen, to_fen, uci, comment=""):
        from_id = self.get_or_create_position(from_fen)
        to_id = self.get_or_create_position(to_fen)
        self.cursor.execute("SELECT id FROM moves WHERE repertoire_id=? AND from_position_id=? AND uci=?",
                            (repertoire_id, from_id, uci))
        existing = self.cursor.fetchone()
        if existing:
            if comment:
                self.cursor.execute("UPDATE moves SET comment=? WHERE id=?", (comment, existing['id']))
                self.conn.commit()
            return existing['id']
        else:
            self.cursor.execute(
                "INSERT INTO moves (repertoire_id, from_position_id, to_position_id, uci, comment) VALUES (?, ?, ?, ?, ?)",
                (repertoire_id, from_id, to_id, uci, comment))
            self.conn.commit()
            return self.cursor.lastrowid

    def get_moves_from_fen(self, repertoire_id, fen):
        clean_fen = " ".join(fen.split(" ")[:4])
        self.cursor.execute("SELECT id FROM positions WHERE fen = ?", (clean_fen,))
        row = self.cursor.fetchone()
        if not row: return []
        from_id = row['id']
        self.cursor.execute(
            "SELECT m.id, m.uci, m.comment, p.fen as to_fen FROM moves m JOIN positions p ON m.to_position_id = p.id WHERE m.repertoire_id = ? AND m.from_position_id = ?",
            (repertoire_id, from_id))
        return self.cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()