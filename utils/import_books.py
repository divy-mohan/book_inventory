import pandas as pd
import os
import sys

# Adjust the path to your project root if needed
sys.path.append(r"e:\Divy\Projects\Prabhakar JI\Sahitya Vistar")

from database.db_manager import DatabaseManager

# Path to your Excel file
excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Book_entry.xlsx")

# Read the Excel file
df = pd.read_excel(excel_path)

# Company name
company_name = "सुल्तानपुर साहित्य विस्तार पटल"

# Initialize database manager
db = DatabaseManager()

# Get all companies
companies = db.get_all_companies()
# Find the company with the matching name
company = next((c for c in companies if c['name'] == company_name), None)

if not company:
    print(f"Company '{company_name}' not found in database.")
    sys.exit(1)
company_id = company['id']

# Insert books using add_book
for idx, row in df.iterrows():
    book_code = str(row['BOOK CODE']).strip()
    book_name = str(row['BOOK NAME']).strip()
    category = str(row['CATEGORY']).strip() if 'CATEGORY' in row else ''
    language = str(row['Language']).strip() if 'Language' in row else 'Hindi'
    book_data = {
        'company_id': company_id,
        'name': book_name,
        'isbn': book_code,
        'category': category,
        'language': language
    }
    success = db.add_book(book_data)
    if success:
        print(f"Inserted: {book_code} - {book_name} ({category}, {language})")
    else:
        print(f"Failed to insert: {book_code} - {book_name} ({category}, {language})")

# print("All books imported successfully.")