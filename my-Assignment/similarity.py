import sqlite3
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# function to find similarity
def find_similar(target_id, k=5):
    conn = sqlite3.connect('redfin_properties.db')
    cursor = conn.cursor()

    # Fetch properties data 
    cursor.execute('SELECT ROWID, price, beds, baths FROM properties')
    listings = cursor.fetchall()
    conn.close()

    features = []
    ids = []
    for listing in listings:
        row_id, price, beds, baths = listing
        if price and beds and baths:
            price = float(price.replace('$', '').replace(',', ''))
            beds = int(''.join(filter(str.isdigit, beds)))  
            baths = float(''.join(filter(str.isdigit, baths)))  

            features.append([price, beds, baths])
            ids.append(row_id)

    # Convert to numpy array for easier manipulation
    features = np.array(features)
    ids = np.array(ids)

    # Standardize the features 
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Create the KNN model
    knn = NearestNeighbors(n_neighbors=k, metric='euclidean')
    knn.fit(features_scaled)

    # Find the target listing's index
    if target_id not in ids:
        print(f"Listing with ROWID {target_id} not found in the dataset.")
        return []

    target_index = np.where(ids == target_id)[0][0]
    target_listing = features_scaled[target_index].reshape(1, -1)

    # Get the indices of the k nearest neighbors
    distances, indices = knn.kneighbors(target_listing)

    similar_listings = ids[indices.flatten()]
    return similar_listings

if __name__ == "__main__":
    target_listing_id = 1 # target id
    similar_listings = find_similar(target_listing_id)
    print(f"Listings similar to ROWID {target_listing_id}: {similar_listings}")
