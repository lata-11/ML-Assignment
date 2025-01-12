import sqlite3
import pandas as pd

# Read the CSV file using pandas
csv_file = 'redfin_properties_with_about.csv'
df = pd.read_csv(csv_file)

db_file = 'redfin_properties.db'
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create a table with the same column names as the CSV
columns = ', '.join([f'"{col}" TEXT' for col in df.columns])
create_table_query = f'CREATE TABLE IF NOT EXISTS properties ({columns});'

cursor.execute(create_table_query)

# Insert the CSV data into the SQLite database table
df.to_sql('properties', conn, if_exists='replace', index=False)


conn.commit()
conn.close()

print(f"CSV data from {csv_file} has been successfully imported into {db_file} database.")
