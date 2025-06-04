import json
import pandas as pd
import os
from urllib.parse import urlparse

# Define the path to your input JSON file
INPUT_ARTICLES_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_aggregated_articles.json"
# Define the path for the output Excel file
OUTPUT_EXCEL_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\source_mapping_template.xlsx"


def load_json_file(filepath):
    """Loads JSON data from a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} articles from {filepath}")
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. File might be corrupted or empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading articles: {e}")
        return None

def get_unique_source_urls(articles):
    """Extracts all unique source URLs from the loaded articles."""
    unique_urls = {article.get('source_url') for article in articles if article.get('source_url')}
    # Filter out any None values if they somehow crept in and sort for consistency
    return sorted([url for url in list(unique_urls) if url is not None])

def main():
    # 1. Load the articles from the JSON file you provided
    articles = load_json_file(INPUT_ARTICLES_FILE)
    if articles is None:
        return

    # 2. Get unique source URLs from the loaded articles
    unique_urls = get_unique_source_urls(articles)
    print(f"Extracted {len(unique_urls)} unique source URLs from your JSON file.")

    # --- DEBUG PRINT: Show the actual unique URLs found ---
    print("\n--- Unique URLs found in the JSON file (for debugging) ---")
    for i, url in enumerate(unique_urls):
        print(f"{i+1}. {url}")
    print("----------------------------------------------------------\n")
    # --- END DEBUG PRINT ---

    # 3. Prepare data for DataFrame
    data_for_excel = []
    for url in unique_urls:
        data_for_excel.append({
            'Source URL': url,
            'Base Domain': urlparse(url).netloc.replace('www.', ''), # Helpful for quick reference
            'Tribe': '', # Placeholder for manual entry
            'Region': ''  # Placeholder for manual entry
        })

    # 4. Create a Pandas DataFrame
    df = pd.DataFrame(data_for_excel)

    # 5. Save the DataFrame to an Excel file
    output_dir = os.path.dirname(OUTPUT_EXCEL_FILE)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        except OSError as e:
            print(f"Error creating directory {output_dir}: {e}")
            print("Cannot save Excel file. Please check permissions or path.")
            return

    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False, engine='openpyxl')
        print(f"\nSuccessfully created Excel file: {OUTPUT_EXCEL_FILE}")
        print(f"This Excel file contains {len(unique_urls)} unique source URLs.")
        print("Please open this Excel file, fill in the 'Tribe' and 'Region' columns, and save it.")
        print("We will use this updated Excel file in the next step to enrich and sort your JSON data.")
    except Exception as e:
        print(f"Error saving data to Excel file: {e}")

if __name__ == "__main__":
    main()