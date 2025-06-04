import json
import os
import re
from urllib.parse import urlparse
import time

# NOTE: The 'Google Search' tool is called directly by the model in its environment.
# You, running this script locally, would typically need a separate library/API key
# (e.g., Google Custom Search API, SerpApi) to perform web searches.
# However, for the purpose of demonstrating the *logic* of automated suggestion,
# I will use the syntax that would trigger the search for me.
# If you run this script locally and need it to perform actual web searches,
# you would need to replace the `Google Search` calls with calls to a
# web search API you have set up.

# --- File Paths ---
INPUT_ARTICLES_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\nativekin_aggregated_articles.json"
SOURCE_MAPPING_FILE = r"C:\Users\John\Documents\nativekin.org\nativekin-media-site\nativekin.github.io\media\source_mapping.json"


def load_json_file(filepath, description="data"):
    """Loads JSON data from a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} items from {description} file: {filepath}")
        return data
    except FileNotFoundError:
        print(f"Error: {description.capitalize()} file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. File might be corrupted or empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading {description}: {e}")
        return None

def get_base_domain(url):
    """Extracts the base domain from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc.replace('www.', '')

def extract_hints_from_search(query_results):
    """
    Attempts to extract tribe and region hints from Google Search results.
    This is heuristic and might not be perfect.
    """
    potential_tribe = "Uncertain Tribe"
    potential_region = "Uncertain Region"

    # Keywords to look for in search snippets/titles
    tribe_keywords = ['tribe', 'nation', 'band of', 'community', 'peoples', 'confederated']
    # Prioritize common states for region detection
    region_keywords = ['alaska', 'arizona', 'california', 'colorado', 'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia', 'wisconsin', 'wyoming',
                       'midwest', 'southwest', 'southeast', 'northeast', 'northwest', 'plains', 'great lakes', 'rocky mountains', 'pacific northwest', 'atlantic coast', 'gulf coast']

    # Combine all relevant text from search results
    all_search_text = " ".join([r.get('title', '') + " " + r.get('snippet', '') for r in query_results]).lower()

    # Simple keyword matching for tribe
    found_tribes = []
    # A list of more specific tribal names to search for
    known_tribes_specific = [
        "navajo", "cherokee", "osage", "muscogee", "choctaw", "chickasaw", "apache",
        "salish", "kootenai", "hopi", "oneida", "ojibwe", "chippewa", "pima", "maricopa",
        "mohican", "cheyenne", "arapaho", "cowlitz", "potawatomi", "ute", "spokane",
        "meskwaki", "quinault", "lac du flambeau", "menominee", "ho-chunk", "tulalip",
        "yakama", "grand ronde", "colorado river indian", "semilpo", "saginaw chippewa",
        "oglalala", "lakota", "sioux", "iroquois", "wampanoag", "lumbee", "chumash",
        "puyallup", "flathead", "blackfeet", "crow", "nez perce", "shoshone", "paiute",
        "hualapai", "zuni", "akwesasne", "onondaga", "seneca", "cayuga", "tuscarora",
        "mohawk", "mashpee", "penobscot", "passamaquoddy", "narragansett", "miccosukee",
        "seminole", "caddo", "wichita", "kiowa", "comanche", "cree", "choctaw", "ponca",
        "omaha", "kansa", "otoe-missouria", "kickapoo", "potawatomi", "sac and fox",
        "wyandotte", "delaware", "shawnee", "modoc", "klamath", "coquille", "karuk",
        "yurok", "hoopa", "pit river", "round valley", "tule river", "big valley",
        "dry creek", "federated indians", "ukiah", "colusa", "morongo", "san manuel",
        "agau caliente", "viejas", "barona", "sycu", "capitan grande", "campo", "la jolla",
        "mesa grande", "pauma", "rincon", "santa ysabel", "sycuan", "torres martinez",
        "twenty-nine palms", "agua caliete", "cabazon", "cahuilla"
        # This list can be expanded for better accuracy.
    ]

    for tribe in known_tribes_specific:
        if tribe.lower() in all_search_text:
            found_tribes.append(tribe) # Keep original capitalization or apply title() later

    # If specific tribes found, prioritize them
    if found_tribes:
        potential_tribe = ", ".join(sorted(list(set(found_tribes))))
    # Fallback to generic if specific not found but context suggests Native focus
    elif any(k in all_search_text for k in tribe_keywords):
        potential_tribe = "Likely Tribal/Native Focused"

    # Simple keyword matching for region
    found_regions = []
    for region in region_keywords:
        if region.lower() in all_search_text:
            found_regions.append(region)

    if found_regions:
        potential_region = ", ".join(sorted(list(set(found_regions))))

    return potential_tribe, potential_region


