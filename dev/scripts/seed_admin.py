from dev.db import SessionLocal
from dev.models import AdminUser
from dev.auth import hash_password


def seed(username='admin', password='admin'):
    with SessionLocal() as session:
        if session.query(AdminUser).filter_by(username=username).first():
            print('admin exists')
            return
        a = AdminUser(username=username, password_hash=hash_password(password))
        session.add(a)
        session.commit()
        print('admin created')

if __name__ == '__main__':
    seed()
