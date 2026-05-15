import os
import hashlib
import uuid
import json
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, redirect, url_for, request,
                   flash, session, send_from_directory, jsonify, abort)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image

from models import db, User, Document, BlockchainBlock, Alert, VerificationLog
from blockchain import (get_blockchain, add_identity_to_chain,
                        add_document_to_chain, add_verification_to_chain,
                        verify_identity_on_chain)

# ─── App Configuration ────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32).hex()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'qlockain.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["QR_FOLDER"] = os.path.join(BASE_DIR, "static", "qr_codes")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "docx"}

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def get_user_agent():
    return request.headers.get("User-Agent", "Unknown")


def create_alert(user_id, alert_type, title, message, severity="info"):
    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        title=title,
        message=message,
        severity=severity,
        ip_address=get_client_ip(),
        user_agent=get_user_agent()[:500]
    )
    db.session.add(alert)
    db.session.commit()
    return alert


def generate_qr_code(user):
    qr_data = json.dumps({
        "uid": user.uid,
        "username": user.username,
        "identity_hash": user.identity_hash,
        "platform": "Qlockain"
    })
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00f5d4", back_color="#0a0f1e")
    filename = f"qr_{user.uid}.png"
    path = os.path.join(app.config["QR_FOLDER"], filename)
    img.save(path)
    return f"qr_codes/{filename}"


def save_block_to_db(block, data_type, data_ref=None):
    b = BlockchainBlock(
        block_index=block.index,
        block_hash=block.hash,
        previous_hash=block.previous_hash,
        nonce=block.nonce,
        data_type=data_type,
        data_ref=data_ref,
        timestamp=block.timestamp
    )
    db.session.add(b)
    db.session.commit()
    return b


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Init Database ────────────────────────────────────────────────────────────
def init_db():
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
        # Create default admin
        if not User.query.filter_by(username="admin").first():
            admin = User(
                uid=str(uuid.uuid4()),
                full_name="Qlockain Admin",
                dob="2000-01-01",
                email="admin@qlockain.io",
                phone="0000000000",
                username="admin",
                password_hash=generate_password_hash("Admin@123"),
                is_admin=True,
                is_verified=True
            )
            admin.generate_identity_hash()
            db.session.add(admin)
            db.session.commit()
            try:
                admin.qr_code_path = generate_qr_code(admin)
                db.session.commit()
                block = add_identity_to_chain(admin.uid, admin.username, admin.identity_hash)
                save_block_to_db(block, "IDENTITY_REGISTRATION", admin.uid)
            except Exception:
                pass


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stats = {
        "users": User.query.count(),
        "documents": Document.query.count(),
        "blocks": BlockchainBlock.query.count() + 1,
        "verifications": VerificationLog.query.count()
    }
    return render_template("index.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([full_name, dob, email, phone, username, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html")

        user = User(
            uid=str(uuid.uuid4()),
            full_name=full_name,
            dob=dob,
            email=email,
            phone=phone,
            username=username,
            password_hash=generate_password_hash(password),
            is_verified=False
        )
        user.generate_identity_hash()
        db.session.add(user)
        db.session.commit()

        try:
            user.qr_code_path = generate_qr_code(user)
            db.session.commit()
        except Exception as e:
            print(f"QR error: {e}")

        try:
            block = add_identity_to_chain(user.uid, user.username, user.identity_hash)
            save_block_to_db(block, "IDENTITY_REGISTRATION", user.uid)
            user.is_verified = True
            db.session.commit()
        except Exception as e:
            print(f"Blockchain error: {e}")

        create_alert(user.id, "REGISTRATION", "Account Created",
                     f"Your Qlockain identity vault was created. Identity hash anchored to blockchain.", "success")

        flash("Account created! Your digital identity is now on the blockchain.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            if user:
                user.failed_attempts += 1
                db.session.commit()
                if user.failed_attempts >= 3:
                    create_alert(user.id, "FAILED_LOGIN", "Multiple Failed Login Attempts",
                                 f"Suspicious activity: {user.failed_attempts} failed login attempts from IP {get_client_ip()}",
                                 "danger")
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        user.failed_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)

        prev_agent = session.get("last_user_agent")
        curr_agent = get_user_agent()
        session["last_user_agent"] = curr_agent

        severity = "info"
        msg = f"Login from IP {get_client_ip()}"
        if prev_agent and prev_agent[:50] != curr_agent[:50]:
            severity = "warning"
            msg += " — New device or browser detected"

        create_alert(user.id, "LOGIN", "Successful Login", msg, severity)

        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    create_alert(current_user.id, "LOGOUT", "Session Ended",
                 f"You logged out from IP {get_client_ip()}", "info")
    logout_user()
    flash("You have been logged out securely.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).limit(5).all()
    alerts = Alert.query.filter_by(user_id=current_user.id, is_read=False).order_by(Alert.created_at.desc()).limit(5).all()
    verifications = VerificationLog.query.filter_by(user_id=current_user.id).order_by(VerificationLog.verified_at.desc()).limit(3).all()
    bc = get_blockchain()
    chain_valid, _, chain_msg = bc.is_chain_valid()
    unread_count = Alert.query.filter_by(user_id=current_user.id, is_read=False).count()
    doc_count = Document.query.filter_by(user_id=current_user.id).count()
    ver_count = VerificationLog.query.filter_by(user_id=current_user.id).count()
    return render_template("dashboard.html",
                           docs=docs, alerts=alerts, verifications=verifications,
                           chain_valid=chain_valid, chain_msg=chain_msg,
                           unread_count=unread_count, doc_count=doc_count, ver_count=ver_count)


@app.route("/identity")
@login_required
def identity():
    return render_template("identity.html")


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected.", "danger")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("File type not allowed. Use PDF, JPG, PNG, or DOCX.", "danger")
            return redirect(request.url)

        original_name = secure_filename(file.filename)
        ext = original_name.rsplit(".", 1)[1].lower()
        unique_name = f"{current_user.uid}_{uuid.uuid4().hex[:8]}_{original_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(save_path)

        file_hash = get_file_hash(save_path)
        file_size = os.path.getsize(save_path)

        block = add_document_to_chain(current_user.uid, original_name, file_hash)
        db_block = save_block_to_db(block, "DOCUMENT_UPLOAD", unique_name)

        doc = Document(
            user_id=current_user.id,
            filename=unique_name,
            original_name=original_name,
            file_hash=file_hash,
            file_size=file_size,
            file_type=ext.upper(),
            blockchain_block=block.index,
            is_verified=True
        )
        db.session.add(doc)
        db.session.commit()

        create_alert(current_user.id, "DOCUMENT_UPLOAD", "Document Uploaded",
                     f"'{original_name}' was securely stored and anchored to the blockchain (Block #{block.index}).",
                     "success")

        flash(f"Document '{original_name}' uploaded and anchored to blockchain (Block #{block.index}).", "success")
        return redirect(url_for("documents"))

    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template("upload.html", docs=docs)


@app.route("/documents")
@login_required
def documents():
    docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.uploaded_at.desc()).all()
    return render_template("documents.html", docs=docs)


