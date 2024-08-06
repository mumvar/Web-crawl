import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import tkinter as tk
from tkinter import scrolledtext, StringVar, OptionMenu, Frame, BOTH
import csv

# Headers for web requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# List of sites to crawl
sites = ['https://extension.colostate.edu/topic-areas/agriculture/brooding-and-space-requirements-for-poultry-2-502/',
         'https://poultryassociationofnigeria.org/', 'https://panog.org.ng/',
         'https://babbangona.com/poultry-farming-in-nigeria-how-to-get-started/', 'https://lsetf.ng/content/setting-poultry-farm',
         'https://afrimash.com/poultry-vaccination-what-you-need-to-know/','https://en.wikipedia.org/wiki/Poultry',
         'https://www.thepoultrysite.com/articles/vaccine-administration-to-poultry-flocks']


# Function to extract text data from soup object, soup represents parsed html document
def extract_text(soup):
    info = []
    paragraphs = soup.find_all('p') # find all paragraph , result stored in paragraph list
    for p in paragraphs: # iterate through each paragraph found
        text = p.get_text(strip=True) # extract text, strip removes trailing and leading whitespaces, store in text variable
        info.append(text) # append extracted text to info
    return info # returns info list

# Function to extract table data from soup object
def extract_table_data(soup):
    tables = []
    table_elements = soup.find_all('table') # find all tables, store in table element
    for table in table_elements: # iterates through each table
        df = pd.read_html(str(table))[0]  # Convert table to string then read into DataFrame, [0] selects first dataframe
        tables.append(df) # Append dataframe to tables
    return tables

# Main crawling function
def crawl_sites(sites, search_term, max_retries=3):
    all_data = []
    for site in sites: # iterate through sites
        retries = 0 # initialize retries variable at 0
        while retries < max_retries: # checks condition
            try: # Try block to catch exceptions that may arise during http requests
                response = requests.get(site, headers=headers) # send http get request to site
                if response.status_code == 200:# checks if response statuus = 200, which signifies success
                    soup = BeautifulSoup(response.content, "html.parser") # parses content of response
                    info = extract_text(soup) # calls extract_text function to extract text from soup
                    tables = extract_table_data(soup) # calls extract_table_data function to extract table from soup
                    if info or tables: # checks if info or table contains data
                        all_data.append({ # Append dictionary containing the variables below
                            'url': site,
                            'text': info,
                            'table_data': tables
                        })
                    break  # Break out of the retry loop on success
                else: # if status code not 200
                    print(f"Failed to retrieve {site}. Status code: {response.status_code}") # prints error message
                    break  # Exit the retry loop on non-200 status codes
            except requests.exceptions.RequestException as e: # catches any exception raised during http request
                retries += 1 # increment retries by 1
                print(f"Error fetching {site}: {str(e)}. Retrying ({retries}/{max_retries})...") # prints error message with url, exception message and retries amount
                time.sleep(random.uniform(1, 3))  # Wait before retrying, Pauses execution for a random duration between 1,3 seconds
    return all_data

# Function to crawl, save, and display results based on the selected keyword
def crawl_and_save(keyword):
    search_term = keyword.lower()  # Lowercase for case-insensitive search
    all_data = crawl_sites(sites, search_term) # calls crawl site function, passing in sites and search term
    filtered_data = []
    for data in all_data: # iterate through all data
        text_found = any(search_term in text.lower() for text in data['text']) # checks if search term is present in any text content in data list, stores True/False in text_found variable
        table_found = any(any(search_term in str(cell).lower() for cell in table.values.flatten()) for table in data['table_data']) # checks if search term is present in any cell
        
        if text_found or table_found: # checks if text_found or table_found is true
            filtered_data.append({ # if found , appends a dictionary to filtered data 
                'url': data['url'],
                'text': "\n".join(data['text']),  # Join paragraphs with newline for CSV storage
                'table_data': [table.to_csv(index=False) for table in data['table_data'] if any(search_term in str(cell).lower() for cell in table.values.flatten())]
                # a list of csv strings for each table where search term is found
            })
    
    if filtered_data: # if filtered data contains any element 
        save_to_csv(filtered_data, search_term) # calls save to csv function
        display_results(filtered_data) # calls display results function
    else:
        result_text.config(state=tk.NORMAL) # configures result text to a normal state
        result_text.delete(1.0, tk.END) # deletes any existing text in result text widget
        result_text.insert(tk.INSERT, f"No data found for search term '{keyword}'") # insert message into result text
        result_text.config(state=tk.DISABLED) # configure result text disabled, which is read only mode 



# Function to save filtered data to CSV based on keyword
def save_to_csv(data, keyword, filename="crawl_data.csv"):
    # Determine filename based on keyword
    if keyword == 'vaccine':
        filename = 'vaccine_data.csv'
    elif keyword == 'temperature':
        filename = 'temperature_data.csv'
    elif keyword == 'brooding':
        filename = 'brooding_data.csv'
    elif keyword == 'space':
        filename = 'space_data.csv'
    elif keyword == 'disease':
        filename = 'disease_data.csv'
    # with as a context manager
    with open(filename, mode='w', newline='', encoding='utf-8') as file: # opens filename in write mode, nweline = ' ' to prevent additional newlines,utf-8 to handle unicode characters
        fieldnames = ['url', 'text', 'table_data'] # Defines fieldnames for csv
        writer = csv.DictWriter(file, fieldnames=fieldnames) # csv.dictwriter writes dictionary to csv file
        writer.writeheader() # writes the header row
        for entry in data: # iterate through data list
            writer.writerow({ # writes row to the csv file for each entry
                'url': entry['url'],
                'text': entry['text'],
                'table_data': "\n".join(entry['table_data']) if entry['table_data'] else None
            })
    print(f"Data saved to '{filename}'")

# Function to display results in the ScrolledText widget
def display_results(data):
    results = []
    for entry in data: # iterates through data
        results.append(f"URL: {entry['url']}\n")
        results.append("Text Data:\n")
        results.append(entry['text'])
        results.append("\nTable Data:\n")
        if entry['table_data']:
            results.extend(entry['table_data'])
        results.append("\n\n")
    
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.INSERT, "\n".join(results))
    result_text.config(state=tk.DISABLED)

# GUI setup
def create_gui():
    root = tk.Tk()
    root.title("KNOW ABOUT POULTRY")

    # Create the main frame
    main_frame = Frame(root)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10) # expand to fill entire window

    # Dropdown menu for keyword selection
    keyword_var = StringVar(root) # store slected keyword in dropdown menu
    keyword_var.set('SELECT')  # Default value
    keywords = ['vaccine', 'temperature', 'brooding', 'space', 'disease']
    tk.Label(main_frame, text="SELECT WHAT YOU NEED TO KNOW ABOUT YOUR POULTRY:\n CRAWL AND DISPLAY TO VIEW:").pack(pady=5)
    keyword_menu = OptionMenu(main_frame, keyword_var, *keywords) # widget that allows user to select keyword from keywords and assigns it to keyword var
    keyword_menu.pack(pady=5)

    # Button to start crawling
    button_crawl = tk.Button(main_frame, text="Crawl and Display", command=lambda: crawl_and_save(keyword_var.get())) # button that calls crawl and save function, with currently selected keyword
    button_crawl.pack(pady=10)

    # Frame to hold the ScrolledText widget
    text_frame = Frame(main_frame)
    text_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

    # ScrolledText widget to display results
    global result_text # declares result text as global to be used by other functions
    result_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD) # initializes result text as  a scrolled text widget
    result_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

    root.mainloop()

create_gui()
