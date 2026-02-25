from platformdirs import user_data_dir
from pathlib import Path
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import sessionmaker

from datetime import datetime

APP_NAME = "SalaryTracker"
APP_AUTHOR = "SalaryAuthor"

data_dir = Path(user_data_dir(APP_NAME, APP_AUTHOR))
data_dir.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = data_dir / "salary_test.db"

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

class Setting(Base):
    __tablename__ = "settings"
    
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str | None] = mapped_column(String)


Base.metadata.create_all(bind=engine)


class Database:

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
        """
        Возвращает сводку по месяцам, включая общую сумму и "итоговую сумму за месяц" (аванс текущего + зарплата следующего).
        Формат: [(месяц_str, total_sum_current_month, total_for_display), ...]
        """
        from collections import defaultdict
        
        all_records = self.get_all_records()
        
        monthly_total = defaultdict(float)
        monthly_advance = defaultdict(float)
        monthly_salary = defaultdict(float)

        for _, date_str, amount, category in all_records:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m") # YYYY-MM
                
                monthly_total[month_key] += amount
                if category == "advance":
                    monthly_advance[month_key] += amount
                elif category == "salary":
                    monthly_salary[month_key] += amount
            except ValueError:
                continue

        all_months = sorted(list(set(monthly_total.keys()) | set(monthly_advance.keys()) | set(monthly_salary.keys())))
        
        result_summary = []
        for i, month_key in enumerate(all_months):
            current_month_total = monthly_total[month_key]
            current_month_advance = monthly_advance[month_key]
            
            next_month_salary = 0.0
            if i + 1 < len(all_months):
                next_month_key = all_months[i+1]
                next_month_salary = monthly_salary[next_month_key]
            elif (dt_current_month := datetime.strptime(month_key, "%Y-%m")).month == datetime.now().month and dt_current_month.year == datetime.now().year: #If it is current month, check one more month. Otherwise, we don't care
                next_month_year = dt_current_month.year
                next_month_month = dt_current_month.month + 1
                if next_month_month > 12:
                    next_month_month = 1
                    next_month_year += 1
                
                for _, other_date_str, other_amount, other_category in all_records:
                    try:
                        other_dt = datetime.strptime(other_date_str, "%Y-%m-%d")
                        if other_dt.year == next_month_year and other_dt.month == next_month_month and other_category == "salary":
                            next_month_salary += other_amount
                    except ValueError:
                        continue


            total_for_display = current_month_advance + next_month_salary
            result_summary.append((month_key, current_month_total, total_for_display))
            
        return result_summary

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
        

    def delete_record_by_id(self, record_id: int):
        with SessionLocal() as session:
            record = session.get(FinancialRecord, record_id)
            if record:
                session.delete(record)
                session.commit()

    def add_record(self, date: str, amount: float, category: str):
        with SessionLocal() as session:
            new_rec = FinancialRecord(date=date, amount=amount, category=category)
            session.add(new_rec)
            session.commit()

    def delete_records_by_month(self, year_month: str):
        with SessionLocal() as session:
            stmt = delete(FinancialRecord).where(FinancialRecord.date.like(f"{year_month}-%"))
            session.execute(stmt)
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
            return False

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