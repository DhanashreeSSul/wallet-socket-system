# wallet-socket-system

## Project Overview
The **Wallet Socket System** is a Python-based project that simulates a simple wallet with **Credit** and **Debit** operations over a **TCP socket protocol**.  
It demonstrates:
- TCP/IP socket programming  
- Custom binary protocol design  
- SQLite database persistence  
- Tkinter GUI client  
- Automated test runner for validation  

This project was created as a **lab assignment (PCCOE)** to learn **network programming, database integration, and GUI development** in Python.

---

## ⚙️ Tech Stack
- **Python 3**  
- **SQLite** (lightweight database)  
- **Tkinter** (GUI library)  
- Standard libraries: `socket`, `struct`, `threading`, `argparse`, `sqlite3`

---

## 📂 Project Structure

Wallet/ # Root project folder
├── wallet_server.py # TCP server with SQLite persistence
├── wallet_client.py # CLI client (one-shot or interactive)
├── wallet_gui.py # Tkinter GUI client
├── wallet_testrunner.py # Automated test runner (for validation/grading)
├── wallet.db # SQLite database file (created at runtime)
└── README.md # Project documentation


---

## 🚀 How to Run

### 1. Start the Server
Start the server with a chosen balance:
```bash
python3 wallet_server.py --start-balance 1000 --db wallet.db

Default host: 0.0.0.0
Default port: 5555

2. CLI Client
Credit 200:
python3 wallet_client.py CR 200

Debit 50:
python3 wallet_client.py DB 50


Interactive mode:
python3 wallet_client.py --interactive

3. GUI Client
Run the Tkinter GUI:
python3 wallet_gui.py

Enter amount → click Credit, Debit, or Get Balance
Balance and history displayed in the window

Database (SQLite)

All wallet data is persisted in wallet.db.
This means the balance is saved across server restarts.

Inspect the Database

Install SQLite CLI:
sudo apt install sqlite3 -y


Open the DB:
sqlite3 wallet.db

Commands inside SQLite:

.tables              -- list tables
.schema wallet       -- show table schema
SELECT * FROM wallet; -- view current balance
.exit                -- exit


Example:
sqlite> .tables
wallet
sqlite> SELECT * FROM wallet;
1|1350

(1 = wallet ID, 1350 = current balance)

Protocol Specification
Each message is 4 bytes:

Client → Server
2 bytes: Instruction (CR = Credit, DB = Debit)
2 bytes: Amount (0..65535)

Server → Client
2 bytes: Response (BA = Balance, ER = Error)
2 bytes: Value (new balance if BA, 0 if ER)
