def generate_email(name: str):
    return f"{name}@example.com"


def enrich_user(user: dict):
    user["role"] = "admin" if user["id"] == 101 else "user"
    return user


def format_user(user: dict):
    return f"{user['name']} ({user['email']}) - {user['role']}"