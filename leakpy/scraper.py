#!/usr/bin/python3

import sys
import json
import time
import requests

from os import makedirs
from rich.console import Console
from os.path import exists, expanduser, join


class LeakixScraper:

    def __init__(self, api_key=None, verbose=False):
        """
        Initialize a new instance of the LeakixScraper.

        Args:
            api_key (str, optional): The API key for accessing Leakix services. Defaults to None.
            verbose (bool, optional): Flag to enable verbose logging. Defaults to False.
        """
        self.console = Console()
        user_folder = expanduser("~")
        local_folder = join(user_folder, ".local")
        makedirs(local_folder) if not exists(local_folder) else None
        self.api_key_file = join(local_folder, ".api.txt")
        self.api_key = api_key.strip() if api_key and len(api_key.strip()) == 48 else self.read_api_key()
        self.verbose = verbose

    def log(self, *args, **kwargs):
        """
        Log messages conditionally based on the verbose flag.

        Args:
            *args: Variable-length arguments to pass to the print function.
            **kwargs: Keyword arguments to pass to the print function.
        """
        if self.verbose:
            self.console.print(*args, **kwargs)
    
            
    def execute(self, scope="leak", query="", pages=2, plugin="", fields="protocol,ip,port"):
        """
        Execute the scraper to fetch data based on provided parameters.

        Args:
            scope (str, optional): The scope of the search. Defaults to "leak".
            query (str, optional): Search query string. Defaults to an empty string.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            plugin (str, optional): Comma-separated plugin names. Defaults to an empty string.
            fields (str, optional): Comma-separated list of fields to extract from results. Defaults to "protocol,ip,port".

        Returns:
            list: A list of scraped results based on the provided criteria.
        """
            
        plugins = self.get_plugins()
        given_plugins = [p.strip() for p in plugin.split(",") if p.strip()]

        plugin_names = {plugin_name for plugin_name in plugins}
        invalid_plugins = [p for p in given_plugins if p not in plugin_names]
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins}")

        valid_plugins = given_plugins
        results = self.query(scope, pages, query, valid_plugins, fields)
        return results
    
    def get_plugins(self):
        """
        Retrieve the list of available plugins from Leakix.

        Returns:
            list[str]: A list of available plugin names.
        """
        response = requests.get("https://leakix.net/api/plugins")
        plugins = json.loads(response.text)
        plugins_list = [plugin["name"] for plugin in plugins]
        return plugins_list

    def save_api_key(self, api_key):
        """
        Save the API key to a local file for later use.

        Args:
            api_key (str): The API key to be saved.
        """
        with open(self.api_key_file, "w") as f:
            f.write(api_key)

    def read_api_key(self):
        """
        Retrieve the API key from the local file.

        Returns:
            str or None: The stored API key or None if no key is found.
        """
        if not exists(self.api_key_file):
            return None

        with open(self.api_key_file, "r") as f:
            return f.read().strip()

    def extract_data_from_json(self, data, fields):
        """
        Extract specific fields from the provided JSON data.

        Args:
            data (dict): The JSON data from which fields are to be extracted.
            fields (str or None): Comma-separated list of fields to extract. 
                                  Each field can be a top-level key or a nested key separated by dots.

        Returns:
            dict: A dictionary with extracted field data.
        """
        if fields is None:
            fields_list = ["protocol", "ip", "port"]
        else:
            fields_list = [field.strip() for field in fields.split(',')]
        extracted_data = {}

        for field in fields_list:
            try:
                keys = field.split('.')
                value = data
                for key in keys:
                    value = value[key]
                extracted_data[field] = value
                    
            except (KeyError, TypeError):
                extracted_data[field] = "N/A"
        
        if fields_list == ["protocol", "ip", "port"]:
            protocol = data.get("protocol")
            if protocol in ["http", "https"]:
                return {'url': f"{protocol}://{data['ip']}:{data['port']}"}

        return extracted_data

    def get_all_fields(self, data, current_path=None):
        """
        Recursively retrieve all field paths from a nested dictionary.

        Args:
            data (dict): The nested dictionary to extract field paths from.
            current_path (list, optional): Current path being traversed. Defaults to None.

        Returns:
            list[str]: A list of field paths sorted alphabetically.
        """        
        fields = []
        if current_path is None:
            current_path = []
        
        if isinstance(data, dict):
            for key, value in sorted(data.items()):
                new_path = current_path + [key]
                if isinstance(value, dict):
                    fields.extend(self.get_all_fields(value, new_path))
                else:
                    fields.append('.'.join(new_path))
                    
        return sorted(fields)


    def query(self, scope, pages=2, query_param="", plugins=None, fields=None, return_data_only=False):
        """
        Perform a query on the Leakix website based on provided criteria.

        Args:
            scope (str): The scope of the search.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            query_param (str, optional): The query string to be used. Defaults to an empty string.
            plugins (list or str, optional): List or comma-separated string of plugin names. Defaults to None.
            fields (list of str or None, optional): List of fields to extract from the results. 
                                                   Each field can be a top-level key or nested key separated by dots.
            return_data_only (bool, optional): Return raw data only without processing. Defaults to False.

        Returns:
            list of str or dict: List of processed strings or raw data based on `return_data_only` flag.
        """
        data = []
        if plugins:
            if isinstance(plugins, str):
                plugins = plugins.split(',')
            plugin_queries = [f"{plugin}" for plugin in plugins]
            query_param += " +plugin:(" + ' '.join(plugin_queries) + ")"

        results = []
        for page in range(pages):
            self.log(f"[bold green]\n[-] Query {page + 1} : \n")
            response = requests.get(
                "https://leakix.net/search",
                params={"page": str(page), "q": query_param, "scope": scope},
                headers={"api-key": self.api_key, "Accept": "application/json"},
            )

            try:
                if not response.text:
                    break
                
                data = json.loads(response.text)
                if not data:
                    self.log("[bold yellow][!] No more results available (Please check your query or scope)")
                    break
                
                if isinstance(data, dict) and data.get('Error') == 'Page limit':
                    self.log(f"[bold red][X] Error : Page Limit for free users and non users ({page})")
                    break

                for json_data in data[1:]:
                    result_dict = self.extract_data_from_json(json_data, fields)
                    self.log(f"[bold white][+] {', '.join([f'{k}: {v}' for k, v in result_dict.items()])}") 
                    results.append(result_dict)

            except json.JSONDecodeError:
                self.log("[bold yellow][!] No more results available (Please check your query or scope)")
                break

            time.sleep(1.2)
            
        if return_data_only:
            return data    
        
        return results

    def run(self, scope, pages=2, query="", plugins=None, output=None, fields=None):
        """
        Initiate the scraping process based on provided criteria and optionally save results to a file.

        Args:
            scope (str): The scope of the search.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            query (str, optional): The query string for the search. Defaults to an empty string.
            plugins (list or str, optional): List or comma-separated string of plugin names. Defaults to None.
            output (str, optional): Path to the file where results should be saved. If None, results won't be saved. Defaults to None.
            fields (list of str or None, optional): List of fields to extract from results. Defaults to None.

        Returns:
            None: This method does not return any value.
        """
        
        all_plugins = self.get_plugins()
        plugin_names = {plugin_name for plugin_name in all_plugins}
        if plugins:
            if isinstance(plugins, str):
                plugins = plugins.split(',')
            for plugin in plugins:
                plugin = plugin.strip()
                if plugin not in plugin_names:
                    self.log(f"\n[bold red][X] Plugin '{plugin}' is not valid")
                    self.log(f"[bold yellow][!] Plugins available : {len(all_plugins)}\n")
                    for plugin_name, access in all_plugins:
                        self.log(f"[bold cyan][+] {plugin_name} - {access}")
                    sys.exit(1)

        if not self.api_key or len(self.api_key) != 48:
            self.api_key = input("Please Specify your API Key (leave blank if you don't have) : ")
            self.save_api_key(self.api_key)

        if not self.api_key:
            self.log(f"\n[bold yellow][!] Querying without API Key...\n (remove or edit {self.api_key_file} to add API Key if you have)")
        else:
            self.log("\n[bold green][+] Using API Key for queries...\n")

        results = self.query(scope, pages, query, plugins, fields)
        if output:
            with open(output, "a") as f:
                for result in results:
                    if not fields and 'url' in result:
                        f.write(f"{result['url']}\n")
                    else:
                        f.write(json.dumps(result) + "\n")
            self.log(f"\n[bold green][+] File written successfully to {output} with {len(results)} lines\n")

