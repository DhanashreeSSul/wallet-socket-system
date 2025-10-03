#!/usr/bin/env python3
"""
Simple Tkinter GUI client for the wallet server.

Usage:
  python3 wallet_gui.py
Default host is 127.0.0.1 and port 5555 (editable in the GUI).
"""
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import socket
import struct

MSG_FMT = "!2sH"
MSG_LEN = 4
MAX_UINT16 = 65535

def recv_exact(sock, n):
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("socket closed")
        buf += chunk
    return buf

def send_instruction(host, port, instr, amount, timeout=5.0):
    """Send a single instruction and return (resp_code_str, value_int)."""
    if instr not in ("CR", "DB"):
        raise ValueError("instr must be 'CR' or 'DB'")
    if not (0 <= amount <= MAX_UINT16):
        raise ValueError("amount must be 0..65535")

    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(struct.pack(MSG_FMT, instr.encode('ascii'), amount))
        resp = recv_exact(s, MSG_LEN)
        code_bytes, value = struct.unpack(MSG_FMT, resp)
        code = code_bytes.decode('ascii', errors='ignore')
        return code, value


class WalletGUI:
    def __init__(self, root):
        self.root = root
        root.title("Wallet GUI Client")

        # Host / Port
        frm_conn = tk.Frame(root)
        frm_conn.pack(padx=8, pady=6, anchor='w')
        tk.Label(frm_conn, text="Host:").grid(row=0, column=0, sticky='w')
        self.host_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(frm_conn, textvariable=self.host_var, width=15).grid(row=0, column=1, sticky='w', padx=(2,8))
        tk.Label(frm_conn, text="Port:").grid(row=0, column=2, sticky='w')
        self.port_var = tk.IntVar(value=5555)
        tk.Entry(frm_conn, textvariable=self.port_var, width=6).grid(row=0, column=3, sticky='w')

        # Amount
        frm_amt = tk.Frame(root)
        frm_amt.pack(padx=8, pady=4, anchor='w')
        tk.Label(frm_amt, text="Amount:").grid(row=0, column=0, sticky='w')
        self.amount_var = tk.StringVar()
        tk.Entry(frm_amt, textvariable=self.amount_var, width=12).grid(row=0, column=1, sticky='w')

        # Buttons
        frm_btn = tk.Frame(root)
        frm_btn.pack(padx=8, pady=6, anchor='w')
        tk.Button(frm_btn, text="Credit", width=10, command=self.on_credit).grid(row=0, column=0, padx=4)
        tk.Button(frm_btn, text="Debit", width=10, command=self.on_debit).grid(row=0, column=1, padx=4)
        tk.Button(frm_btn, text="Get Balance", width=12, command=self.on_get_balance).grid(row=0, column=2, padx=6)

        # Current balance label
        self.balance_label = tk.Label(root, text="Balance: (unknown)", font=("TkDefaultFont", 11, "bold"))
        self.balance_label.pack(padx=8, pady=(0,6), anchor='w')

        # History log
        tk.Label(root, text="History:").pack(anchor='w', padx=8)
        self.history = scrolledtext.ScrolledText(root, height=10, width=60, state='disabled')
        self.history.pack(padx=8, pady=(0,8))

    def log(self, msg):
        self.history.config(state='normal')
        self.history.insert('end', msg + '\n')
        self.history.see('end')
        self.history.config(state='disabled')

    def set_balance_label(self, value):
        self.balance_label.config(text=f"Balance: {value}")

    def do_network_op(self, instr, amount):
        host = self.host_var.get()
        port = int(self.port_var.get())
        try:
            code, value = send_instruction(host, port, instr, amount)
            if code == 'BA':
                msg = f"{instr} {amount} -> BALANCE = {value}"
                self.root.after(0, lambda: self.set_balance_label(value))
            else:
                msg = f"{instr} {amount} -> ERROR from server"
            self.root.after(0, lambda: self.log(msg))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"NETWORK ERROR: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Network error", str(e)))

    def parse_amount(self):
        s = self.amount_var.get().strip()
        if s == "":
            raise ValueError("Enter an amount")
        amt = int(s)
        if not (0 <= amt <= MAX_UINT16):
            raise ValueError(f"Amount must be 0..{MAX_UINT16}")
        return amt

    def on_credit(self):
        try:
            amt = self.parse_amount()
        except Exception as e:
            messagebox.showerror("Input error", str(e))
            return
        threading.Thread(target=self.do_network_op, args=("CR", amt), daemon=True).start()

    def on_debit(self):
        try:
            amt = self.parse_amount()
        except Exception as e:
            messagebox.showerror("Input error", str(e))
            return
        threading.Thread(target=self.do_network_op, args=("DB", amt), daemon=True).start()

    def on_get_balance(self):
        # send CR 0 to query balance safely (does not change value).
        threading.Thread(target=self.do_network_op, args=("CR", 0), daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = WalletGUI(root)
    root.mainloop()
