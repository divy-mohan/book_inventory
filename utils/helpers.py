import streamlit as st
from datetime import datetime, date
import pandas as pd
from typing import List, Dict, Any, Optional

def init_session_state():
    """Initialize session state variables"""
    if 'selected_company' not in st.session_state:
        st.session_state.selected_company = None
    if 'cart_items' not in st.session_state:
        st.session_state.cart_items = []
    if 'invoice_counter' not in st.session_state:
        st.session_state.invoice_counter = 1

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def format_date(date_obj) -> str:
    """Format date for display"""
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, (date, datetime)):
        return date_obj.strftime("%d/%m/%Y")
    return str(date_obj)

def validate_email(email: str) -> bool:
    """Basic email validation"""
    return '@' in email and '.' in email.split('@')[1]

def validate_phone(phone: str) -> bool:
    """Basic phone validation"""
    clean_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
    return clean_phone.isdigit() and len(clean_phone) >= 10

def show_success(message: str):
    """Show success message"""
    st.success(f"✅ {message}")

def show_error(message: str):
    """Show error message"""
    st.error(f"❌ {message}")

def show_warning(message: str):
    """Show warning message"""
    st.warning(f"⚠️ {message}")

def show_info(message: str):
    """Show info message"""
    st.info(f"ℹ️ {message}")

def create_download_link(file_path: str, file_name: str = ""):
    """Create download link for file"""
    if not file_name:
        file_name = file_path.split('/')[-1]
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        st.download_button(
            label=f"📥 Download {file_name}",
            data=file_data,
            file_name=file_name,
            mime='application/pdf'
        )
        return True
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return False

def paginate_data(data: List[Dict], page_size: int = 10):
    """Paginate data for display"""
    if not data:
        return [], 0, 0
    
    total_pages = len(data) // page_size + (1 if len(data) % page_size > 0 else 0)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()
    
    with col2:
        st.write(f"Page {st.session_state.current_page} of {total_pages}")
    
    with col3:
        if st.button("Next ➡️") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()
    
    # Get data for current page
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = data[start_idx:end_idx]
    
    return page_data, st.session_state.current_page, total_pages

def filter_data(data: List[Dict], search_term: str, search_fields: List[str]) -> List[Dict]:
    """Filter data based on search term"""
    if not search_term:
        return data
    
    search_term = search_term.lower()
    filtered_data = []
    
    for item in data:
        for field in search_fields:
            if field in item and search_term in str(item[field]).lower():
                filtered_data.append(item)
                break
    
    return filtered_data

def export_to_csv(data: List[Dict], filename: str = "") -> bytes:
    """Export data to CSV"""
    if not filename:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def calculate_stock_value(books: List[Dict]) -> Dict[str, float]:
    """Calculate total stock value"""
    total_purchase_value = 0
    total_selling_value = 0
    total_profit = 0
    
    for book in books:
        available_stock = book['stock_quantity'] - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
        purchase_value = available_stock * book.get('purchase_price', 0)
        selling_value = available_stock * book.get('selling_price', 0)
        
        total_purchase_value += purchase_value
        total_selling_value += selling_value
        total_profit += (selling_value - purchase_value)
    
    return {
        'total_purchase_value': total_purchase_value,
        'total_selling_value': total_selling_value,
        'total_profit': total_profit
    }

def get_low_stock_books(books: List[Dict], threshold: int = 5) -> List[Dict]:
    """Get books with low stock"""
    low_stock_books = []
    
    for book in books:
        available_stock = book['stock_quantity'] - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
        if available_stock <= threshold:
            low_stock_books.append({
                **book,
                'available_stock': available_stock
            })
    
    return low_stock_books

def searchable_selectbox(label: str, options: List[str], key: str = "", placeholder: str = "Type to search...") -> Optional[str]:
    """Create a searchable selectbox with filtering"""
    if not options:
        st.warning(f"No options available for {label}")
        return None
    
    # Create search input
    search_key = f"{key}_search" if key else f"{label.lower().replace(' ', '_')}_search"
    search_term = st.text_input(f"🔍 Search {label}", placeholder=placeholder, key=search_key)
    
    # Filter options based on search
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
        if not filtered_options:
            st.warning(f"No {label.lower()} found matching '{search_term}'")
            return None
    else:
        filtered_options = options
    
    # Show selectbox with filtered options
    if filtered_options:
        return st.selectbox(f"Select {label}", filtered_options, key=key if key else None)
    
    return None

def searchable_multiselect(label: str, options: List[str], default: List[str] = [], key: str = "", placeholder: str = "Type to search...") -> List[str]:
    """Create a searchable multiselect with filtering"""
    if not options:
        st.warning(f"No options available for {label}")
        return []
    
    # Create search input
    search_key = f"{key}_search" if key else f"{label.lower().replace(' ', '_')}_search"
    search_term = st.text_input(f"🔍 Search {label}", placeholder=placeholder, key=search_key)
    
    # Filter options based on search
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
    else:
        filtered_options = options
    
    # Show multiselect with filtered options
    if filtered_options:
        return st.multiselect(f"Select {label}", filtered_options, default=default, key=key if key else None)
    
    return []

def generate_dashboard_metrics(db):
    """Generate metrics for dashboard"""
    try:
        # Total companies
        companies = db.get_all_companies()
        total_companies = len(companies)
        
        # Total books
        books = db.get_all_books()
        total_books = len(books)
        
        # Total customers
        customers = db.get_all_customers()
        total_customers = len(customers)
        
        # Total sales
        all_sales = []
        for company in companies:
            sales = db.get_sales_by_company(company['id'])
            all_sales.extend(sales)
        
        total_sales = len(all_sales)
        total_revenue = sum(sale['final_amount'] for sale in all_sales)
        
        # Stock value
        stock_metrics = calculate_stock_value(books)
        
        # Low stock items
        low_stock_items = get_low_stock_books(books)
        
        return {
            'total_companies': total_companies,
            'total_books': total_books,
            'total_customers': total_customers,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'stock_value': stock_metrics['total_selling_value'],
            'low_stock_count': len(low_stock_items),
            'low_stock_items': low_stock_items
        }
    
    except Exception as e:
        st.error(f"Error generating dashboard metrics: {e}")
        return {}
