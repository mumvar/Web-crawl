import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import tkinter as tk
from tkinter import scrolledtext
import csv

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
sites = ['https://extension.colostate.edu/topic-areas/agriculture/brooding-and-space-requirements-for-poultry-2-502/',
         'https://poultryassociationofnigeria.org/', 'https://panog.org.ng/',
         'https://babbangona.com/poultry-farming-in-nigeria-how-to-get-started/', 'https://lsetf.ng/content/setting-poultry-farm']

# Placeholder functions for extracting text and table data
def extract_text(soup, search_term):
    info = []
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        if search_term.lower() in text.lower():
            info.append(text)
    return info

def extract_table_data(soup, search_term):
    tables = []
    table_elements = soup.find_all('table')
    for table in table_elements:
        df = pd.read_html(str(table))[0]  # convert table into DataFrame
        if df.applymap(lambda x: search_term.lower() in str(x).lower()).any().any():
            tables.append(df)
    return tables

def crawl_sites(sites, search_term, max_retries=3):
    all_data = []
    for site in sites:
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(site, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    info = extract_text(soup, search_term)
                    tables = extract_table_data(soup, search_term)
                    if info or tables:
                        all_data.append({
                            'url': site,
                            'info': info,
                            'tables': tables
                        })
                    break  # Break out of the retry loop on success
                else:
                    print(f"Failed to retrieve {site}. Status code: {response.status_code}")
                    break  # Exit the retry loop on non-200 status codes
            except requests.exceptions.RequestException as e:
                retries += 1
                print(f"Error fetching {site}: {str(e)}. Retrying ({retries}/{max_retries})...")
                time.sleep(random.uniform(1, 3))  # Wait before retrying
    return all_data

def crawl():
    search_term = entry_term.get()
    results = []
    all_data = crawl_sites(sites, search_term)
    for data in all_data:
        if search_term.lower() in " ".join(data['info']).lower():
            results.append(f"Term '{search_term}' found in {data['url']}")
        else:
            results.append(f"Term '{search_term}' not found in {data['url']}")
        
        for table in data['tables']:
            results.append(f"Table data from {data['url']}:")
            for row in table.itertuples(index=False):
                results.append("\t" + " | ".join(map(str, row)))
    
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.INSERT, "\n".join(results))
    result_text.config(state=tk.DISABLED)
    save_to_csv(all_data)

def save_to_csv(data, filename="crawl_data.csv"):
    all_data = []
    for entry in data:
        for df in entry['tables','p']:
            all_data.append(df)
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.to_csv(filename, index=False)
        print(f"Data saved to '{filename}'")
    else:
        print("No tables found to save.")

def print_csv(textbox):
    textbox.delete('1.0', tk.END)
    csv_file = "crawl_data.csv"
    try:
        df = pd.read_csv(csv_file)
        textbox.insert(tk.END, df.to_string(index=False))  # Displaying as a string without index
    except Exception as e:
        textbox.insert(tk.END, f"Error reading CSV file: {str(e)}")

# GUI setup
def create_gui():
    root = tk.Tk()
    root.title("Web Crawler GUI")
    tk.Label(root, text="Enter Search Term:").pack(pady=5)
    global entry_term
    entry_term = tk.Entry(root, width=50)
    entry_term.pack(pady=5)
    button_crawl = tk.Button(root, text="Crawl", command=crawl)
    button_crawl.pack(pady=10)
    global result_text
    result_text = scrolledtext.ScrolledText(root, width=80, height=20, state=tk.DISABLED)
    result_text.pack(pady=10)
    
    # CSV Viewer Section
    textbox = tk.Text(root, height=20, width=80)
    textbox.pack(padx=10, pady=10)
    button_check = tk.Button(root, text="Check Data", command=lambda: print_csv(textbox))
    button_check.pack(pady=5)

    root.mainloop()

create_gui()
