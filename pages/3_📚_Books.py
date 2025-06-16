import streamlit as st
import pandas as pd
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.book import Book
from utils.helpers import show_success, show_error, format_currency, paginate_data, filter_data

st.set_page_config(
    page_title="Books - Book Inventory",
    page_icon="📚",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# Page header
st.markdown("""
<div style="background: linear-gradient(90deg, #1f77b4 0%, #2e86de 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;">
    <h1>📚 Book Inventory Management</h1>
    <p>Manage your complete book collection with Hindi/English support</p>
</div>
""", unsafe_allow_html=True)

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before managing books.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Sidebar for actions
with st.sidebar:
    st.markdown("### 📖 Book Actions")
    action = st.selectbox(
        "Choose Action",
        ["View Books", "Add New Book", "Edit Book", "Update Stock", "Delete Book"]
    )
    
    st.markdown("### 🏢 Filter by Company")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )

# Main content based on selected action
if action == "View Books":
    st.markdown("### 📋 Book Inventory")
    
    # Get books based on company filter
    if company_filter == "All Companies":
        books = db.get_all_books()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        books = db.get_books_by_company(selected_company['id'])
    
    if books:
        # Search and filter options
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search books...", placeholder="Enter book name, author, category, or ISBN")
        
        with col2:
            language_filter = st.selectbox("Language", ["All", "English", "Hindi", "Other"])
        
        with col3:
            category_filter = st.selectbox("Category", ["All"] + list(set(book.get('category', 'Uncategorized') for book in books)))
        
        # Apply filters
        filtered_books = books
        
        if search_term:
            filtered_books = filter_data(filtered_books, search_term, ['name', 'author', 'category', 'isbn'])
        
        if language_filter != "All":
            filtered_books = [book for book in filtered_books if book.get('language', 'English') == language_filter]
        
        if category_filter != "All":
            filtered_books = [book for book in filtered_books if book.get('category', 'Uncategorized') == category_filter]
        
        # Display books count
        st.write(f"📊 Showing **{len(filtered_books)}** of **{len(books)}** books")
        
        if filtered_books:
            # Pagination
            page_data, current_page, total_pages = paginate_data(filtered_books, 10)
            
            # Display books in a table format
            for book in page_data:
                with st.expander(f"📖 {book['name']} - {book.get('author', 'Unknown Author')}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Company:** {book.get('company_name', 'N/A')}")
                        st.write(f"**Category:** {book.get('category', 'Uncategorized')}")
                        st.write(f"**Language:** {book.get('language', 'English')}")
                        st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Purchase Price:** {format_currency(book.get('purchase_price', 0))}")
                        st.write(f"**Selling Price:** {format_currency(book.get('selling_price', 0))}")
                        st.write(f"**Profit per Unit:** {format_currency(book.get('selling_price', 0) - book.get('purchase_price', 0))}")
                    
                    with col3:
                        stock_qty = book.get('stock_quantity', 0)
                        damaged_qty = book.get('damaged_quantity', 0)
                        lost_qty = book.get('lost_quantity', 0)
                        available_stock = stock_qty - damaged_qty - lost_qty
                        
                        # Color code stock levels
                        if available_stock <= 5:
                            stock_color = "🔴"
                        elif available_stock <= 20:
                            stock_color = "🟡"
                        else:
                            stock_color = "🟢"
                        
                        st.write(f"**Total Stock:** {stock_qty}")
                        st.write(f"**Available Stock:** {stock_color} {available_stock}")
                        st.write(f"**Damaged:** {damaged_qty}")
                        st.write(f"**Lost:** {lost_qty}")
                        st.write(f"**Stock Value:** {format_currency(available_stock * book.get('selling_price', 0))}")
        else:
            st.info("No books match your search criteria.")
    else:
        st.info("No books added yet. Add your first book!")

