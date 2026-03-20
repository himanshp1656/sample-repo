from utils import generate_email


class DatabaseClient:
    def fetch_user(self, user_id: int):
        name = self._get_name(user_id)
        email = generate_email(name)
        return {
            "id": user_id,
            "name": name,
            "email": email
        }

    def _get_name(self, user_id: int):
        return f"user_{user_id}"