#!/usr/bin/python3

import sys
import argparse
import traceback
from rich.console import Console
from .scraper import LeakixScraper

def main():
    console = Console()
    
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--scope", choices=["service", "leak"], default="leak", help="Type Of Informations", type=str)
        parser.add_argument("-p", "--pages", help="Number Of Pages", default=2, type=int)
        parser.add_argument("-q", "--query", help="Specify The Query", default="", type=str)
        parser.add_argument("-P", "--plugins", help="Specify The Plugin(s)", type=str, default=None)
        parser.add_argument("-o", "--output", help="Output File", type=str)
        parser.add_argument("-f", "--fields", help="Fields to extract from the JSON, comma-separated. For example: 'protocol,ip,port'", type=str)
        parser.add_argument("-r", "--reset-api", action="store_true", help="Reset the saved API key")
        parser.add_argument("-lp", "--list-plugins", action="store_true", help="List Available Plugins")
       
        args = parser.parse_args()

        scraper = LeakixScraper(verbose=True)

        if args.reset_api:
            scraper.save_api_key("")  
            console.print("[bold green][+] API key has been reset.")
            sys.exit(0)

        if args.list_plugins:
            plugins = scraper.get_plugins()
            console.print(f"[bold yellow][!] Plugins available : {len(plugins)}\n")
            for plugin, access in plugins:
                console.print(f"[bold cyan][+] {plugin} - {access}")
            sys.exit(0)    
            
        scraper.run(args.scope, args.pages, args.query, args.plugins, args.output, args.fields)    
        
    except Exception as e:
        error_message = traceback.format_exc()
        console.print(f"\n[bold red][X] An error occurred: {e}\n")
        console.print(f"{error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
