import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.helpers import show_success, show_error, format_currency, paginate_data, filter_data, format_date

st.set_page_config(
    page_title="Purchase - Book Inventory",
    page_icon="🛒",
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
    <h1>🛒 Purchase Management</h1>
    <p>Record book purchases and manage inventory procurement</p>
</div>
""", unsafe_allow_html=True)

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before managing purchases.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Sidebar for actions
with st.sidebar:
    st.markdown("### 🛒 Purchase Actions")
    action = st.selectbox(
        "Choose Action",
        ["View Purchases", "Add New Purchase", "Purchase History"]
    )
    
    st.markdown("### 🏢 Filter by Company")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )

# Main content based on selected action
if action == "View Purchases":
    st.markdown("### 📋 Purchase Records")
    
    # Get purchases based on company filter
    if company_filter == "All Companies":
        all_purchases = []
        for company in companies:
            purchases = db.get_purchases_by_company(company['id'])
            all_purchases.extend(purchases)
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        all_purchases = db.get_purchases_by_company(selected_company['id'])
    
    if all_purchases:
        # Search and filter options
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search purchases...", placeholder="Enter book name, author, or supplier")
        
        with col2:
            # Date range filter
            date_filter = st.selectbox("Date Range", ["All Time", "This Month", "Last 30 Days", "This Year"])
        
        # Apply search filter
        filtered_purchases = all_purchases
        if search_term:
            filtered_purchases = filter_data(filtered_purchases, search_term, ['book_name', 'author', 'supplier_name'])
        
        # Apply date filter
        if date_filter != "All Time":
            today = datetime.now().date()
            if date_filter == "This Month":
                filter_date = today.replace(day=1)
            elif date_filter == "Last 30 Days":
                filter_date = today - pd.Timedelta(days=30)
            elif date_filter == "This Year":
                filter_date = today.replace(month=1, day=1)
            
            filtered_purchases = [
                purchase for purchase in filtered_purchases 
                if purchase.get('purchase_date') and 
                datetime.strptime(str(purchase['purchase_date']), '%Y-%m-%d').date() >= filter_date
            ]
        
        # Display purchase count
        st.write(f"📊 Showing **{len(filtered_purchases)}** of **{len(all_purchases)}** purchase records")
        
        if filtered_purchases:
            # Calculate totals
            total_amount = sum(purchase['total_amount'] for purchase in filtered_purchases)
            total_quantity = sum(purchase['quantity'] for purchase in filtered_purchases)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📦 Total Quantity", total_quantity)
            with col2:
                st.metric("💰 Total Amount", format_currency(total_amount))
            
            st.markdown("---")
            
            # Pagination
            page_data, current_page, total_pages = paginate_data(filtered_purchases, 10)
            
            # Display purchases
            for purchase in page_data:
                with st.expander(f"🛒 {purchase['book_name']} - {format_date(purchase['purchase_date'])}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Book:** {purchase['book_name']}")
                        st.write(f"**Author:** {purchase.get('author', 'N/A')}")
                        st.write(f"**Company:** {purchase.get('company_name', 'N/A')}")
                        st.write(f"**Supplier:** {purchase.get('supplier_name', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Quantity:** {purchase['quantity']}")
                        st.write(f"**Price per Unit:** {format_currency(purchase['price_per_unit'])}")
                        st.write(f"**Total Amount:** {format_currency(purchase['total_amount'])}")
                        st.write(f"**Purchase Date:** {format_date(purchase['purchase_date'])}")
                    
                    with col3:
                        if purchase.get('notes'):
                            st.write(f"**Notes:** {purchase['notes']}")
                        st.write(f"**Created:** {format_date(purchase.get('created_at', ''))}")
        else:
            st.info("No purchases match your search criteria.")
    else:
        st.info("No purchase records found. Add your first purchase!")

elif action == "Add New Purchase":
    st.markdown("### ➕ Record New Purchase")
    
    # Get books for purchase
    if company_filter == "All Companies":
        books = db.get_all_books()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        books = db.get_books_by_company(selected_company['id'])
    
    if not books:
        st.warning("⚠️ No books available. Please add books first.")
        if st.button("📚 Go to Books"):
            st.switch_page("pages/3_📚_Books.py")
        st.stop()
    
    with st.form("add_purchase_form"):
        st.markdown("#### Purchase Information")
        
        # Book selection
        book_options = {f"{book['name']} - {book.get('author', 'Unknown')} ({book.get('company_name', 'N/A')})": book['id'] for book in books}
        selected_book_key = st.selectbox("Select Book *", list(book_options.keys()))
        book_id = book_options[selected_book_key]
        
        # Get selected book details
        selected_book = next(book for book in books if book['id'] == book_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_name = st.text_input("Supplier Name", placeholder="Enter supplier/vendor name")
            quantity = st.number_input("Quantity *", min_value=1, value=1, step=1)
            price_per_unit = st.number_input("Price per Unit (₹) *", min_value=0.01, value=float(selected_book.get('purchase_price', 0)), step=0.01)
        
        with col2:
            purchase_date = st.date_input("Purchase Date", value=date.today())
            total_amount = quantity * price_per_unit
            st.write(f"**Total Amount:** {format_currency(total_amount)}")
            
            # Show current stock
            st.info(f"📦 Current Stock: {selected_book.get('stock_quantity', 0)}")
        
        notes = st.text_area("Notes", placeholder="Additional notes about this purchase")
        
        submitted = st.form_submit_button("🛒 Record Purchase", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if quantity <= 0:
                errors.append("Quantity must be greater than 0")
            
            if price_per_unit <= 0:
                errors.append("Price per unit must be greater than 0")
            
            if errors:
                for error in errors:
                    show_error(error)
            else:
                # Create purchase record
                purchase_data = {
                    'company_id': selected_book['company_id'],
                    'book_id': book_id,
                    'supplier_name': supplier_name.strip(),
                    'quantity': quantity,
                    'price_per_unit': price_per_unit,
                    'total_amount': total_amount,
                    'purchase_date': purchase_date,
                    'notes': notes.strip()
                }
                
                # Add to database
                if db.add_purchase(purchase_data):
                    show_success(f"Purchase recorded successfully! Stock updated for '{selected_book['name']}'")
                    st.balloons()
                    
                    # Show updated stock information
                    updated_book = db.get_book_by_id(book_id)
                    st.info(f"📈 Stock updated: {selected_book.get('stock_quantity', 0)} → {updated_book.get('stock_quantity', 0)}")
                    st.rerun()
                else:
                    show_error("Failed to record purchase. Please try again.")

elif action == "Purchase History":
    st.markdown("### 📊 Purchase Analytics")
    
    # Get purchases based on company filter
    if company_filter == "All Companies":
        all_purchases = []
        for company in companies:
            purchases = db.get_purchases_by_company(company['id'])
            all_purchases.extend(purchases)
        analysis_title = "All Companies"
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        all_purchases = db.get_purchases_by_company(selected_company['id'])
        analysis_title = selected_company['name']
    
    if all_purchases:
        st.markdown(f"#### Purchase Analysis for {analysis_title}")
        
        # Summary metrics
        total_purchases = len(all_purchases)
        total_amount = sum(purchase['total_amount'] for purchase in all_purchases)
        total_quantity = sum(purchase['quantity'] for purchase in all_purchases)
        unique_books = len(set(purchase['book_id'] for purchase in all_purchases))
        unique_suppliers = len(set(purchase.get('supplier_name', 'Unknown') for purchase in all_purchases if purchase.get('supplier_name')))
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🛒 Total Purchases", total_purchases)
        
        with col2:
            st.metric("💰 Total Amount", format_currency(total_amount))
        
        with col3:
            st.metric("📦 Total Quantity", total_quantity)
        
        with col4:
            st.metric("📚 Unique Books", unique_books)
        
        with col5:
            st.metric("🏪 Suppliers", unique_suppliers)
        
        st.markdown("---")
        
        # Time-based analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Monthly Purchase Trends")
            
            # Create monthly summary
            monthly_data = {}
            for purchase in all_purchases:
                if purchase.get('purchase_date'):
                    try:
                        purchase_date = datetime.strptime(str(purchase['purchase_date']), '%Y-%m-%d')
                        month_key = purchase_date.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'amount': 0, 'quantity': 0, 'count': 0}
                        
                        monthly_data[month_key]['amount'] += purchase['total_amount']
                        monthly_data[month_key]['quantity'] += purchase['quantity']
                        monthly_data[month_key]['count'] += 1
                    except:
                        continue
            
            if monthly_data:
                monthly_df = pd.DataFrame.from_dict(monthly_data, orient='index')
                monthly_df.index = pd.to_datetime(monthly_df.index)
                monthly_df = monthly_df.sort_index()
                
                st.line_chart(monthly_df['amount'])
            else:
                st.info("No date-based data available for trends.")
        
        with col2:
            st.markdown("#### 🏪 Top Suppliers")
            
            # Supplier analysis
            supplier_data = {}
            for purchase in all_purchases:
                supplier = purchase.get('supplier_name', 'Unknown')
                if supplier not in supplier_data:
                    supplier_data[supplier] = {'amount': 0, 'quantity': 0, 'count': 0}
                
                supplier_data[supplier]['amount'] += purchase['total_amount']
                supplier_data[supplier]['quantity'] += purchase['quantity']
                supplier_data[supplier]['count'] += 1
            
            # Sort by amount
            sorted_suppliers = sorted(supplier_data.items(), key=lambda x: x[1]['amount'], reverse=True)[:10]
            
            if sorted_suppliers:
                supplier_df = pd.DataFrame([
                    {
                        'Supplier': supplier,
                        'Total Amount': format_currency(data['amount']),
                        'Purchases': data['count'],
                        'Quantity': data['quantity']
                    }
                    for supplier, data in sorted_suppliers
                ])
                st.dataframe(supplier_df, use_container_width=True)
            else:
                st.info("No supplier data available.")
        
        st.markdown("---")
        
        # Book-wise purchase analysis
        st.markdown("#### 📚 Most Purchased Books")
        
        book_purchases = {}
        for purchase in all_purchases:
            book_key = f"{purchase['book_name']} - {purchase.get('author', 'Unknown')}"
            if book_key not in book_purchases:
                book_purchases[book_key] = {'amount': 0, 'quantity': 0, 'count': 0}
            
            book_purchases[book_key]['amount'] += purchase['total_amount']
            book_purchases[book_key]['quantity'] += purchase['quantity']
            book_purchases[book_key]['count'] += 1
        
        # Sort by quantity
        sorted_books = sorted(book_purchases.items(), key=lambda x: x[1]['quantity'], reverse=True)[:10]
        
        if sorted_books:
            books_df = pd.DataFrame([
                {
                    'Book': book,
                    'Total Quantity': data['quantity'],
                    'Total Amount': format_currency(data['amount']),
                    'Purchases': data['count'],
                    'Avg Price': format_currency(data['amount'] / data['quantity']) if data['quantity'] > 0 else '₹0.00'
                }
                for book, data in sorted_books
            ])
            st.dataframe(books_df, use_container_width=True)
        
        # Export options
        st.markdown("---")
        st.markdown("#### 📥 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Purchase Summary", use_container_width=True):
                summary_data = [{
                    'Total Purchases': total_purchases,
                    'Total Amount': total_amount,
                    'Total Quantity': total_quantity,
                    'Unique Books': unique_books,
                    'Unique Suppliers': unique_suppliers,
                    'Analysis Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                
                csv = pd.DataFrame(summary_data).to_csv(index=False)
                st.download_button(
                    label="Download Summary CSV",
                    data=csv,
                    file_name=f"purchase_summary_{analysis_title.replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Export Detailed Records", use_container_width=True):
                detailed_data = []
                for purchase in all_purchases:
                    detailed_data.append({
                        'Date': purchase.get('purchase_date', ''),
                        'Book Name': purchase['book_name'],
                        'Author': purchase.get('author', ''),
                        'Supplier': purchase.get('supplier_name', ''),
                        'Quantity': purchase['quantity'],
                        'Price per Unit': purchase['price_per_unit'],
                        'Total Amount': purchase['total_amount'],
                        'Notes': purchase.get('notes', '')
                    })
                
                csv = pd.DataFrame(detailed_data).to_csv(index=False)
                st.download_button(
                    label="Download Detailed CSV",
                    data=csv,
                    file_name=f"purchase_details_{analysis_title.replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )
    else:
        st.info("No purchase records available for analysis.")

# Quick Actions
st.markdown("---")
st.markdown("### ⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📚 Manage Books", use_container_width=True):
        st.switch_page("pages/3_📚_Books.py")

with col2:
    if st.button("💰 Record Sale", use_container_width=True):
        st.switch_page("pages/6_💰_Sales.py")

with col3:
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_📊_Dashboard.py")