@app.route("/documents/download/<int:doc_id>")
@login_required
def download_doc(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    return send_from_directory(app.config["UPLOAD_FOLDER"], doc.filename, as_attachment=True, download_name=doc.original_name)


@app.route("/documents/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete_doc(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    try:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], doc.filename))
    except Exception:
        pass
    name = doc.original_name
    create_alert(current_user.id, "DOCUMENT_DELETE", "Document Deleted",
                 f"'{name}' was permanently removed from your vault.", "warning")
    db.session.delete(doc)
    db.session.commit()
    flash(f"Document '{name}' deleted.", "info")
    return redirect(url_for("documents"))


@app.route("/documents/verify/<int:doc_id>")
@login_required
def verify_doc(doc_id):
    doc = Document.query.filter_by(id=doc_id, user_id=current_user.id).first_or_404()
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], doc.filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "FILE_MISSING", "message": "File not found on server."})
    current_hash = get_file_hash(file_path)
    if current_hash == doc.file_hash:
        return jsonify({"status": "INTACT", "message": "Document integrity verified. No tampering detected.", "hash": current_hash})
    else:
        create_alert(current_user.id, "TAMPERING", "Document Tampered!",
                     f"ALERT: '{doc.original_name}' hash mismatch detected! Original: {doc.file_hash[:16]}... Current: {current_hash[:16]}...",
                     "danger")
        return jsonify({"status": "TAMPERED", "message": "ALERT: Document hash mismatch! Tampering detected.", "original": doc.file_hash, "current": current_hash})


@app.route("/verify", methods=["GET", "POST"])
def verify():
    step = int(request.form.get("step", 1))
    result = None
    block_data = None

    if request.method == "POST":
        if step == 1:
            uid_input = request.form.get("uid_input", "").strip()
            user = User.query.filter(
                (User.uid == uid_input) | (User.username == uid_input.lower())
            ).first()
            if not user:
                flash("Identity not found. Check User ID or Username.", "danger")
                return render_template("verify.html", step=1)
            return render_template("verify.html", step=2, uid_input=uid_input, target_user=user)

        elif step == 2:
            uid_input = request.form.get("uid_input", "").strip()
            password = request.form.get("verify_password", "")
            user = User.query.filter(
                (User.uid == uid_input) | (User.username == uid_input.lower())
            ).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Password verification failed.", "danger")
                return render_template("verify.html", step=2, uid_input=uid_input, target_user=user)

            # Recompute hash and compare
            raw = f"{user.uid}{user.username}{user.email}{user.full_name}{user.dob}"
            recomputed_hash = hashlib.sha256(raw.encode()).hexdigest()

            if recomputed_hash != user.identity_hash:
                result = "TAMPERED"
            else:
                blockchain_result, block_data = verify_identity_on_chain(user.identity_hash)
                result = blockchain_result

            log = VerificationLog(
                user_id=user.id,
                identity_hash=user.identity_hash,
                result=result,
                ip_address=get_client_ip(),
                block_index=block_data.get("index") if block_data else None
            )
            db.session.add(log)

            try:
                v_block = add_verification_to_chain(user.uid, result, user.identity_hash)
                save_block_to_db(v_block, "VERIFICATION_LOG", user.uid)
            except Exception:
                pass

            severity_map = {"VERIFIED": "success", "TAMPERED": "danger", "INVALID": "warning"}
            create_alert(user.id, "VERIFICATION", f"Identity {result}",
                         f"Two-factor identity verification completed: {result} from IP {get_client_ip()}",
                         severity_map.get(result, "info"))
            db.session.commit()

            return render_template("verify.html", step=3, result=result, block_data=block_data, target_user=user)

    return render_template("verify.html", step=1)