elif action == "Add New Book":
    st.markdown("### ➕ Add New Book")
    
    with st.form("add_book_form"):
        st.markdown("#### Book Information")
        
        # Company selection
        company_options = {f"{comp['name']}": comp['id'] for comp in companies}
        selected_company_name = st.selectbox("Company *", list(company_options.keys()))
        company_id = company_options[selected_company_name]
        
        col1, col2 = st.columns(2)
        
        with col1:
            book_name = st.text_input("Book Name *", placeholder="Enter book title")
            author = st.text_input("Author", placeholder="Author name")
            category = st.text_input("Category", placeholder="Fiction, Non-Fiction, Educational, etc.")
            language = st.selectbox("Language", ["English", "Hindi", "Other"])
        
        with col2:
            isbn = st.text_input("ISBN", placeholder="ISBN number")
            purchase_price = st.number_input("Purchase Price (₹)", min_value=0.0, value=0.0, step=0.01)
            selling_price = st.number_input("Selling Price (₹)", min_value=0.0, value=0.0, step=0.01)
            initial_stock = st.number_input("Initial Stock Quantity", min_value=0, value=0, step=1)
        
        submitted = st.form_submit_button("📚 Add Book", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if not book_name.strip():
                errors.append("Book name is required")
            
            if purchase_price < 0:
                errors.append("Purchase price cannot be negative")
            
            if selling_price < 0:
                errors.append("Selling price cannot be negative")
            
            if initial_stock < 0:
                errors.append("Stock quantity cannot be negative")
            
            if errors:
                for error in errors:
                    show_error(error)
            else:
                # Create book object
                book = Book(
                    company_id=company_id,
                    name=book_name.strip(),
                    author=author.strip(),
                    category=category.strip(),
                    language=language,
                    isbn=isbn.strip(),
                    purchase_price=purchase_price,
                    selling_price=selling_price,
                    stock_quantity=initial_stock
                )
                
                # Add to database
                if db.add_book(book.to_dict()):
                    show_success(f"Book '{book_name}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    show_error("Failed to add book. Please try again.")

elif action == "Edit Book":
    st.markdown("### ✏️ Edit Book")
    
    # Get books for selection
    if company_filter == "All Companies":
        books = db.get_all_books()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        books = db.get_books_by_company(selected_company['id'])
    
    if books:
        book_options = {f"{book['name']} - {book.get('author', 'Unknown')} (ID: {book['id']})": book['id'] for book in books}
        selected_book_key = st.selectbox("Select Book to Edit", list(book_options.keys()))
        
        if selected_book_key:
            book_id = book_options[selected_book_key]
            book = db.get_book_by_id(book_id)
            
            if book:
                with st.form("edit_book_form"):
                    st.markdown("#### Update Book Information")
                    
                    # Company selection
                    company_options = {f"{comp['name']}": comp['id'] for comp in companies}
                    current_company_name = next(comp['name'] for comp in companies if comp['id'] == book['company_id'])
                    selected_company_name = st.selectbox("Company *", list(company_options.keys()), 
                                                        index=list(company_options.keys()).index(current_company_name))
                    company_id = company_options[selected_company_name]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        book_name = st.text_input("Book Name *", value=book['name'])
                        author = st.text_input("Author", value=book.get('author', ''))
                        category = st.text_input("Category", value=book.get('category', ''))
                        language = st.selectbox("Language", ["English", "Hindi", "Other"], 
                                               index=["English", "Hindi", "Other"].index(book.get('language', 'English')))
                    
                    with col2:
                        isbn = st.text_input("ISBN", value=book.get('isbn', ''))
                        purchase_price = st.number_input("Purchase Price (₹)", min_value=0.0, 
                                                       value=float(book.get('purchase_price', 0)), step=0.01)
                        selling_price = st.number_input("Selling Price (₹)", min_value=0.0, 
                                                       value=float(book.get('selling_price', 0)), step=0.01)
                        stock_quantity = st.number_input("Stock Quantity", min_value=0, 
                                                        value=int(book.get('stock_quantity', 0)), step=1)
                    
                    updated = st.form_submit_button("💾 Update Book", use_container_width=True)
                    
                    if updated:
                        # Validation
                        errors = []
                        
                        if not book_name.strip():
                            errors.append("Book name is required")
                        
                        if purchase_price < 0:
                            errors.append("Purchase price cannot be negative")
                        
                        if selling_price < 0:
                            errors.append("Selling price cannot be negative")
                        
                        if stock_quantity < 0:
                            errors.append("Stock quantity cannot be negative")
                        
                        if errors:
                            for error in errors:
                                show_error(error)
                        else:
                            # Update book
                            updated_book = Book(
                                id=book_id,
                                company_id=company_id,
                                name=book_name.strip(),
                                author=author.strip(),
                                category=category.strip(),
                                language=language,
                                isbn=isbn.strip(),
                                purchase_price=purchase_price,
                                selling_price=selling_price,
                                stock_quantity=stock_quantity
                            )
                            
                            if db.update_book(book_id, updated_book.to_dict()):
                                show_success(f"Book '{book_name}' updated successfully!")
                                st.rerun()
                            else:
                                show_error("Failed to update book. Please try again.")
    else:
        st.info("No books available to edit.")

elif action == "Update Stock":
    st.markdown("### 📦 Update Stock")
    
    # Get books for selection
    if company_filter == "All Companies":
        books = db.get_all_books()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        books = db.get_books_by_company(selected_company['id'])
    
    if books:
        book_options = {f"{book['name']} - {book.get('author', 'Unknown')} (Current: {book['stock_quantity']})": book['id'] for book in books}
        selected_book_key = st.selectbox("Select Book", list(book_options.keys()))
        
        if selected_book_key:
            book_id = book_options[selected_book_key]
            book = db.get_book_by_id(book_id)
            
            if book:
                st.markdown("#### Current Stock Information")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📚 Total Stock", book['stock_quantity'])
                
                with col2:
                    damaged_qty = book.get('damaged_quantity', 0)
                    lost_qty = book.get('lost_quantity', 0)
                    available_stock = book['stock_quantity'] - damaged_qty - lost_qty
                    st.metric("✅ Available Stock", available_stock)
                
                with col3:
                    stock_value = available_stock * book.get('selling_price', 0)
                    st.metric("💰 Stock Value", format_currency(stock_value))
                
                st.markdown("#### Stock Adjustment")
                
                adjustment_type = st.selectbox(
                    "Adjustment Type",
                    ["Add Stock (Purchase/Return)", "Remove Stock (Sale/Loss)", "Mark as Damaged", "Mark as Lost"]
                )
                
                quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
                reason = st.text_area("Reason/Notes", placeholder="Reason for stock adjustment")
                
                if st.button("📦 Update Stock", use_container_width=True):
                    success = False
                    
                    if adjustment_type == "Add Stock (Purchase/Return)":
                        success = db.update_book_stock(book_id, quantity, 'IN')
                    elif adjustment_type == "Remove Stock (Sale/Loss)":
                        if quantity <= available_stock:
                            success = db.update_book_stock(book_id, -quantity, 'OUT')
                        else:
                            show_error(f"Cannot remove {quantity} items. Only {available_stock} available.")
                    elif adjustment_type == "Mark as Damaged":
                        if quantity <= available_stock:
                            # Update damaged quantity
                            db.execute_update("UPDATE books SET damaged_quantity = damaged_quantity + ? WHERE id = ?", 
                                            (quantity, book_id))
                            success = True
                        else:
                            show_error(f"Cannot mark {quantity} as damaged. Only {available_stock} available.")
                    elif adjustment_type == "Mark as Lost":
                        if quantity <= available_stock:
                            # Update lost quantity
                            db.execute_update("UPDATE books SET lost_quantity = lost_quantity + ? WHERE id = ?", 
                                            (quantity, book_id))
                            success = True
                        else:
                            show_error(f"Cannot mark {quantity} as lost. Only {available_stock} available.")
                    
                    if success:
                        show_success(f"Stock updated successfully! {adjustment_type}: {quantity}")
                        st.rerun()
                    elif not any(adjustment_type.startswith(prefix) for prefix in ["Mark as Damaged", "Mark as Lost"]):
                        show_error("Failed to update stock. Please try again.")
    else:
        st.info("No books available for stock update.")

elif action == "Delete Book":
    st.markdown("### 🗑️ Delete Book")
    
    # Get books for selection
    if company_filter == "All Companies":
        books = db.get_all_books()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        books = db.get_books_by_company(selected_company['id'])
    
    if books:
        st.warning("⚠️ **Warning:** Deleting a book will permanently remove it from the system!")
        
        book_options = {f"{book['name']} - {book.get('author', 'Unknown')} (ID: {book['id']})": book['id'] for book in books}
        selected_book_key = st.selectbox("Select Book to Delete", list(book_options.keys()))
        
        if selected_book_key:
            book_id = book_options[selected_book_key]
            book = db.get_book_by_id(book_id)
            
            if book:
                st.markdown("#### Book Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {book['name']}")
                    st.write(f"**Author:** {book.get('author', 'N/A')}")
                    st.write(f"**Category:** {book.get('category', 'N/A')}")
                    st.write(f"**Language:** {book.get('language', 'N/A')}")
                
                with col2:
                    st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
                    st.write(f"**Purchase Price:** {format_currency(book.get('purchase_price', 0))}")
                    st.write(f"**Selling Price:** {format_currency(book.get('selling_price', 0))}")
                    st.write(f"**Stock Quantity:** {book.get('stock_quantity', 0)}")
                
                # Confirmation checkbox
                confirm_delete = st.checkbox(f"I understand that deleting '{book['name']}' will permanently remove it from the system")
                
                if confirm_delete:
                    if st.button("🗑️ Delete Book", type="primary", use_container_width=True):
                        if db.delete_book(book_id):
                            show_success(f"Book '{book['name']}' deleted successfully!")
                            st.rerun()
                        else:
                            show_error("Failed to delete book. Please try again.")
    else:
        st.info("No books available to delete.")

# Book Statistics
st.markdown("---")
st.markdown("### 📊 Inventory Statistics")

if company_filter == "All Companies":
    books = db.get_all_books()
else:
    selected_company = next(comp for comp in companies if comp['name'] == company_filter)
    books = db.get_books_by_company(selected_company['id'])

if books:
    total_books = len(books)
    total_stock = sum(book.get('stock_quantity', 0) for book in books)
    total_value = sum((book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)) * book.get('selling_price', 0) for book in books)
    low_stock_count = len([book for book in books if (book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)) <= 5])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Total Books", total_books)
    
    with col2:
        st.metric("📦 Total Stock", total_stock)
    
    with col3:
        st.metric("💰 Stock Value", format_currency(total_value))
    
    with col4:
        st.metric("⚠️ Low Stock Items", low_stock_count)
else:
    st.info("Add books to see statistics.")
