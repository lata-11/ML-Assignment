import sqlite3


conn = sqlite3.connect('/home/lata/Desktop/ML-Assignment/redfin_properties.db')
cursor = conn.cursor()

# Query the top 5 rows from the 'properties' table
query = "SELECT * FROM ranked_properties LIMIT 5"  
cursor.execute(query)

# Query to get the row count
cursor.execute("SELECT COUNT(*) FROM ranked_properties")


row_count = cursor.fetchone()[0]


print(f"Total number of rows in ranked_properties: {row_count}")


rows = cursor.fetchall()


for row in rows:
    print(row)

conn.close()
