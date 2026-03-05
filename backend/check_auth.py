from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password, hash_password

db = SessionLocal()
user = db.query(User).filter(User.email == "admin@docufiscal.it").first()

if user:
    is_correct = verify_password("admin123", user.hashed_password)
    print(f"User found: {user.email}")
    print(f"Password 'admin123' correct: {is_correct}")
    if not is_correct:
        print("Updating password to 'admin123'...")
        user.hashed_password = hash_password("admin123")
        db.commit()
        print("Password updated.")
else:
    print("User admin@docufiscal.it not found!")
db.close()
