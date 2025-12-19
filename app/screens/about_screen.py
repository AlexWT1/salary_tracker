# app/screens/about_screen.py
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label
from textual import work
import webbrowser
import httpx
from app.constants import APP_NAME, APP_VERSION, GITHUB_REPO

# 🔴 ИСПРАВЛЕНО: УБРАНЫ ПРОБЕЛЫ В URL!
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"

class AboutScreen(ModalScreen):
    DEFAULT_CSS = """
    #about-dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 1 2;
        width: 60;
        height: 30;
        border: thick $primary;
        background: $surface;
    }
    #about-title {
        column-span: 2;
        text-align: center;
        color: $success;
        text-style: bold;
    }
    #update-status {
        column-span: 2;
        text-align: center;
    }
    #buttons {
        column-span: 2;
        align: center middle;
        height: 10;
    }
    .about-button {
        margin: 0 1;
        /* Убран color: white — пусть тема сама решает */
    }
    """

    def compose(self):
        yield Grid(
            Label(f"{APP_NAME} v{APP_VERSION}", id="about-title"),
            Label("Нажмите 'Проверить', чтобы найти обновления", id="update-status"),
            Grid(
                Button("Проверить", id="check", variant="primary", classes="about-button"),
                Button("Открыть релиз", id="open", variant="success", disabled=True, classes="about-button"),
                Button("Закрыть", id="close", variant="default", classes="about-button"),
                id="buttons"
            ),
            id="about-dialog"
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "close":
            self.dismiss()
        elif event.button.id == "open":
            webbrowser.open(GITHUB_RELEASES_PAGE)
        elif event.button.id == "check":
            self.check_updates()

    @work
    async def check_updates(self):
        status = self.query_one("#update-status", Label)
        check_btn = self.query_one("#check", Button)
        open_btn = self.query_one("#open", Button)

        try:
            check_btn.disabled = True
            status.update("Проверка...")
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(GITHUB_API_URL)
                resp.raise_for_status()
                latest = resp.json()
                latest_tag = latest["tag_name"].lstrip("v")
                current = APP_VERSION.lstrip("v")

                if latest_tag != current:
                    status.update(f"[green]Доступна новая версия: {latest_tag}[/]")
                    open_btn.disabled = False
                else:
                    status.update("[dim]У вас последняя версия[/]")
        except (httpx.ConnectTimeout, httpx.NetworkError):
            status.update("[red]Нет подключения к интернету[/]")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                status.update("[red]Репозиторий не найден (404)[/]")
            else:
                status.update(f"[red]Ошибка GitHub: {e.response.status_code}[/]")
        except Exception as e:
            status.update(f"[red]Ошибка: {type(e).__name__}[/]")
        finally:
            check_btn.disabled = False