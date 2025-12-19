from database import Database
from app.salary_app import SalaryApp

if __name__ == "__main__":
    db = Database()
    SalaryApp(db).run()