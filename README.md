<div align="center">

# Qlockain

### A digital identity vault with verifiable document fingerprints.

Register an identity, keep documents in one place, and inspect tamper-evident verification records through a clean Flask dashboard.

<p>
	<img src="https://img.shields.io/badge/Python-Flask-111827?style=flat-square&logo=flask&logoColor=white" alt="Python and Flask">
	<img src="https://img.shields.io/badge/Database-SQLite-111827?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
	<img src="https://img.shields.io/badge/Verification-SHA--256-111827?style=flat-square" alt="SHA-256 verification">
</p>

[Get started](#get-started) · [Features](#what-it-does) · [Security notes](#security-notes)

</div>

## What it does

Qlockain is a Flask application for exploring digital identity and document verification. It creates SHA-256 fingerprints for identity records and uploaded files, then records events in a small proof-of-work blockchain that can be inspected in the app.

| Capability | Details |
| --- | --- |
| Identity vault | Create an account, generate an identity fingerprint, and view its QR code. |
| Document integrity | Upload PDF, JPG/JPEG, PNG, or DOCX files (up to 16 MiB); Qlockain hashes each file and lets you check it later for changes. |
| Identity verification | Verify an identity using its username or ID and password, then compare its fingerprint with the chain. |
| Blockchain explorer | Browse blocks and inspect chain validity, hashes, timestamps, and proof-of-work metadata. |
| Account activity | Review alerts and verification history, update profile details, and change your password. |
| Administration | Review users, documents, verification activity, alerts, and chain statistics from the admin dashboard. |

## Get started

### Requirements

- Python and pip

### Install

Clone the repository and enter its directory:

```bash
git clone https://github.com/me13krishna/Qlockain.git
cd Qlockain
```

Create a virtual environment and install dependencies.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Run

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. On first launch, Qlockain creates the SQLite database and local upload/QR-code directories.

### Demo administrator

The first launch seeds a local administrator account:

| Username | Password |
| --- | --- |
| `admin` | `Admin@123` |

Change this password immediately and keep the app restricted to your own machine. These credentials are for local evaluation only.

## Typical workflow

1. Create an account from the registration page.
2. Open your identity page to view its generated fingerprint and QR code.
3. Upload a supported document from the vault. Qlockain computes a SHA-256 fingerprint and records the upload event.
4. Verify your identity or re-check a document from the relevant page; inspect the resulting status and block in the explorer.

## Built with

- [Flask](https://flask.palletsprojects.com/) for the web application
- [Flask-Login](https://flask-login.readthedocs.io/) and [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) for sessions and persistence
- SQLite for local account, document, alert, and block metadata
- Python's `hashlib` for SHA-256 fingerprints and a custom proof-of-work chain
- [qrcode](https://pypi.org/project/qrcode/) and Pillow for identity QR codes

## Project layout

```text
Qlockain/
├── app.py                 # Flask routes and application setup
├── blockchain.py          # Demo blockchain and verification helpers
├── models.py              # SQLAlchemy models
├── run.py                 # Database initialization and local entry point
├── requirements.txt
├── database/              # SQLite database created at runtime
├── static/
│   ├── css/
│   ├── js/
│   ├── qr_codes/          # Generated QR images
│   └── uploads/            # Uploaded documents
└── templates/             # Jinja pages
```

## Security notes

Qlockain is a learning/demo project, not audited security software. Do not use it to protect real identity data or sensitive documents, and do not expose it to the public internet.

- The administrator password is seeded in the source code; change it before any shared use.
- The app starts Flask's development server with debug mode enabled and binds to all interfaces.
- The blockchain is a custom, single-process proof-of-work demonstration. It is not decentralized, and its live chain state is held in memory; it is not a production blockchain or durable consensus system.
- Uploaded files are stored on local disk without at-rest encryption. Hashing can reveal changes, but it does not encrypt or back up files.
- The Flask secret key is generated at startup, so sessions do not survive a server restart.

## License

No license is currently included in this repository. Contact the repository owner before redistributing or reusing the project.
