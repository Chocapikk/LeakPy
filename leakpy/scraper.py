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
        self.verbose = verbose
        user_folder = expanduser("~")
        local_folder = join(user_folder, ".local")
        makedirs(local_folder) if not exists(local_folder) else None
        self.api_key_file = join(local_folder, ".api.txt")
        
        if api_key:
            self.api_key = api_key.strip()
            self.save_api_key(self.api_key)
        else:
            self.api_key = self.read_api_key()
        
        self.is_api_pro = None

    def api_check_privilege(self, plugin, scope):
        """Check if the API is pro using a specific plugin and scope."""
        response = requests.get(
            "https://leakix.net/search",
            params={"page": "1", "q": plugin, "scope": scope},
            headers={"api-key": self.api_key, "Accept": "application/json"},
        )

        return bool(response.text)

    
    def has_api_key(self):
        """
        Check if an API key is available and valid (48 characters).

        Returns:
            bool: True if API key is valid, False otherwise.
        """
        self.api_key = self.read_api_key()
        if not self.api_key:
            return False
        return len(self.api_key) == 48
 
    
    def log(self, *args, **kwargs):
        """
        Log messages conditionally based on the verbose flag.

        Args:
            *args: Variable-length arguments to pass to the print function.
            **kwargs: Keyword arguments to pass to the print function.
        """
        if self.verbose:
            self.console.print(*args, **kwargs)
    
    def process_and_print_data(self, data, fields):
        """
        Process the provided data, extract desired fields, and print the results.

        Args:
            data (list or dict): Either a list of dictionaries or a single dictionary, typically JSON data to be processed.
            fields (str or None): Comma-separated list of fields to extract. 
                                Each field can be a top-level key or a nested key separated by dots.

        Returns:
            list: A list of dictionaries containing the extracted fields from the data.
            
        Note:
            This method also logs the extracted data in a formatted manner.
        """
        results = []

        if not isinstance(data, list):
            data = [data]

        for json_data in data:
            result_dict = self.extract_data_from_json(json_data, fields)
            self.log(f"[bold white][+] {', '.join([f'{k}: {v}' for k, v in result_dict.items()])}")
            results.append(result_dict)
        return results

        
    def execute(self, scope="leak", query="", pages=2, plugin="", fields="protocol,ip,port", use_bulk=False):
        """
        Execute the scraper to fetch data based on provided parameters.

        Args:
            scope (str, optional): The scope of the search. Defaults to "leak".
            query (str, optional): Search query string. Defaults to an empty string.
            pages (int, optional): Number of pages to scrape. Defaults to 2.
            plugin (str, optional): Comma-separated plugin names. Defaults to an empty string.
            fields (str, optional): Comma-separated list of fields to extract from results. Defaults to "protocol,ip,port".
            use_bulk (bool, optional): Whether to use the bulk functionality. Defaults to False.
            
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
        results = self.query(scope, pages, query, valid_plugins, fields, use_bulk)
        return results
    
    def get_plugins(self):
        """
        Retrieve the list of available plugins from Leakix.

        Returns:
            list[str]: A list of available plugin names.
        """
        try:
            response = requests.get("https://leakix.net/api/plugins")
            response.raise_for_status()
            
            plugins = json.loads(response.text)
            plugins_list = [plugin["name"] for plugin in plugins]
            return plugins_list
        except (requests.RequestException, json.JSONDecodeError):
            return []

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
            data (dict or list of dicts): The JSON data from which fields are to be extracted.
            fields (str or None): Comma-separated list of fields to extract. 
                                Each field can be a top-level key or a nested key separated by dots.

        Returns:
            dict or list of dicts: A dictionary or a list of dictionaries with extracted field data.
        """
        if fields is None:
            fields_list = ["protocol", "ip", "port"]
        else:
            fields_list = [field.strip() for field in fields.split(',')]
        
        def extract_from_single_entry(entry):
            extracted_data = {}
            for field in fields_list:
                try:
                    keys = field.split('.')
                    value = entry
                    for key in keys:
                        value = value[key]
                    extracted_data[field] = value
                        
                except (KeyError, TypeError):
                    extracted_data[field] = "N/A"
            
            if fields_list == ["protocol", "ip", "port"]:
                protocol = entry.get("protocol")
                if protocol in ["http", "https"]:
                    return {'url': f"{protocol}://{entry['ip']}:{entry['port']}"}
            
            return extracted_data

        if "events" in data and isinstance(data["events"], list):
            return [extract_from_single_entry(event) for event in data["events"]]

        return extract_from_single_entry(data)


    def list_fields(self):
        """
        Lists all possible fields from a sample JSON retrieved from the API.
        This is a wrapper around the get_all_fields method to fetch and process a sample JSON.
        """
        self.verbose = not self.verbose
        sample_data = self.query(scope="leak", pages=1, return_data_only=True)
        self.verbose = not self.verbose
        
        if not sample_data or not isinstance(sample_data, list) or not sample_data:
            self.log("[bold red]Failed to retrieve a sample JSON. Cannot list fields.")
            return []

        return self.get_all_fields(sample_data[0])


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


    def query(self, scope, pages=2, query_param="", plugins=None, fields=None, use_bulk=False, return_data_only=False):
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
        
        if not self.has_api_key():
            raise ValueError("A valid API key is required.")
        
        if self.is_api_pro is None:
            self.is_api_pro = self.api_check_privilege("WpUserEnumHttp", "leak")
            
        data = []
        if plugins:
            if isinstance(plugins, str):
                plugins = plugins.split(',')
            plugin_queries = [f"{plugin}" for plugin in plugins]
            query_param += " +plugin:(" + ' '.join(plugin_queries) + ")"

        if self.is_api_pro and use_bulk:
            self.log("[bold green][-] Opting for bulk search due to the availability of a Pro API Key.")
            response = requests.get(
                "https://leakix.net/bulk/search",
                params={"q": query_param},
                headers={"api-key": self.api_key},
            )
            
            try:
                loaded_data = [json.loads(line) for line in response.text.strip().split("\n") if line.strip()]
                data = [item.get('events', []) for item in loaded_data if isinstance(item, dict) and 'events' in item]
                data = [event for sublist in data for event in sublist]

                if not data:
                    self.log("[bold yellow][!] No results returned from bulk query.")
                    return []

                if return_data_only:
                    return data

                return self.process_and_print_data(data, fields)

            except json.JSONDecodeError:
                self.log("[bold yellow][!] Error processing bulk query response.")
                return []
        
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

                results.extend(self.process_and_print_data(data[1:], fields))

            except json.JSONDecodeError:
                self.log("[bold yellow][!] No more results available (Please check your query or scope)")
                break

            time.sleep(1.2)
            
        if return_data_only:
            return data    
        
        return results

    def run(self, scope, pages=2, query="", plugins=None, output=None, fields=None, use_bulk=False):
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
                    for plugin_name in all_plugins:
                        self.log(f"[bold cyan][+] {plugin_name}")
                    sys.exit(1)
        
        self.log("\n[bold green][+] Using API Key for queries...\n")
          
        results = self.query(scope, pages, query, plugins, fields, use_bulk)
        
        if output:
            with open(output, "a") as f:
                for result in results:
                    if not fields and 'url' in result:
                        f.write(f"{result['url']}\n")
                    else:
                        f.write(json.dumps(result) + "\n")
            self.log(f"\n[bold green][+] File written successfully to {output} with {len(results)} lines\n")

