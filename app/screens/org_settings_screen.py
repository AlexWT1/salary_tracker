from textual.screen import Screen
from textual.widgets import Button, Label, Input, Static
from textual.containers import Grid
from datetime import datetime

class OrgSettingsScreen(Screen):
    def compose(self):
        db = self.app.db
        org_name = db.get_organization_name() or ""
        start_date = db.get_start_date() or ""
        end_date = db.get_end_date() or ""

        title = "Добро пожаловать! Настройте организацию" if not org_name else "Настройки организации"
        subtitle = "Это нужно сделать только один раз" if not org_name else "Измените данные при необходимости"

        yield Grid(
            Label(title, id="org_setting_title"),
            Label(subtitle, classes="org_setting_label"),
            Label("Название организации:", classes="label"),
            Input(value=org_name, placeholder="ООО «Ромашка»",classes="input-setting", id="org_name"),
            Label("Дата начала работы:", classes="label"),
            Input(value=start_date, placeholder="01.01.2024",classes="input-setting", id="start_date"),
            Label("Дата окончания (пусто = по наст. время):", classes="label"),
            Input(value=end_date, placeholder="31.12.2024 или оставить пустым",classes="input-setting", id="end_date"),
            Static(),
            Button("Отмена", variant="warning", id="cancel"),
            Button("Сохранить", variant="success", id="save"),
            id="settings_grid",
        )

    def on_button_pressed(self, event):
        if event.button.id == "save":
            org_name = self.query_one("#org_name", Input).value.strip()
            start_date = self.query_one("#start_date", Input).value.strip()
            end_date = self.query_one("#end_date", Input).value.strip() or None

            if not org_name or not start_date:
                self.notify("Заполните обязательные поля!", severity="error")
                return

            try:
                datetime.strptime(start_date, "%d.%m.%Y")
                if end_date:
                    datetime.strptime(end_date, "%d.%m.%Y")
            except ValueError:
                self.notify("Неверный формат даты! ДД.ММ.ГГГГ", severity="error")
                return

            db = self.app.db
            db.set_organization_name(org_name)
            db.set_start_date(start_date)
            db.set_end_date(end_date)

            self.app._update_subtitle()
            if self.app.query_one("DataTable").row_count == 0:
                self.app.call_after_refresh(self.app._load_salaries)

            self.dismiss()
        else:
            if not self.app.db.get_organization_name():
                self.notify("Сначала настройте организацию!", severity="warning")
            else:
                self.dismiss()