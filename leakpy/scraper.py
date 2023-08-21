#!/usr/bin/python3

import sys
import json
import time
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from os import makedirs
from os.path import exists, expanduser, join


class LeakixScraper:

    def __init__(self, api_key=None, verbose=False):
        """
        Initialize the LeakixScraper instance.
        
        Args:
            api_key (str): The API key for Leakix. Defaults to None.
            verbose (bool): If True, print additional debug information. Defaults to False.
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
        Print log messages if verbose mode is enabled.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        if self.verbose:
            self.console.print(*args, **kwargs)

    def execute(self, scope="leak", query="", pages=2, plugin="", fields="protocol,ip,port"):
        """
        Execute the scraper.
        
        Args:
            scope (str): The scope of the search. Defaults to "leak".
            query (str): The query parameter. Defaults to "".
            pages (int): Number of pages to scrape. Defaults to 2.
            plugin (str): Comma-separated plugin names. Defaults to "".

        Returns:
            list: The scraped results.
        """
            
        plugins = self.get_plugins()
        given_plugins = [p.strip() for p in plugin.split(",") if p.strip()]

        plugin_names = {plugin_name for plugin_name, _ in plugins}
        invalid_plugins = [p for p in given_plugins if p not in plugin_names]
        if invalid_plugins:
            raise ValueError(f"Invalid plugins: {', '.join(invalid_plugins)}. Valid plugins: {plugins}")

        valid_plugins = given_plugins
        results = self.query(scope, pages, query, valid_plugins, fields)
        return results
    
    def get_plugins(self):
        """
        Fetch the list of available plugins from Leakix.

        Returns:
            list: A list of tuples where each tuple contains a plugin name and its access level.
        """
        plugins_url = 'https://leakix.net/plugins'
        response = requests.get(plugins_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        row_elements = soup.find_all('div', {'class': 'row'})

        plugins_dict = {}

        for row in row_elements:
            plugin_name_element = row.find('div', {'class': 'col-sm-3'})
            
            if plugin_name_element:
                plugin_name = plugin_name_element.find('a').text.strip()
                
                access_level_element = plugin_name_element.find_next_sibling('div', {'class': 'col-sm-3'})
                
                if access_level_element:
                    access_level = access_level_element.find('em').text.strip() if access_level_element.find('em') else "Unknown"
                    plugins_dict[plugin_name] = access_level

        plugins_list = [(plugin_name, access_level) for plugin_name, access_level in plugins_dict.items()]

        return plugins_list

    def save_api_key(self, api_key):
        """
        Save the provided API key to a file.
        
        Args:
            api_key (str): The API key to be saved.
        """
        with open(self.api_key_file, "w") as f:
            f.write(api_key)

    def read_api_key(self):
        """
        Read the API key from the file.
        
        Returns:
            str: The read API key or None if the file doesn't exist.
        """
        if not exists(self.api_key_file):
            return None

        with open(self.api_key_file, "r") as f:
            return f.read().strip()

    def extract_data_from_json(self, data, fields):
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

    
    def query(self, scope, pages=2, query_param="", plugins=None, fields=None):
        """
        Query the Leakix website and get results.
        
        Args:
            scope (str): The scope of the search.
            pages (int): Number of pages to scrape. Defaults to 2.
            query_param (str): The query parameter. Defaults to "".
            plugins (list or None): List of plugin names or a single plugin name. Defaults to None.
            fields (list of str or None): List of fields to extract from the JSON. 
                Each field can be a top-level key or a nested key separated by dots. Defaults to ["protocol", "ip", "port"].
            
        Returns:
            list of str: List of formatted strings extracted from the JSON.
        """
        if plugins:
            if isinstance(plugins, str):
                plugins = plugins.split(',')
            plugin_queries = [f"{plugin}" for plugin in plugins]
            query_param += " +plugin:(" + ' '.join(plugin_queries) + ")"

        results = []
        print(query_param)
        for page in range(pages):
            self.log(f"[bold green]\n[-] Query {page + 1} : \n")
            response = requests.get(
                "https://leakix.net/search",
                params={"page": str(page), "q": query_param, "scope": scope},
                headers={"api-key": self.api_key, "Accept": "application/json"},
            )

            if response.text == "null":
                self.log("[bold yellow][!] No more results available (Please check your query or scope)")
                break
            elif response.text == '{"Error":"Page limit"}':
                self.log(f"[bold red][X] Error : Page Limit for free users and non users ({page})")
                break

            try:
                data = json.loads(response.text)
                for json_data in data[1:]:
                    result_dict = self.extract_data_from_json(json_data, fields)
                    self.log(f"[bold white][+] {', '.join([f'{k}: {v}' for k, v in result_dict.items()])}") 
                    results.append(result_dict)
            except json.JSONDecodeError:
                self.log("[bold yellow][!] No more results available (Please check your query or scope)")
                break

            time.sleep(1.2)
        return results

    def run(self, scope, pages=2, query="", plugins=None, output=None, fields=None):
        """
        Main function to start the scraping process.
        
        Args:
            scope (str): The scope of the search.
            pages (int): Number of pages to scrape. Defaults to 2.
            query (str): The query parameter. Defaults to "".
            plugins (list or None): List of plugin names or a single plugin name. Defaults to None.
            output (str): The filename to save the scraped results. Defaults to None.
        """
        
        all_plugins = self.get_plugins()
        plugin_names = {plugin_name for plugin_name, _ in all_plugins}
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

