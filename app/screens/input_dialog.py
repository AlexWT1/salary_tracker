from textual.widgets import Button, Label, Input, Static
from textual.containers import Grid
from textual.screen import Screen

class InputDialog(Screen):
    def __init__(self, is_edit=False, current=None, row_key=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_edit = is_edit
        self.current = current or ("", "", "", "")
        self.row_key = row_key

    def compose(self):
        date, salary, advance, total = self.current

        title = "Изменить запись" if self.is_edit else "Добавить запись"
        ok_label = "Сохранить" if self.is_edit else "Ок"

        yield Grid(
            Label(title, id='title'),
            Label('Дата:', classes='label'),
            Input(value=date, placeholder='Дата', classes='input', id='date'),
            Label('Зарплата:', classes='label'),
            Input(value=str(salary) if salary else "", placeholder='Зарплата', classes='input', id='salary'),
            Label('Аванс:', classes='label'),
            Input(value=str(advance) if advance else "", placeholder='Аванс', classes='input', id='advance'),
            Static(),
            Button("Отмена", variant="warning", id="cancel"),
            Button(ok_label, variant="success", id="ok"),
            id="input-dialog",
        )

    def on_button_pressed(self, event):
        if event.button.id == 'ok':
            try:
                date = self.query_one("#date", Input).value.strip()
                salary_str = self.query_one("#salary", Input).value.strip()
                advance_str = self.query_one("#advance", Input).value.strip()

                if not date or not salary_str or not advance_str:
                    self.notify("Все поля обязательны!", severity="error")
                    return

                salary = float(salary_str)
                advance = float(advance_str)
                total = salary + advance

                self.dismiss({
                    'date': date,
                    'salary': salary,
                    'advance': advance,
                    'total': total,
                    'row_key': self.row_key
                })
            except ValueError:
                self.notify("Зарплата и аванс должны быть числами!", severity="error")
        else:
            self.dismiss(None)