#!/usr/bin/env python3
import socket
import struct
import threading
import argparse
import logging
import sqlite3
import os

MSG_FMT = "!2sH"
MSG_LEN = 4
MAX_UINT16 = 65535

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("Socket closed")
        buf += chunk
    return buf


class WalletDB:
    def __init__(self, filename: str, start_balance: int):
        self.filename = filename
        self.conn = sqlite3.connect(self.filename, check_same_thread=False)
        self._init_db(start_balance)

    def _init_db(self, start_balance: int):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, balance INTEGER)")
        self.conn.commit()
        cur.execute("SELECT COUNT(*) FROM wallet")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO wallet (balance) VALUES (?)", (start_balance,))
            self.conn.commit()

    def get_balance(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT balance FROM wallet WHERE id=1")
        return cur.fetchone()[0]

    def set_balance(self, new_balance: int):
        cur = self.conn.cursor()
        cur.execute("UPDATE wallet SET balance=? WHERE id=1", (new_balance,))
        self.conn.commit()


def handle_client(conn: socket.socket, addr, db: WalletDB, lock: threading.Lock):
    logging.info(f"Client connected: {addr}")
    try:
        with conn:
            while True:
                try:
                    data = recv_exact(conn, MSG_LEN)
                except EOFError:
                    logging.info(f"Client {addr} disconnected")
                    break

                instr_bytes, amount = struct.unpack(MSG_FMT, data)
                instr = instr_bytes.decode('ascii', errors='ignore')

                response_code = b'ER'
                response_value = 0

                with lock:
                    balance = db.get_balance()

                    if instr == 'CR':
                        if balance + amount <= MAX_UINT16:
                            balance += amount
                            db.set_balance(balance)
                            response_code = b'BA'
                            response_value = balance
                    elif instr == 'DB':
                        if balance >= amount:   # change to > if strict
                            balance -= amount
                            db.set_balance(balance)
                            response_code = b'BA'
                            response_value = balance
                    else:
                        logging.warning(f"Invalid instruction '{instr}'")

                conn.sendall(struct.pack(MSG_FMT, response_code, response_value))
    except Exception as e:
        logging.exception(f"Error with client {addr}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--start-balance", type=int, default=0)
    ap.add_argument("--db", default="wallet.db", help="SQLite database file")
    args = ap.parse_args()

    db = WalletDB(args.db, args.start_balance)
    lock = threading.Lock()

    srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv_sock.bind((args.host, args.port))
    srv_sock.listen(8)

    logging.info(f"Server listening on {args.host}:{args.port}")

    try:
        while True:
            conn, addr = srv_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr, db, lock), daemon=True).start()
    except KeyboardInterrupt:
        logging.info("Server shutting down")
    finally:
        srv_sock.close()


if __name__ == "__main__":
    main()
