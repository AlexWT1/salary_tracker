# app/screens/month_records_screen.py
from textual.app import App, on

from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Header, Footer, Button, Label
from textual.containers import Horizontal
from textual.containers import Vertical
from .add_record_dialog import AddRecordDialog
from .question_dialog import QuestionDialog


class MonthRecordsScreen(Screen):
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
        for id_, date, amount, category in self.app.db.get_records_by_month(self.month):
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

        # Открываем диалог редактирования
        def handle_update(result):
            if result is not None:
                # Обновляем запись в БД
                self.app.db.update_record(
                    id_=result["id"],
                    date=result["date"],
                    amount=result["amount"],
                    category=result["category"]
                )
                # Перезагружаем список
                self._load_records()

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
    
    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(True)
            event.stop()  # предотвращает стандартное поведение