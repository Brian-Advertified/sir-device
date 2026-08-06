from getpass import getpass

from app.application.services.auth_service import AuthService
from app.domain.enums import UserRole
from app.infrastructure.db.session import SessionLocal, create_schema


def main() -> None:
    create_schema()
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (optional): ").strip() or None
    password = getpass("Password (minimum 10 characters): ")
    with SessionLocal() as session:
        user = AuthService(session).create_staff_user(
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            role=UserRole.ADMINISTRATOR,
        )
        session.commit()
        print(f"Created administrator {user.email}")


if __name__ == "__main__":
    main()
