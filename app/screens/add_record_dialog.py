# app/screens/add_record_dialog.py

from textual.widgets import Button, Label, Input, Checkbox, Static
from textual.containers import Grid
from textual.screen import Screen

class AddRecordDialog(Screen):
    def __init__(self, is_edit=False, record=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_edit = is_edit
        self.record = record
        self.initial_category = record[3] if is_edit else "salary"

    def compose(self):
        title = "Изменить запись" if self.is_edit else "Добавить доход"
        date_val = self.record[1] if self.is_edit else ""
        amount_val = str(self.record[2]) if self.is_edit else ""

        yield Grid(
            Label(title, id="title"),
            Label("Дата (ГГГГ-ММ-ДД):", classes="label"),
            Input(value=date_val, placeholder="2025-03-15", id="date"),
            Label("Сумма:", classes="label"),
            Input(value=amount_val, placeholder="10000", id="amount"),
            Label("Категория:", classes="label"),
            Checkbox("Зарплата", id="chk_salary"),
            Checkbox("Аванс", id="chk_advance"),
            Checkbox("Другое", id="chk_other"),
            Static(),
            Button("Отмена", variant="warning", id="cancel"),
            Button("Сохранить", variant="success", id="save"),
            id="add-record-dialog"
        )

    def on_mount(self):
        # Устанавливаем начальное состояние
        if self.initial_category == "salary":
            self.query_one("#chk_salary", Checkbox).value = True
        elif self.initial_category == "advance":
            self.query_one("#chk_advance", Checkbox).value = True
        else:
            self.query_one("#chk_other", Checkbox).value = True

    def _sync_checkboxes(self, changed_id: str):
        """Снимает галочки со всех, кроме changed_id"""
        ids = ["chk_salary", "chk_advance", "chk_other"]
        for id_ in ids:
            if id_ != changed_id:
                self.query_one(f"#{id_}", Checkbox).value = False

    def on_checkbox_changed(self, event: Checkbox.Changed):
        """Обрабатывает изменение любого чекбокса"""
        if event.checkbox.value:  # только если поставили галочку
            self._sync_checkboxes(event.checkbox.id)

    def on_button_pressed(self, event):
        if event.button.id == "save":
            date = self.query_one("#date", Input).value.strip()
            amount_str = self.query_one("#amount", Input).value.strip()

            # Определяем категорию по активному чекбоксу
            category = "other"  # default
            if self.query_one("#chk_salary", Checkbox).value:
                category = "salary"
            elif self.query_one("#chk_advance", Checkbox).value:
                category = "advance"
            elif self.query_one("#chk_other", Checkbox).value:
                category = "other"

            if not date or not amount_str:
                self.notify("Заполните все поля", severity="error")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                self.notify("Сумма должна быть положительным числом", severity="error")
                return

            try:
                from datetime import datetime
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                self.notify("Неверный формат даты (используйте ГГГГ-ММ-ДД)", severity="error")
                return

            result = {
                "date": date,
                "amount": amount,
                "category": category
            }
            if self.is_edit:
                result["id"] = self.record[0]
            self.dismiss(result)
        else:
            self.dismiss(None)