import time
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table

from typing import Union, Optional, List, Dict


class RichLogger:
    def __init__(self):
        self.console = Console()

    def log(self, message, style="bold cyan", delay=0.01):
        live_text = Text(style=style)
        with Live(live_text, console=self.console, refresh_per_second=30, transient=False):
            for char in message:
                live_text.append(char)
                time.sleep(delay)
        self.console.print()

    def panel(self, title, content, style="bold green"):
        panel = Panel(content, title=title, title_align="left", border_style=style)
        self.console.print(panel)
    
    def table(self, title, data):
        from rich.table import Table

        table = Table(title=title, show_header=True, header_style="bold magenta")

        if isinstance(data, dict):
            # Tek bir dict ise basit key-value tablosu
            table.add_column("Key", style="cyan", width=20)
            table.add_column("Value", style="green")
            for key, value in data.items():
                table.add_row(str(key), str(value))
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # Liste içindeki tüm dict'lerin key'lerini topla
            keys = list({k for row in data for k in row.keys()})

            table.add_column("No", style="bold yellow", justify="right")  # sıra numarası kolonu
            for key in keys:
                table.add_column(str(key), style="cyan")

            for idx, row in enumerate(data, start=1):
                row_values = [str(row.get(key, "")) for key in keys]
                table.add_row(str(idx), *row_values)
        else:
            self.console.print("[red]ERROR: Invalid data format for table. Must be dict or list of dicts.")
            return

        self.console.print(table)
    
    def prompt_panel(self, question: str, choices: Optional[List[int]] = None, default: Optional[int] = None) -> int:
        while True:
            value = Prompt.ask(question, default=default, console=self.console)
            
            try:
                value = int(value)
            except ValueError:
                value = None 

            if choices and value not in choices:
                self.panel(
                    title="ERROR",
                    content=f"Invalid input! Please enter one of the following values: {', '.join(str(choices))}",
                    style="bold red"
                )
            else:
                break
        return value

    
    def show_panel(self, title: str, content: str, style: str = "bold green"):
        panel = Panel(content, title=title, title_align="left", border_style=style)
        self.console.print(panel)

    def prompt_input(self, question: str, default: Optional[str] = None) -> str:
        value = Prompt.ask(question, default=default, console=self.console)
        return value

    def prompt_choice(self, question: str, choices: List[str], default: Optional[str] = None) -> str:
        value = Prompt.ask(
            question,
            choices=choices,
            default=default,
            show_choices=True,
            console=self.console
        )
        return value

    def clear(self):
        self.console.clear()
