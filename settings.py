from dotenv import load_dotenv
import os

load_dotenv()

load_dotenv(verbose=True)


from pathlib import Path

env_path = Path(".") / ".env"
x = load_dotenv(dotenv_path=env_path)


class Credentials:
    USERNAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    PUBLIC_CLIENT = os.getenv("PUBLIC_CLIENT")
