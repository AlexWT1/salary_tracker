# app/screens/add_record_dialog.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from salary_app import SalaryApp


from textual.widgets import Button, Label, Input, Checkbox, Static
from textual.containers import Grid
from textual.screen import Screen

class AddRecordDialog(Screen):
    @property
    def app(self) -> SalaryApp:
        return super().app  # type: ignore
    
    def __init__(self, is_edit=False, record=None, month_prefix=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_edit = is_edit
        self.record = record
        self.month_prefix = month_prefix

    def compose(self):
        title = "Изменить запись" if self.is_edit else "Добавить доход"
        if self.is_edit:
            assert self.record is not None

            date_val = self.record[1]
            amount_val = str(self.record[2])
        else:
            # Автоматически подставляем дату: месяц + "-01"
            date_val = f"{self.month_prefix}-" if self.month_prefix else ""
            amount_val = ""

         # Формируем список виджетов
        widgets = [
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
        ]

        # Добавляем кнопку "Удалить" ТОЛЬКО при редактировании
        if self.is_edit:
            widgets.append(Button("Удалить", variant="error", id="delete_record"))

        yield Grid(*widgets, id="add-record-dialog")

    def on_mount(self):
        if self.month_prefix and not self.is_edit:
            if self.app.db.has_salary_or_advance_in_month(self.month_prefix, "salary"):
                self.query_one("#chk_salary", Checkbox).disabled = True
            if self.app.db.has_salary_or_advance_in_month(self.month_prefix, "advance"):
                self.query_one("#chk_advance", Checkbox).disabled = True

    def _sync_checkboxes(self, changed_id: str):
        """Снимает галочки со всех, кроме changed_id"""
        ids = ["chk_salary", "chk_advance", "chk_other"]
        for id_ in ids:
            if id_ != changed_id:
                self.query_one(f"#{id_}", Checkbox).value = False

    def on_checkbox_changed(self, event: Checkbox.Changed):
        """Обрабатывает изменение любого чекбокса"""
        checkbox = event.checkbox
        if checkbox.value and checkbox.id is not None:
            self._sync_checkboxes(checkbox.id)

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
                dt = datetime.strptime(date, "%Y-%m-%d")
                year_month = dt.strftime("%Y-%m")
            except ValueError:
                self.notify("Неверный формат даты (используйте ГГГГ-ММ-ДД)", severity="error")
                return

            result = {
                "date": date,
                "amount": amount,
                "category": category
            }

            if category in ("salary", "advance"):
                if self.app.db.has_salary_or_advance_in_month(year_month, category):
                    cat_name = "зарплата" if category == "salary" else "аванс"
                    self.notify(f"В этом месяце уже есть запись '{cat_name}'. Нельзя добавить вторую.", severity="error")
                    return

            
            if self.is_edit:
                assert self.record is not None
                result["id"] = self.record[0]
            self.dismiss(result)
        elif event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "delete_record":
            assert self.record is not None

            def confirm_delete(accepted):
                assert self.record is not None

                if accepted:
                    # Передаём ID записи для удаления
                    self.dismiss({"action": "delete", "id": self.record[0]})

            from .question_dialog import QuestionDialog  # убедитесь, что путь правильный
            self.app.push_screen(
                QuestionDialog(f"Удалить запись от {self.record[1]}?"),
                callback=confirm_delete
            )
