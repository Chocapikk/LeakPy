#!/usr/bin/python3

import sys
import argparse
import traceback

from . import __version__
from rich.console import Console
from .scraper import LeakixScraper
from collections import defaultdict
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

def display_help(console):
    commands = {
        'exit': 'Exit the interactive mode.',
        'help': 'Display this help menu.',
        'set': 'Set a particular setting. Usage: set <setting_name> <value>',
        'run': 'Run the scraper with the current settings.',
        'list-fields': 'List all possible fields from a sample JSON.',
        'list-plugins': 'List available plugins.',
        'show': 'Display current settings.',
    }

    console.print("[bold yellow]Available Commands:[/bold yellow]")
    for command, desc in commands.items():
        console.print(f"[bold cyan]{command.ljust(15)}[/bold cyan]: {desc}")


def interactive_mode():
    console = Console()
    scraper = LeakixScraper(verbose=True)
    
    settings = {
        "scope": "leak",
        "pages": 2,
        "query": "",
        "plugins": None,
        "output": None,
        "fields": None,
        "use_bulk": False
    }

    commands = {
        'show': lambda args: show_command(console, settings),
        'exit': lambda args: console.print("[bold green]Exiting interactive mode. Goodbye!") or 'exit',
        'help': lambda args: display_help(console),
        'set': lambda args: set_command(console, settings, args),
        'run': lambda args: scraper.run(settings["scope"], int(settings["pages"]), settings["query"], settings["plugins"], settings["output"], settings["fields"], bool(settings["use_bulk"])),
        'list-fields': lambda args: list_fields_command(console, scraper),
        'list-plugins': lambda args: list_plugins_command(console, scraper)
    }

    session = PromptSession(history=InMemoryHistory(), auto_suggest=AutoSuggestFromHistory())

    console.print("[bold green]Welcome to LeakPy interactive mode!")
    console.print("[bold blue]Type 'help' for available commands.")

    while True:
        try:
            cmd_line = session.prompt(HTML('<bold><magenta>LeakPy > </magenta></bold>'))
            args = cmd_line.strip().split()
            
            cmd = args.pop(0).lower() if args else None

            if cmd in commands:
                result = commands[cmd](args)
                if result == 'exit':
                    break
            else:
                console.print(f"[bold red]Unknown command: {cmd}. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted by user. Type 'exit' to leave or 'help' for available commands.")
        
        except Exception as e:
            console.print(f"[bold red]Error: {e}")

def set_command(console, settings, args):
    if len(args) >= 2:
        key = args[0]
        value = ' '.join(args[1:])

        if key == "use_bulk":
            value = value.lower() == "true"

        if key in settings:
            settings[key] = value
            console.print(f"[bold cyan]{key}[/bold cyan] set to [bold magenta]{value}[/bold magenta].")
        else:
            console.print(f"[bold red]Unknown setting: {key}. Use 'show' to view available settings.")
    else:
        console.print("[bold red]Usage: set <setting_name> <value>")


def show_command(console, settings):
    console.print("\n[bold magenta]Current Settings:[/bold magenta]\n")
    for key, value in settings.items():
        console.print(f"[bold cyan]{key}:[/bold cyan][bold magenta] {value}[/bold magenta]")
    console.print("\n")    

def organize_fields(fields):
    organized = defaultdict(list)
    
    for field in fields:
        parts = field.split('.')
        if len(parts) > 1:
            organized[parts[0]].append('.'.join(parts[1:]))
        else:
            organized["general"].append(parts[0])
            
    return organized

def list_fields_command(console, scraper):
    fields = scraper.list_fields()
    if fields:
        organized_fields = organize_fields(fields)
        
        console.print("\n[bold white]Available Fields:\n[/bold white]")
        for category, items in organized_fields.items():
            console.print(f"[bold magenta]{category}[/bold magenta]")
            for item in items:
                console.print(f"[bold cyan]- {item}[/bold cyan]")
            console.print() 
    else:
        console.print("[bold red]Failed to list fields.[/bold red]")

def list_plugins_command(console, scraper):
    plugins = scraper.get_plugins()
    if plugins:
        console.print("\n[bold white]Available Plugins:[/bold white]\n")
        for plugin in plugins:
            console.print(f"[bold cyan]- {plugin}[/bold cyan]")
    else:
        console.print("[bold red]Failed to list plugins.[/bold red]")


    
    
def main():
    console = Console()
    console.print("[bold magenta][~] LeakPy " + __version__ + "[/bold magenta]")
    
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--scope", choices=["service", "leak"], default="leak", help="Type Of Informations", type=str)
        parser.add_argument("-p", "--pages", help="Number Of Pages", default=2, type=int)
        parser.add_argument("-q", "--query", help="Specify The Query", default="", type=str)
        parser.add_argument("-P", "--plugins", help="Specify The Plugin(s)", type=str, default=None)
        parser.add_argument("-o", "--output", help="Output File", type=str)
        parser.add_argument("-f", "--fields", help="Fields to extract from the JSON, comma-separated. For example: 'protocol,ip,port'", type=str)
        parser.add_argument("-b", "--bulk", action="store_true", help="Activate bulk mode.")
        parser.add_argument("-i", "--interactive", action="store_true", help="Activate interactive mode.")
        parser.add_argument("-r", "--reset-api", action="store_true", help="Reset the saved API key")
        parser.add_argument("-lp", "--list-plugins", action="store_true", help="List Available Plugins")
        parser.add_argument("-lf", "--list-fields", action="store_true", help="List all possible fields from a sample JSON")
        parser.add_argument("-v", "--version", action="version", version="LeakPy " + __version__)

        args = parser.parse_args()

        scraper = LeakixScraper(verbose=True)

        if not scraper.has_api_key():
            session = PromptSession()
            console.print("[bold yellow]API key is missing. Please enter your API key to continue.[/bold yellow]")
            api_key = session.prompt(HTML('<ansibold><ansiwhite>API Key:</ansiwhite></ansibold> '), is_password=True).strip()
            scraper.save_api_key(api_key)

            if not scraper.has_api_key():
                console.print("[bold red]The provided API key is invalid. It must be 48 characters long.[/bold red]")
                sys.exit(1)            
                
        if args.interactive:
            interactive_mode()
            sys.exit(0)
            
        if args.reset_api:
            scraper.save_api_key("")  
            console.print("[bold green][+] API key has been reset.")
            sys.exit(0)

        if args.list_plugins:
            plugins = scraper.get_plugins()
            console.print(f"[bold yellow][!] Plugins available : {len(plugins)}\n")
            for plugin in plugins:
                console.print(f"[bold cyan][+] {plugin}")
            sys.exit(0)    
        
        if args.list_fields:
            scraper.verbose = not scraper.verbose
            sample_data = scraper.query(args.scope, 1, args.query, args.plugins, None, return_data_only=True)
            scraper.verbose = not scraper.verbose
            
            if not sample_data or not isinstance(sample_data, list) or not sample_data[0]:
                console.print("[bold red][X] Couldn't fetch valid sample data. (Please check your query, scope or plugins)")
                sys.exit(1)

            sample_dict = sample_data[0]
            
            fields = scraper.get_all_fields(sample_dict)
            console.print(f"[bold yellow][!] Possible fields from sample JSON : {len(fields)}\n")
            for field in fields:
                console.print(f"[bold cyan][+] {field}")
            sys.exit(0)

        
        scraper.run(args.scope, args.pages, args.query, args.plugins, args.output, args.fields, args.bulk)    
        
    except Exception as e:
        error_message = traceback.format_exc()
        console.print(f"\n[bold red][X] An error occurred: {e}\n")
        console.print(f"{error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
