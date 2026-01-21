# app/screens/month_records_screen.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from salary_app import SalaryApp


from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Header, Footer, Button, Label
from textual.containers import Horizontal
from textual.containers import Vertical
from .add_record_dialog import AddRecordDialog
from .question_dialog import QuestionDialog


class MonthRecordsScreen(Screen):
    @property
    def app(self) -> SalaryApp:
        return super().app  # type: ignore
    
    def __init__(self, month: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.month = month  # например: "2025-03"

    def compose(self):
        yield Header()
        yield Label(f"Записи за {self.month}", id="month-title")
        yield DataTable(id="month_records")
        yield Horizontal(
            Button("Добавить запись", id="add_record", variant="success"),
            Button("Назад", id="back", variant="default"),
            Button("Удалить", variant="error", id="delete"),
            classes="button-row"
        )
        yield Footer()

    def on_mount(self):
        table = self.query_one("#month_records", DataTable)
        table.add_columns("Дата", "Сумма", "Категория")
        table.cursor_type = "row"
        self._load_records()

    def _load_records(self):
        table = self.query_one("#month_records", DataTable)
        table.clear()
        
        records = self.app.db.get_records_by_month(self.month)
        
        if not records:
            self.app.pop_screen()
            return

        for id_, date, amount, category in records:
            cat_label = {"salary": "Зарплата", "advance": "Аванс", "other": "Другое"}[category]
            table.add_row(date, f"{amount:.2f}", cat_label, key=id_)


        
    def on_data_table_row_selected(self, event):
        """Обрабатывает клик по строке — открывает диалог редактирования"""
        record_id = event.row_key.value  # ID записи из БД

        # Получаем запись напрямую из базы данных
        record_data = self.app.db.get_record_by_id(record_id)
        if record_data is None:
            self.notify("Запись не найдена", severity="error")
            self._load_records()
            return

        # Распаковываем: (id, date, amount, category)
        id_, date, amount, category = record_data
        record = (id_, date, amount, category)

        def handle_update(result):
            if result is None:
                return  # пользователь нажал "Отмена" или закрыл окно

            # Проверяем, не является ли результат запросом на удаление
            if isinstance(result, dict) and result.get("action") == "delete":
                # Удаляем запись из БД
                self.app.db.delete_record_by_id(result["id"])
                # Обновляем таблицу
                self._load_records()
                self.notify("Запись удалена", severity="information")
            else:
                # Обычное обновление записи
                self.app.db.update_record(
                    id_=result["id"],
                    date=result["date"],
                    amount=result["amount"],
                    category=result["category"]
                )
                self._load_records()
                self.notify("Запись обновлена", severity="information")

        self.app.push_screen(
            AddRecordDialog(is_edit=True, record=record),
            handle_update
        )
    
    def on_button_pressed(self, event):
        if event.button.id == "add_record":
            def handle_new(result):
                if result:
                    self.app.db.add_record(
                        result["date"],
                        result["amount"],
                        result["category"]
                    )
                    self._load_records()
            self.app.push_screen(AddRecordDialog(month_prefix=self.month), handle_new)

        elif event.button.id == "back":
            self.dismiss(True)

        elif event.button.id == "delete":
            def confirm_delete(accepted):
                if accepted:
                    self.app.db.delete_records_by_month(self.month)
                    self._load_records()
                    self.dismiss()
            self.app.push_screen(QuestionDialog(f"Удаить все записи за {self.month} ?"), confirm_delete)
    
    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(True)
            event.stop()  # предотвращает стандартное поведение