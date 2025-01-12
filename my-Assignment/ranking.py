import sqlite3
import pandas as pd
import re

# Connect to the raw data database
conn_raw = sqlite3.connect('/home/lata/Desktop/ML-Assignment/redfin_properties.db')
cursor_raw = conn_raw.cursor()

# Fetch relevant data from the raw properties table
cursor_raw.execute('''
SELECT price, Beds, Baths, Address, Link, [About This Home], [Key Details]
FROM properties
''')

# Fetch all rows of data
properties_data = cursor_raw.fetchall()

# Convert the fetched data into a Pandas DataFrame for easier manipulation
columns = ['price', 'beds', 'baths', 'address', 'link', 'about_this_home', 'key_details']
df = pd.DataFrame(properties_data, columns=columns)

# Function to extract and calculate the feature score based on the keywords in the text
def feature_score(text):
    score = 0
    keywords = [
        'garage', 'pool', 'balcony', 'garden', 'view', 'renovated', 'modern',
        'spacious', 'luxury', 'elevator', 'fireplace', 'gym', 'sauna', 'patio',
        'terrace', 'rooftop', 'hardwood', 'marble', 'stainless steel', 'kitchen island',
        'granite', 'basement', 'air conditioning', 'central heating', 'security',
        'smart home', 'office', 'home theater', 'jacuzzi', 'panoramic', 'walk-in closet',
        'greenhouse', 'outdoor kitchen', 'wine cellar', 'guest house', 'sauna', 'high ceiling',
        'fenced', 'private', 'pool house', 'beachfront', 'waterfront', 'acreage', 'barn',
        'shed', 'gated', 'mountain view', 'lake view', 'city view', 'sunroom', 'atrium',
        'solar panels', 'eco-friendly', 'sustainable', 'home automation', 'smart lighting',
        'energy-efficient', 'ceramic tiles', 'crown molding', 'luxurious', 'open floor plan',
        'country style', 'mediterranean', 'contemporary', 'historic', 'french doors',
        'skylights', 'balustrade', 'conservatory', 'hardscaping', 'pool table', 'playroom',
        'staircase', 'built-in shelves', 'barbecue area', 'green roof', 'solar power', 'soundproof',
        'shutters', 'outdoor fireplace', 'pet-friendly', 'community amenities', 'swimming pool',
        'exercise room', 'view of city', 'lakeside', 'townhouse', 'single family', 'apartment',
        'close to transport', 'close to shopping', 'quiet neighborhood', 'renovated kitchen',
        'open-plan living', 'new construction', 'modern appliances', 'upgraded finishes', 'natural light',
        'near parks', 'walkable', 'biking paths', 'balcony views', 'close to schools', 'open kitchen',
        'double garage', 'private driveway', 'home office', 'panoramic views', 'custom built',
        'move-in ready', 'high-end finishes', 'multi-level', 'two-story', 'underfloor heating',
        'indoor-outdoor living', 'sound system', 'climate control', 'luxury finishes', 'maintenance-free',
        'near beach', 'close to highway', 'ample parking', 'en-suite bathroom', 'smart thermostat'
    ]
    # Loop through the keywords and increase score if found in the text
    for keyword in keywords:
        if keyword.lower() in text.lower():
            score += 1
    return score

# Apply feature scoring to both 'about_this_home' and 'key_details'
df['feature_score'] = df['about_this_home'].apply(feature_score) + df['key_details'].apply(feature_score)

# Extract year 
def extract_age_of_house(key_details):
    match = re.search(r'Built in (\d{4})', key_details)
    if match:
        built_year = int(match.group(1))
        current_year = 2025
        return current_year - built_year
    return None  

# Apply the function to the DataFrame
df['age_of_house'] = df['key_details'].apply(extract_age_of_house)

# Extract lot size (sq ft)
def extract_lot_size(key_details):
    match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*sq ft lot', key_details)
    if match:
        return float(match.group(1).replace(',', ''))
    return None  

# Extract price per square foot
def extract_price_per_sqft(key_details):
    match = re.search(r'\$(\d+)\s*per sq ft', key_details)
    if match:
        return float(match.group(1))
    return None

df['lot_size'] = df['key_details'].apply(extract_lot_size)
df['price_per_sqft'] = df['key_details'].apply(extract_price_per_sqft)


# Heuristic rank calculation
def calculate_rank(price, beds, baths, feature_score):
    """
    Calculate rank using a heuristic formula that incorporates price, beds, baths, and feature score.
    Handles missing or invalid data by treating them as zero.
    """
    # Convert values to numeric, ensuring that strings or None are handled appropriately
    price = pd.to_numeric(price, errors='coerce') if price else 0
    beds = pd.to_numeric(beds, errors='coerce') if beds else 0
    baths = pd.to_numeric(baths, errors='coerce') if baths else 0
    feature_score = feature_score if feature_score > 0 else 0
    
    return 0.4 * price + 0.3 * beds * 10000 + 0.2 * baths * 10000 + 0.1 * feature_score * 1000


# Apply heuristic rank safely
df['heuristic_rank'] = df.apply(
    lambda x: calculate_rank(x['price'], x['beds'], x['baths'], x['feature_score']),
    axis=1
)

# Normalize ranks
min_rank = df['heuristic_rank'].min()
max_rank = df['heuristic_rank'].max()
if max_rank != min_rank: 
    df['normalized_rank'] = ((df['heuristic_rank'] - min_rank) / (max_rank - min_rank) * (len(df) - 1)).round() + 1
else:
    df['normalized_rank'] = 1  


# Create a new database to store the relevant ranking data
conn_ranking = sqlite3.connect('/home/lata/Desktop/ML-Assignment/ranking_properties.db')
cursor_ranking = conn_ranking.cursor()

# Drop the table if it already exists (optional, be cautious with this)
cursor_ranking.execute('DROP TABLE IF EXISTS ranked_properties')

# Create the table with all necessary columns
cursor_ranking.execute('''
CREATE TABLE IF NOT EXISTS ranked_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price INTEGER,
    beds INTEGER,
    baths INTEGER,
    address TEXT,
    link TEXT,
    feature_score INTEGER,
    price_per_sqft REAL,
    lot_size REAL,
    age_of_house INTEGER,
    heuristic_rank REAL,    -- Added column
    normalized_rank INTEGER
)
''')


# Insert the processed data into the ranked_properties table
for row in df.itertuples(index=False):
    cursor_ranking.execute('''
    INSERT INTO ranked_properties (price, beds, baths, address, link, feature_score, price_per_sqft, lot_size, age_of_house, heuristic_rank, normalized_rank)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row.price, row.beds, row.baths, row.address, row.link, row.feature_score, row.price_per_sqft, row.lot_size, row.age_of_house, row.heuristic_rank, row.normalized_rank))


# Store results as a .txt file
txt_file_path = '/home/lata/Desktop/ML-Assignment/ranking_properties.txt'


df.to_csv(txt_file_path, sep='\t', index=False)  

# Commit changes and close the connections
conn_ranking.commit()
conn_raw.close()
conn_ranking.close()

print("Ranking data has been successfully processed and stored.")