def main():
    # 1. Load articles to get all source URLs
    articles = load_json_file(INPUT_ARTICLES_FILE, "articles")
    if articles is None:
        return

    unique_source_urls = {article.get('source_url') for article in articles if article.get('source_url')}
    print(f"\nFound {len(unique_source_urls)} unique source URLs in the articles.")

    # 2. Load existing source mapping
    existing_mapping = load_json_file(SOURCE_MAPPING_FILE, "source mapping")
    if existing_mapping is None:
        existing_mapping = {} # Start with an empty mapping if file doesn't exist/is invalid

    unmapped_sources = [url for url in unique_source_urls if url not in existing_mapping]
    print(f"\nFound {len(unmapped_sources)} unmapped source URLs.")

    if not unmapped_sources:
        print("All unique source URLs are already mapped. No new suggestions needed.")
        return

    print("\n--- Generating Suggestions for Unmapped Sources (using Google Search) ---")
    print("Please review these suggestions and update your 'source_mapping.json' file.")
    print("This process can take some time due to search queries (approx. 2 seconds per unmapped source).\n")

    suggested_updates = {}

    for i, source_url in enumerate(unmapped_sources):
        domain = get_base_domain(source_url)
        print(f"[{i+1}/{len(unmapped_sources)}] Researching: {source_url}")

        # Construct general query for the source
        query_general = f'"{domain}" "Native American tribe" OR "Indian Nation" OR "Indigenous people" news'

        try:
            # THIS IS THE CORRECTED CALL FOR THE GOOGLE SEARCH TOOL
            # The 'queries' parameter expects a list of strings.
            # The tool returns a list of dictionaries, one for each search result.
            search_results = Google Search(queries=[query_general])
            
            # search_results will be a list where each item is a dictionary of results for a query.
            # We want the first (and only) query's results.
            if search_results and search_results[0]:
                hints = extract_hints_from_search(search_results[0]) # Pass the actual list of search result dictionaries
                potential_tribe, potential_region = hints
                
                print(f"  Suggested Tribe: {potential_tribe}")
                print(f"  Suggested Region: {potential_region}")
                suggested_updates[source_url] = {"tribe": potential_tribe, "region": potential_region}
            else:
                print(f"  No significant search results found for {source_url}")
                suggested_updates[source_url] = {"tribe": "Manual Review Needed", "region": "Manual Review Needed"}

        except Exception as e:
            print(f"  Error during Google search for {source_url}: {e}")
            suggested_updates[source_url] = {"tribe": "Search Error", "region": "Search Error"}

        print("-" * 50)
        time.sleep(2) # Be polite to the search tool/API, wait a bit between queries

    print("\n--- Suggested Additions to Your 'source_mapping.json' ---")
    print("Copy and paste these entries into your 'source_mapping.json' file, then verify for accuracy.")
    print("=================================================================================\n")
    print(json.dumps(suggested_updates, indent=4, ensure_ascii=False))
    print("\n=================================================================================\n")
    print("After updating 'source_mapping.json', run the sorting script again.")


if __name__ == "__main__":
    main()