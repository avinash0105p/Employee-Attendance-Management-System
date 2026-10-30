from database import SessionLocal
from models import User, Role
from auth import hash_password


db = SessionLocal()

try:
    email = input("Enter Admin email: ").strip()
    password = input("Enter new Admin password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters")

    else:
        admin = (
            db.query(User)
            .join(Role, User.role_id == Role.role_id)
            .filter(
                User.email == email,
                Role.role_name == "Admin"
            )
            .first()
        )

        if admin is None:
            print("Admin not found with this email")

        else:
            admin.password_hash = hash_password(password)
            db.commit()

            print("Admin password updated successfully")

except Exception as error:
    db.rollback()
    print("Error:", error)

finally:
    db.close()