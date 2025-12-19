from textual.screen import Screen
from textual.widgets import Button, Label
from textual.containers import Grid

class QuestionDialog(Screen):
    def __init__(self, message: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    def compose(self):
        yield Grid(
            Label(self.message, id="question"),
            Button("Да", variant="error", id="yes"),
            Button("Нет", variant="primary", id="no"),
            id="question-dialog"
        )

    def on_button_pressed(self, event):
        self.dismiss(event.button.id == "yes")