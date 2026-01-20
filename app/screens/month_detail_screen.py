from textual.screen import ModalScreen
from textual.widgets import Label, Button, Static
from textual.containers import Vertical, Horizontal

class MonthDetailScreen(ModalScreen):
    def __init__(self, month: str, breakdown: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.month = month
        self.breakdown = breakdown

    def compose(self):
        s = self.breakdown
        yield Vertical(
            Label(f"Детализация за {self.month}", id="detail-title"),
            Static(f"Зарплата: {s['salary']:,.2f}"),
            Static(f"Аванс:     {s['advance']:,.2f}"),
            Static(f"Другое:    {s['other']:,.2f}"),
            Horizontal(
                Button("Закрыть", variant="primary", id="close"),
                classes="detail-buttons"
            ),
            id="month-detail"
        )

    def on_button_pressed(self, event):
        if event.button.id == "close":
            self.dismiss()