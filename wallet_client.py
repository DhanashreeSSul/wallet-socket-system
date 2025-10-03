#!/usr/bin/env python3
"""
wallet_client.py
Usage examples:
  python3 wallet_client.py CR 200               # one-shot: credit 200
  python3 wallet_client.py DB 50                # one-shot: debit 50
  python3 wallet_client.py --interactive        # interactive mode (keep connection open)
"""
import socket
import struct
import argparse

MSG_FMT = "!2sH"
MSG_LEN = 4
MAX_UINT16 = 65535


def recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise EOFError("Socket closed")
        buf += chunk
    return buf


def send_instruction_once(host: str, port: int, instr: str, amount: int):
    if instr not in ("CR", "DB"):
        raise ValueError("Instruction must be 'CR' or 'DB'")
    if not (0 <= amount <= MAX_UINT16):
        raise ValueError("Amount must be 0..65535")

    with socket.create_connection((host, port)) as s:
        s.sendall(struct.pack(MSG_FMT, instr.encode('ascii'), amount))
        resp = recv_exact(s, MSG_LEN)
        resp_code, value = struct.unpack(MSG_FMT, resp)
        resp_code = resp_code.decode('ascii')
        if resp_code == 'BA':
            print(f"[SERVER] BALANCE = {value}")
        else:
            print("[SERVER] ERROR (operation failed)")


def interactive_mode(host: str, port: int):
    print("Interactive mode. Type: CR <amount>  or  DB <amount>  or  quit")
    with socket.create_connection((host, port)) as s:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            if line.lower() in ('quit', 'exit'):
                print("Closing connection.")
                return
            parts = line.split()
            if len(parts) != 2:
                print("Invalid input. Example: CR 100")
                continue
            instr, amt_s = parts[0].upper(), parts[1]
            try:
                amt = int(amt_s)
                s.sendall(struct.pack(MSG_FMT, instr.encode('ascii'), amt))
                resp = recv_exact(s, MSG_LEN)
                resp_code, value = struct.unpack(MSG_FMT, resp)
                resp_code = resp_code.decode('ascii')
                if resp_code == 'BA':
                    print(f"[SERVER] BALANCE = {value}")
                else:
                    print("[SERVER] ERROR (operation failed)")
            except Exception as e:
                print("Error:", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("instruction", nargs="?", help="CR or DB")
    ap.add_argument("amount", nargs="?", type=int, help="Amount 0..65535")
    ap.add_argument("--interactive", action="store_true")
    args = ap.parse_args()

    if args.interactive:
        interactive_mode(args.host, args.port)
    else:
        if not args.instruction or args.amount is None:
            ap.print_help()
            return
        send_instruction_once(args.host, args.port, args.instruction.upper(), args.amount)


if __name__ == "__main__":
    main()
