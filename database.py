from platformdirs import user_data_dir
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

APP_NAME = "SalaryTracker"
APP_AUTHOR = "SalaryAuthor"

data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
data_dir.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = data_dir / "salary.db"

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Salary(Base):
    __tablename__ = "salaries"
    id = Column(Integer, primary_key=True)
    data = Column(String)
    salary = Column(Float)
    advance = Column(Float)
    sum_ = Column(Float, name="sum")

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)


Base.metadata.create_all(bind=engine)


class Database:
    def __init__(self, db_path=None):
        pass

    def get_organization_name(self) -> str | None:
        with SessionLocal() as session:
            stmt = select(Setting.value).where(Setting.key == "org_name")
            return session.execute(stmt).scalar()

    def set_organization_name(self, name: str):
        name = name.strip()
        with SessionLocal() as session:
            setting = session.execute(
                select(Setting).where(Setting.key == "org_name")
            ).scalar_one_or_none()
            if setting:
                setting.value = name
            else:
                session.add(Setting(key="org_name", value=name))
            session.commit()

    def get_start_date(self) -> str | None:
        with SessionLocal() as session:
            stmt = select(Setting.value).where(Setting.key == "start_date")
            return session.execute(stmt).scalar()

    def set_start_date(self, date: str | None):
        date = date.strip() if date else None
        with SessionLocal() as session:
            setting = session.execute(
                select(Setting).where(Setting.key == "start_date")
            ).scalar_one_or_none()
            if setting:
                setting.value = date
            else:
                session.add(Setting(key="start_date", value=date))
            session.commit()

    def get_end_date(self) -> str | None:
        with SessionLocal() as session:
            stmt = select(Setting.value).where(Setting.key == "end_date")
            return session.execute(stmt).scalar()

    def set_end_date(self, date: str | None):
        date = date.strip() if date else None
        with SessionLocal() as session:
            setting = session.execute(
                select(Setting).where(Setting.key == "end_date")
            ).scalar_one_or_none()
            if setting:
                setting.value = date
            else:
                session.add(Setting(key="end_date", value=date))
            session.commit()

    def get_all_financess(self):
        with SessionLocal() as session:
            stmt = select(Salary)
            result = session.execute(stmt).scalars().all()
            return [
                (s.id, s.data, s.salary, s.advance, s.sum_)
                for s in result
            ]

    def get_last_financess(self):
        with SessionLocal() as session:
            stmt = select(Salary).order_by(Salary.id.desc()).limit(1)
            salary = session.execute(stmt).scalar()
            if salary:
                return (salary.id, salary.data, salary.salary, salary.advance, salary.sum_)
            return None

    def add_financess(self, salary_data):
        data, salary, advance, sum_val = salary_data
        with SessionLocal() as session:
            new_salary = Salary(
                data=data,
                salary=salary,
                advance=advance,
                sum_=sum_val
            )
            session.add(new_salary)
            session.commit()

    def delete_financess(self, id_: int):
        with SessionLocal() as session:
            salary = session.get(Salary, id_)
            if salary:
                session.delete(salary)
                session.commit()

    def update_financess(self, id_, data, salary, advance, sum_):
        with SessionLocal() as session:
            salary_obj = session.get(Salary, id_)
            if salary_obj:
                salary_obj.data = data
                salary_obj.salary = salary
                salary_obj.advance = advance
                salary_obj.sum_ = sum_
                session.commit()