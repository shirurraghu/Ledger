from app import create_app, db
from app.models import User  # update path if needed
from werkzeug.security import generate_password_hash
from config import Config

def create_admin():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
        if admin:
            print("✅ Admin user already exists.")
        else:
            new_admin = User(
                username=Config.ADMIN_USERNAME,
                is_admin=True  # Make sure your User model has this field
            )
            new_admin.set_password(Config.ADMIN_PASSWORD)
            db.session.add(new_admin)
            db.session.commit()
            print("✅ Admin user created successfully.")

if __name__ == "__main__":
    create_admin()
