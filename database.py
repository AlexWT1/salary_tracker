from platformdirs import user_data_dir
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from datetime import datetime

APP_NAME = "SalaryTracker"
APP_AUTHOR = "SalaryAuthor"

data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
data_dir.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = data_dir / "salary_test.db"

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# class Salary(Base):
#     __tablename__ = "salaries"
#     id = Column(Integer, primary_key=True)
#     data = Column(String)
#     salary = Column(Float)
#     advance = Column(Float)
#     sum_ = Column(Float, name="sum")

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False) 
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)

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

    def get_monthly_summary(self):
            """Возвращает список: [(месяц_str, total_sum), ...]"""
            from collections import defaultdict
            records = self.get_all_records()
            monthly = defaultdict(float)
            for _, date_str, amount, _ in records:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    month_key = dt.strftime("%Y-%m")  # например: "2025-03"
                    monthly[month_key] += amount
                except ValueError:
                    continue
            return sorted(monthly.items())  # сортировка по дате

    def get_monthly_breakdown(self, year_month: str):
        """Возвращает словарь: {'salary': X, 'advance': Y, 'other': Z}"""
        records = self.get_all_records()
        breakdown = {"salary": 0.0, "advance": 0.0, "other": 0.0}
        for _, date_str, amount, category in records:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                if dt.strftime("%Y-%m") == year_month:
                    breakdown[category] += amount
            except ValueError:
                continue
        return breakdown

    def get_all_records(self):
        with SessionLocal() as session:
            stmt = select(FinancialRecord)
            result = session.execute(stmt).scalars().all()
            return [(r.id, r.date, r.amount, r.category) for r in result]
    
    def get_records_by_month(self, year_month: str):
        """Возвращает записи за указанный месяц в формате YYYY-MM"""
        with SessionLocal() as session:
            all_records = session.execute(select(FinancialRecord)).scalars().all()
            result = []
            for r in all_records:
                try:
                    rec_date = datetime.strptime(r.date, "%Y-%m-%d")
                    if rec_date.strftime("%Y-%m") == year_month:
                        result.append((r.id, r.date, r.amount, r.category))
                except ValueError:
                    continue
            return result
    def get_record_by_id(self, record_id: int):
        with SessionLocal() as session:
            rec = session.get(FinancialRecord, record_id)
            if rec:
                return (rec.id, rec.date, rec.amount, rec.category)
            return None

    def add_record(self, date: str, amount: float, category: str):
        with SessionLocal() as session:
            new_rec = FinancialRecord(date=date, amount=amount, category=category)
            session.add(new_rec)
            session.commit()

    def delete_record(self, id_: int):
        with SessionLocal() as session:
            rec = session.get(FinancialRecord, id_)
            if rec:
                session.delete(rec)
                session.commit()

    def update_record(self, id_: int, date: str, amount: float, category: str):
        with SessionLocal() as session:
            rec = session.get(FinancialRecord, id_)
            if rec:
                rec.date = date
                rec.amount = amount
                rec.category = category
                session.commit()
    
    def has_salary_or_advance_in_month(self, year_month: str, category: str) -> bool:
        """
        Проверяет, существует ли уже запись с категорией 'salary' или 'advance'
        в указанном месяце (формат 'YYYY-MM').
        """
        if category not in ("salary", "advance"):
            return False  # для 'other' ограничение не применяется

        with SessionLocal() as session:
            records = session.execute(select(FinancialRecord)).scalars().all()
            for r in records:
                try:
                    rec_date = datetime.strptime(r.date, "%Y-%m-%d")
                    if rec_date.strftime("%Y-%m") == year_month and r.category == category:
                        return True
                except ValueError:
                    continue
            return False