from textual.app import App, on
from textual.widgets import Header, Footer, Button, DataTable, Static
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate


from .screens.input_dialog import InputDialog
from .screens.question_dialog import QuestionDialog
from .screens.org_settings_screen import OrgSettingsScreen
from .screens.about_screen import AboutScreen
from .screens.month_detail_screen import MonthDetailScreen
from .screens.add_record_dialog import AddRecordDialog
from .screens.month_records_screen import MonthRecordsScreen


class SalaryApp(App):
    CSS_PATH = "salaries.tcss"
    BINDINGS = [
        ("m", "toggle_dark", "Поменять тему"),
        ("q", "request_quit", "Выйти"),
        ("i", "result_financess", "Итого"),
        ("n", "open_settings", "Настройки"),
        ("c", "change", "Изменить"),
        ('a', 'add', "Добавить"),
        ('u', 'open_about', 'О версии')
    ]

    def __init__(self, db):
        super().__init__()
        self.db = db

    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                Button("Добавить", variant="success", id="add"),
                Button("Изменить", variant="default", id="change"),
                Button("Удалить", variant="error", id="delete"),
                Static(classes="separator"),
                Button("Настройки", variant="primary", id="settings"),
                Button("❓", id="about", variant="default", classes="icon-button"),
                classes="buttons_panel"
            ),
            DataTable(classes="salaries_list")
        )
        yield Footer()

    # def on_mount(self):
    #     self.title = "Доходы"
    #     table = self.query_one(DataTable)
    #     table.add_columns("Дата", "Зарплата", "Аванс", "Итог")
    #     table.cursor_type = "row"
    #     table.zebra_stripes = True
    #     table.focus()

    #     if not self.db.get_organization_name():
    #         self.sub_title = "Первоначальная настройка"
    #         self.push_screen(OrgSettingsScreen())
    #     else:
    #         self._update_subtitle()
    #         self._load_salaries()
    def on_mount(self):
        self.title = "Доходы"
        table = self.query_one(DataTable)
        table.add_columns("Месяц", "Сумма")
        table.cursor_type = "row"
        table.zebra_stripes = True
        self._update_subtitle()
        self._load_monthly_view()

    def _load_monthly_view(self):
        table = self.query_one(DataTable)
        table.clear()
        for month, total in self.db.get_monthly_summary():
            table.add_row(month, f"{total:,.2f}", key=month)

    def _update_subtitle(self):
        org = self.db.get_organization_name() or ""
        start = self.db.get_start_date() or ""
        end = self.db.get_end_date()
        period = f" ({start} — наст. вр.)" if start and not end else f" ({start} — {end})" if start else ""
        self.sub_title = f"Финансовая история {org}{period}"

    def _load_salaries(self):
        table = self.query_one(DataTable)
        table.clear()
        for row in self.db.get_all_financess():
            id_, *data = row
            table.add_row(*data, key=id_)
    def action_request_quit(self):
            def check_answer(accepted):
                if accepted:
                    self.exit()
            self.push_screen(QuestionDialog('Вы действительно хотите выйти ?'),check_answer)
        
    def action_setting_screen(self):
        self.push_screen(OrgSettingsScreen())

    def action_result_financess(self):
        data_table = self.query_one(DataTable)

        if data_table.row_count == 0:
            self.notify("Таблица пуста", severity="warning")
            return

        total = 0.0
        last_col_index = len(data_table.ordered_columns) - 1

        for row_index in range(data_table.row_count):
            coord = Coordinate(row_index, last_col_index)
            value = data_table.get_cell_at(coord)

            try:
                total += float(value)
            except (ValueError, TypeError):
                continue 

        self.notify(f"Всего заработано по организации: {total:,.2f}", severity="success")
                

    # @on(Button.Pressed, "#add")
    # def action_add(self):
    #     def handle_result(result):
    #         if result:
    #             self.db.add_financess((result['date'], result['salary'], result['advance'], result['total']))
    #             new_id, *data = self.db.get_last_financess()
    #             table = self.query_one(DataTable)
    #             table.add_row(
    #                 result['date'],
    #                 f"{result['salary']:.2f}",
    #                 f"{result['advance']:.2f}",
    #                 f"{result['total']:.2f}",
    #                 key=new_id
    #             )

    #     self.push_screen(InputDialog(is_edit=False), handle_result)

    @on(Button.Pressed, "#add")
    def action_add(self):
        def handle_result(result):
            if result:
                self.db.add_record(result["date"], result["amount"], result["category"])
                self._load_monthly_view()
        self.push_screen(AddRecordDialog(), handle_result)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        month_key = event.row_key.value  # например: "2025-03"
        breakdown = self.db.get_monthly_breakdown(month_key)
        self.push_screen(MonthDetailScreen(month_key, breakdown))

    @on(DataTable.RowSelected)
    def on_month_selected(self, event):
        month = event.row_key.value  # "2025-03"
        self.push_screen(MonthRecordsScreen(month))

    @on(Button.Pressed, "#delete")
    def action_delete(self):
        salaries_list = self.query_one(DataTable)
        row_key, _ = salaries_list.coordinate_to_cell_key(
            salaries_list.cursor_coordinate
        )

        def check_answer(accepted):
            if accepted and row_key:
                self.db.delete_financess(id_=row_key.value)
                salaries_list.remove_row(row_key)

        data = salaries_list.get_row(row_key)[0]
        self.push_screen(
            QuestionDialog(f"Вы действительно хотите удалить запись от {data}"),
            check_answer,
        )

    @on(Button.Pressed, "#change")
    def action_change(self):
        table = self.query_one(DataTable)
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        if not row_key:
            return

        current_data = table.get_row(row_key)
        date, salary, advance, total = [str(x) if isinstance(x, float) else x for x in current_data]

        def handle_update(result):
            if result and result['row_key']:
                # Обновляем БД
                self.db.update_financess(
                    id_=result['row_key'].value,
                    data=result['date'],
                    salary=result['salary'],
                    advance=result['advance'],
                    sum_=result['total']
                )

                # Обновляем таблицу
                table.remove_row(result['row_key'])
                table.add_row(
                    result['date'],
                    f"{result['salary']:.2f}",
                    f"{result['advance']:.2f}",
                    f"{result['total']:.2f}",
                    key=result['row_key'].value
                )

        self.push_screen(
            InputDialog(is_edit=True, current=current_data, row_key=row_key),
            handle_update
        )

    @on(Button.Pressed, "#settings")
    def action_open_settings(self):
        self.push_screen(OrgSettingsScreen())

    @on(Button.Pressed, "#about")
    def action_open_about(self):
        self.push_screen(AboutScreen())