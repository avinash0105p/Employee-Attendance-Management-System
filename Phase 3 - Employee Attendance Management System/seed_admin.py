import hashlib, secrets, getpass
from database import SessionLocal
from models import Role, User

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    ).hex()
    return f"{salt}${password_hash}"

def create_admin():
    db = SessionLocal()
    try:
        for role_name in ["Admin", "Manager", "Employee"]:
            role = db.query(Role).filter(Role.role_name == role_name).first()
            if role is None:
                db.add(Role(role_name=role_name))
        db.commit()

        existing_admin = db.query(User).join(
            Role, User.role_id == Role.role_id
        ).filter(Role.role_name == "Admin").first()

        if existing_admin:
            print("An Admin account already exists.")
            print("Admin User ID:", existing_admin.user_id)
            return

        full_name = input("Enter Admin name: ").strip()
        email = input("Enter Admin email: ").strip()
        phone = input("Enter Admin phone: ").strip()
        password = getpass.getpass("Enter Admin password: ")

        if len(full_name) < 3 or "@" not in email or "." not in email:
            print("Invalid inputs provided.")
            return

        duplicate = db.query(User).filter(User.email == email).first()
        if duplicate:
            print("This email already exists.")
            return

        admin_role = db.query(Role).filter(Role.role_name == "Admin").first()
        admin = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            role_id=admin_role.role_id,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Initial Admin created successfully.")
        print("Admin User ID:", admin.user_id)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()