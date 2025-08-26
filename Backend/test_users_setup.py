from db_helper import create_user

def setup_test_users():
    try:
        create_user("admin", "admin123", "admin")
        print("✅ Admin account created: admin / admin123")

        create_user("user1", "user123", "user")
        print("✅ User account created: user1 / user123")

    except Exception as e:
        print("⚠️ Error while creating test users:", e)

if __name__ == "__main__":
    setup_test_users()
