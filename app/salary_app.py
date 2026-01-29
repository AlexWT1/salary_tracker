from textual.app import App
from textual._on import on
from textual.widgets import Header, Footer, Button, DataTable, Static
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate

from datetime import datetime


from .screens.input_dialog import InputDialog
from .screens.question_dialog import QuestionDialog
from .screens.org_settings_screen import OrgSettingsScreen
from .screens.about_screen import AboutScreen
from .screens.add_record_dialog import AddRecordDialog
from .screens.month_records_screen import MonthRecordsScreen

from database import Database


class SalaryApp(App):
    CSS_PATH = "salaries.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Поменять тему"),
        ("q", "request_quit", "Выйти"),
        ("i", "result_financess", "Всего"),
        ("n", "open_settings", "Настройки"),
        # ("c", "change", "Изменить"),
        # ('a', 'add', "Добавить"),
        ('u', 'open_about', 'О версии')
    ]

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                Button("Добавить", variant="success", id="add"),
                # Button("Изменить", variant="default", id="change"),
                # Button("Удалить", variant="error", id="delete"),
                # Static(classes="separator"),
                Button("Настройки", variant="primary", id="settings"),
                classes="buttons_panel"
            ),
            DataTable(id="salary_app_table",classes="salaries_list")
        )
        yield Footer()

    def on_mount(self):
        self.title = "Доходы"
        table = self.query_one(DataTable)
        table.add_columns("Месяц", "Сумма")
        table.cursor_type = "row"
        table.zebra_stripes = True
        self._update_subtitle()
        self._load_monthly_view()

        if not self.db.get_organization_name():
            self.sub_title = "Первоначальная настройка"
            self.push_screen(OrgSettingsScreen())
        else:
            self._update_subtitle()
            self._load_monthly_view()

    def _load_monthly_view(self):
        table = self.query_one(DataTable)
        table.clear()
        for month, total in self.db.get_monthly_summary():
            table.add_row(month, f"{total:,.2f} ₽", key=month)

    def _update_subtitle(self):
        org = self.db.get_organization_name() or ""
        start = self.db.get_start_date() or ""
        end = self.db.get_end_date()
        period = f" ({start} — наст. вр.)" if start and not end else f" ({start} — {end})" if start else ""
        self.sub_title = f"Финансовая история {org}{period}"
    
    def action_request_quit(self):
        def check_answer(accepted):
            if accepted:
                self.exit()
        self.push_screen(QuestionDialog('Вы действительно хотите выйти ?'),check_answer)

    def action_result_financess(self):
        total = 0.0
        for _, _, amount, _ in self.db.get_all_records():
            total += amount
        self.notify(f"Всего заработано по организации: {total:,.2f} ₽", severity="information")

    def action_setting_screen(self):
        self.push_screen(OrgSettingsScreen())

                

    @on(Button.Pressed, "#add")
    def action_add(self):
        today_year = datetime.today().year
        def handle_result(result):
            if result:
                self.db.add_record(result["date"], result["amount"], result["category"])
                self._load_monthly_view()

        self.push_screen(AddRecordDialog(month_prefix=today_year), handle_result)

    @on(DataTable.RowSelected, "#salary_app_table")
    def on_month_selected(self, event):
        month = event.row_key.value

        def after_month_screen(result):
            if result is True:
                self._load_monthly_view()

        self.push_screen(MonthRecordsScreen(month), after_month_screen)
    


    @on(Button.Pressed, "#settings")
    def action_open_settings(self):
        self.push_screen(OrgSettingsScreen())

    def action_open_about(self):
        self.push_screen(AboutScreen())