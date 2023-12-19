from telethon.sync import TelegramClient
import telethon

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import configparser
import multiprocessing

import time
import pandas as pd

console = Console()


class Cleaner:
    def __init__(self, client):
        self.client = client
        self.channel_name = ""
        self.channel = None
        self.sub_count = 100

    def get_channel(self):
        self.channel_name = Prompt.ask("\n[bold]Enter a channel name")

        for dialog in self.client.iter_dialogs():
            if dialog.is_channel and dialog.title == self.channel_name:
                print(f"[bold #01AC9F]Selected Channel: {dialog.title}")
                self.channel = self.client.get_entity(dialog.id)
        return self.channel_name, self.channel

    def count_subs(self):
        self.sub_count = self.client.get_stats(self.channel).followers.current
        return self.sub_count

    def kick_subs(self):
        print(
            "\n[bold]Please provide comma-separated IDs\n[italic]Example 1: 1234567890\nExample 2: 1234567890,1234567891,1234567892\n"
        )
        id_input = Prompt.ask("Input IDs")
        ids = id_input.split(",")
        for id in ids:
            user = self.client.get_entity(id)
            self.client.kick_participant(self.channel, user)
            if user.username:
                print(user.username, "removed")
            else:
                print(user.first_name, "removed")
            time.sleep(3)

        print("Completed!")

    def list_subs(self):
        allSubscribers = []
        count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold green]Extracting Subscribers..."),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        ) as progress:
            extraction_task = progress.add_task("", total=self.sub_count)

            for subscriber in self.client.iter_participants(
                self.channel,
                limit=10000,
                aggressive=True,
            ):
                allSubscribers.append(subscriber)
                count += 1

                # Update progress bar
                progress.update(extraction_task, advance=1)

                # Countermeasure against flood error
                if count == 250:
                    time.sleep(30)
                    count = 0

        # Extract attributes from each object
        data = []
        for obj in allSubscribers:
            obj_attributes = vars(obj)
            data.append(obj_attributes)

        # Create DataFrame
        df = pd.DataFrame(data)
        print(df)
        df.to_excel(f"{self.channel_name}.xlsx", index=False)


def get_api_credentials():
    config = configparser.ConfigParser()

    try:
        config.read("config.ini")
        api_id = config.get("API", "id")
        api_hash = config.get("API", "hash")

        print("\n[green]API ID and hash found! Logging in...")

    except (configparser.NoSectionError, configparser.NoOptionError):
        print("[red]API ID and hash not found. Please enter your credentials!")
        api_id = Prompt.ask("API ID")
        api_hash = Prompt.ask("API Hash")

        config["API"] = {"id": api_id, "hash": api_hash}
        with open("config.ini", "w") as configfile:
            config.write(configfile)

    return api_id, api_hash


def main():
    print(
        Panel(
            "\n[bold]Available Commands:[/bold]\n\n[bold #007C24]list[/bold #007C24] - Generate an excel file with a list of current subscribers in a Telegram channel\n\n[bold #007C24]kick[/bold #007C24] - Input a list of subscribers by ID to remove them in bulk\n\n[bold #007C24]change[/bold #007C24] - Select a different Telegram channel\n\n[bold #007C24]exit[/bold #007C24] - Exit the program :wave:\n",
            title="[bold green]Telegram Channel Cleaner[/bold green]",
            subtitle="[italic]v1.0",
        )
    )

    api_id, api_hash = get_api_credentials()

    with TelegramClient("name", api_id, api_hash) as client:
        cleaner = Cleaner(client)
        cleaner.get_channel()

        while True:
            command = Prompt.ask(
                "\n[bold]Enter a command", choices=["list", "kick", "change", "exit"]
            )

            if command == "list":
                cleaner.count_subs()
                cleaner.list_subs()
            elif command == "kick":
                cleaner.kick_subs()
            elif command == "change":
                cleaner.get_channel()
            elif command == "exit":
                print("\n")
                exit()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
