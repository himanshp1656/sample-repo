from service import UserService

def start_app():
    service = UserService()
    result = service.handle_request(101)
    print("Final Result:", result)


if __name__ == "__main__":
    start_app()