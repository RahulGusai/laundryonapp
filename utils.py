from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_password_correct(login_password: str, db_passsword: str):
    return password_context.verify(login_password, db_passsword)
