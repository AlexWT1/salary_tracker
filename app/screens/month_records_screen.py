# app/screens/month_records_screen.py

from textual.screen import ModalScreen
from textual.widgets import DataTable, Header, Footer, Button, Label
from textual.containers import Vertical
from .add_record_dialog import AddRecordDialog
from .question_dialog import QuestionDialog


class MonthRecordsScreen(ModalScreen):
    def __init__(self, month: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.month = month  # например: "2025-03"

    def compose(self):
        yield Header()
        yield Label(f"Записи за {self.month}", id="month-title")
        yield DataTable(id="month_records")
        yield Button("Добавить запись", id="add_record", variant="success")
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
        record_id = event.row_key.value
        row = self.query_one("#month_records").get_row(record_id)
        date, amount_str, cat_label = row
        amount = float(amount_str.replace(",", ""))
        category = {"Зарплата": "salary", "Аванс": "advance", "Другое": "other"}[cat_label]

        record = (record_id, date, amount, category)

        def handle_update(result):
            if result is not None:
                if result.get("id") is not None:
                    # Обновление
                    self.app.db.update_record(
                        id_=result["id"],
                        date=result["date"],
                        amount=result["amount"],
                        category=result["category"]
                    )
                else:
                    # Новая запись (если добавлять из этого экрана — опционально)
                    pass
                self._load_records()  # перезагрузить список

        self.app.push_screen(AddRecordDialog(is_edit=True, record=record), handle_update)

    def on_key(self, event):
        if event.key == "delete":
            self._delete_selected_record()

    def _delete_selected_record(self):
        table = self.query_one("#month_records", DataTable)
        if table.cursor_row is None:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if not row_key:
            return

        record_id = row_key.value
        row = table.get_row(row_key)
        date = row[0]

        def confirm_delete(should_delete):
            if should_delete:
                self.app.db.delete_record(record_id)
                self._load_records()

        self.app.push_screen(
            QuestionDialog(f"Удалить запись от {date}?"),
            confirm_delete
        )
    def on_button_pressed(self, event):
        if event.button.id == "add_record":
            def handle_new(result):
                if result:
                    self.app.db.add_record(result["date"], result["amount"], result["category"])
                    self._load_records()
            self.app.push_screen(AddRecordDialog(), handle_new)