@app.route("/blockchain")
@login_required
def blockchain_explorer():
    bc = get_blockchain()
    blocks = bc.get_all_blocks()
    stats = bc.get_chain_stats()
    db_blocks = BlockchainBlock.query.order_by(BlockchainBlock.block_index.desc()).all()
    return render_template("blockchain.html", blocks=blocks, stats=stats, db_blocks=db_blocks)


@app.route("/blockchain/api")
@login_required
def blockchain_api():
    bc = get_blockchain()
    return jsonify(bc.get_all_blocks())


@app.route("/alerts")
@login_required
def alerts():
    all_alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).all()
    Alert.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("alerts.html", alerts=all_alerts)


@app.route("/alerts/read/<int:alert_id>")
@login_required
def mark_alert_read(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user.id).first_or_404()
    alert.is_read = True
    db.session.commit()
    return redirect(url_for("alerts"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_info":
            current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
            current_user.phone = request.form.get("phone", current_user.phone).strip()
            db.session.commit()
            flash("Profile updated.", "success")

        elif action == "change_password":
            old_pw = request.form.get("old_password", "")
            new_pw = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not check_password_hash(current_user.password_hash, old_pw):
                flash("Current password incorrect.", "danger")
            elif new_pw != confirm:
                flash("New passwords do not match.", "danger")
            elif len(new_pw) < 8:
                flash("Password must be at least 8 characters.", "danger")
            else:
                current_user.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                create_alert(current_user.id, "PASSWORD_CHANGE", "Password Changed",
                             "Your account password was changed.", "warning")
                flash("Password changed successfully.", "success")

        elif action == "upload_avatar":
            if "avatar" in request.files:
                avatar = request.files["avatar"]
                if avatar and allowed_file(avatar.filename):
                    ext = secure_filename(avatar.filename).rsplit(".", 1)[1].lower()
                    if ext in {"jpg", "jpeg", "png"}:
                        fname = f"avatar_{current_user.uid}.{ext}"
                        avatar.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                        current_user.profile_image = f"uploads/{fname}"
                        db.session.commit()
                        flash("Profile image updated.", "success")

    return render_template("profile.html")


# ─── Admin Routes ─────────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    docs = Document.query.order_by(Document.uploaded_at.desc()).all()
    alerts_all = Alert.query.order_by(Alert.created_at.desc()).limit(50).all()
    verifications = VerificationLog.query.order_by(VerificationLog.verified_at.desc()).limit(20).all()
    bc = get_blockchain()
    stats = bc.get_chain_stats()
    suspicious = Alert.query.filter_by(severity="danger").order_by(Alert.created_at.desc()).limit(10).all()
    return render_template("admin.html", users=users, docs=docs, alerts_all=alerts_all,
                           verifications=verifications, bc_stats=stats, suspicious=suspicious)


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("Cannot delete yourself.", "danger")
        return redirect(url_for("admin_dashboard"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete_doc/<int:doc_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_doc(doc_id):
    doc = Document.query.get_or_404(doc_id)
    try:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], doc.filename))
    except Exception:
        pass
    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted by admin.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/search")
@login_required
@admin_required
def admin_search():
    q = request.args.get("q", "").strip()
    users = []
    if q:
        users = User.query.filter(
            (User.username.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%")) |
            (User.full_name.ilike(f"%{q}%"))
        ).all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "full_name": u.full_name,
        "is_verified": u.is_verified,
        "created_at": u.created_at.strftime("%Y-%m-%d")
    } for u in users])


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="Access Forbidden"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page Not Found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal Server Error"), 500


# ─── Context Processor ────────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    unread = 0
    if current_user.is_authenticated:
        unread = Alert.query.filter_by(user_id=current_user.id, is_read=False).count()
    return {"unread_alerts": unread, "now": datetime.utcnow()}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
