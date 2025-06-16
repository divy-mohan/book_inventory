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
    page_title="Sales - Book Inventory",
    page_icon="💰",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# Initialize session state for cart
if 'sale_cart' not in st.session_state:
    st.session_state.sale_cart = []
if 'sale_customer_id' not in st.session_state:
    st.session_state.sale_customer_id = None
if 'sale_company_id' not in st.session_state:
    st.session_state.sale_company_id = None

# Page header
st.markdown("""
<div style="background: linear-gradient(90deg, #1f77b4 0%, #2e86de 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;">
    <h1>💰 Sales Management</h1>
    <p>Record sales transactions and manage customer orders</p>
</div>
""", unsafe_allow_html=True)

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before managing sales.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Sidebar for actions
with st.sidebar:
    st.markdown("### 💰 Sales Actions")
    action = st.selectbox(
        "Choose Action",
        ["View Sales", "Create New Sale", "Sales Analytics"]
    )
    
    st.markdown("### 🏢 Filter by Company")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )

# Main content based on selected action
if action == "View Sales":
    st.markdown("### 📋 Sales Records")
    
    # Get sales based on company filter
    if company_filter == "All Companies":
        all_sales = []
        for company in companies:
            sales = db.get_sales_by_company(company['id'])
            all_sales.extend(sales)
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        all_sales = db.get_sales_by_company(selected_company['id'])
    
    if all_sales:
        # Search and filter options
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search sales...", placeholder="Enter invoice number, customer name")
        
        with col2:
            payment_filter = st.selectbox("Payment Status", ["All", "Completed", "Pending", "Cancelled"])
        
        with col3:
            date_filter = st.selectbox("Date Range", ["All Time", "Today", "This Week", "This Month"])
        
        # Apply filters
        filtered_sales = all_sales
        
        if search_term:
            filtered_sales = filter_data(filtered_sales, search_term, ['invoice_no', 'customer_name'])
        
        if payment_filter != "All":
            filtered_sales = [sale for sale in filtered_sales if sale.get('payment_status') == payment_filter]
        
        # Apply date filter
        if date_filter != "All Time":
            today = datetime.now().date()
            if date_filter == "Today":
                filter_date = today
            elif date_filter == "This Week":
                filter_date = today - pd.Timedelta(days=7)
            elif date_filter == "This Month":
                filter_date = today.replace(day=1)
            
            if date_filter == "Today":
                filtered_sales = [
                    sale for sale in filtered_sales 
                    if sale.get('sale_date') and 
                    datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').date() == filter_date
                ]
            else:
                filtered_sales = [
                    sale for sale in filtered_sales 
                    if sale.get('sale_date') and 
                    datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').date() >= filter_date
                ]
        
        # Display sales count and totals
        st.write(f"📊 Showing **{len(filtered_sales)}** of **{len(all_sales)}** sales records")
        
        if filtered_sales:
            # Calculate totals
            total_amount = sum(sale['final_amount'] for sale in filtered_sales)
            total_discount = sum(sale.get('discount', 0) for sale in filtered_sales)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Total Revenue", format_currency(total_amount))
            with col2:
                st.metric("💸 Total Discounts", format_currency(total_discount))
            
            st.markdown("---")
            
            # Pagination
            page_data, current_page, total_pages = paginate_data(filtered_sales, 10)
            
            # Display sales
            for sale in page_data:
                # Determine status color
                status_color = "🟢" if sale.get('payment_status') == 'Completed' else "🟡" if sale.get('payment_status') == 'Pending' else "🔴"
                
                with st.expander(f"💰 {sale['invoice_no']} - {sale.get('customer_name', 'Walk-in Customer')} {status_color}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Customer:** {sale.get('customer_name', 'Walk-in Customer')}")
                        st.write(f"**Company:** {sale.get('company_name', 'N/A')}")
                        st.write(f"**Sale Date:** {format_date(sale['sale_date'])}")
                        st.write(f"**Payment Status:** {status_color} {sale.get('payment_status', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Total Amount:** {format_currency(sale['total_amount'])}")
                        st.write(f"**Discount:** {format_currency(sale.get('discount', 0))}")
                        st.write(f"**Tax:** {format_currency(sale.get('tax_amount', 0))}")
                        st.write(f"**Final Amount:** {format_currency(sale['final_amount'])}")
                    
                    with col3:
                        if sale.get('notes'):
                            st.write(f"**Notes:** {sale['notes']}")
                        st.write(f"**Created:** {format_date(sale.get('created_at', ''))}")
                        
                        # Action buttons
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"📄 View Invoice", key=f"view_{sale['id']}"):
                                # Store sale ID for invoice generation
                                st.session_state.view_sale_id = sale['id']
                                st.switch_page("pages/7_📄_Billing.py")
                        
                        with col_b:
                            if sale.get('payment_status') != 'Completed' and st.button(f"✅ Mark Paid", key=f"paid_{sale['id']}"):
                                if db.execute_update("UPDATE sales SET payment_status = 'Completed' WHERE id = ?", (sale['id'],)):
                                    show_success("Payment status updated!")
                                    st.rerun()
        else:
            st.info("No sales match your search criteria.")
    else:
        st.info("No sales recorded yet. Create your first sale!")

elif action == "Create New Sale":
    st.markdown("### ➕ Create New Sale")
    
    # Company selection
    if company_filter != "All Companies":
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        company_id = selected_company['id']
        st.session_state.sale_company_id = company_id
    else:
        company_options = {f"{comp['name']}": comp['id'] for comp in companies}
        selected_company_name = st.selectbox("Select Company *", list(company_options.keys()))
        company_id = company_options[selected_company_name]
        st.session_state.sale_company_id = company_id
    
    # Get customers and books for selected company
    customers = db.get_customers_by_company(company_id)
    books = db.get_books_by_company(company_id)
    
    if not books:
        st.warning("⚠️ No books available for this company. Please add books first.")
        if st.button("📚 Go to Books"):
            st.switch_page("pages/3_📚_Books.py")
        st.stop()
    
    # Customer selection
    st.markdown("#### 👤 Customer Information")
    
    customer_options = {"Walk-in Customer": None}
    if customers:
        customer_options.update({f"{cust['name']} - {cust.get('phone', 'No Phone')}": cust['id'] for cust in customers})
    
    selected_customer_key = st.selectbox("Select Customer", list(customer_options.keys()))
    customer_id = customer_options[selected_customer_key]
    st.session_state.sale_customer_id = customer_id
    
    if customer_id is None:
        st.info("💡 This is a walk-in sale. Customer details will not be recorded.")
    
    # Cart management
    st.markdown("#### 🛒 Add Items to Cart")
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        # Available books (with stock)
        available_books = [book for book in books if (book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)) > 0]
        
        if not available_books:
            st.warning("⚠️ No books with available stock.")
        else:
            book_options = {f"{book['name']} - {book.get('author', 'Unknown')} (Stock: {book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)})": book['id'] for book in available_books}
            selected_book_key = st.selectbox("Select Book", list(book_options.keys()))
            book_id = book_options[selected_book_key]
    
    with col2:
        if available_books:
            selected_book = next(book for book in available_books if book['id'] == book_id)
            max_qty = selected_book.get('stock_quantity', 0) - selected_book.get('damaged_quantity', 0) - selected_book.get('lost_quantity', 0)
            quantity = st.number_input("Quantity", min_value=1, max_value=max_qty, value=1)
    
    with col3:
        if available_books:
            price = st.number_input("Price", min_value=0.01, value=float(selected_book.get('selling_price', 0)), step=0.01)
    
    with col4:
        if available_books and st.button("🛒 Add to Cart", use_container_width=True):
            # Check if book already in cart
            existing_item = next((item for item in st.session_state.sale_cart if item['book_id'] == book_id), None)
            
            if existing_item:
                # Update quantity
                total_qty = existing_item['quantity'] + quantity
                if total_qty <= max_qty:
                    existing_item['quantity'] = total_qty
                    existing_item['total_price'] = total_qty * existing_item['price_per_unit']
                    show_success(f"Updated quantity for {selected_book['name']}")
                else:
                    show_error(f"Cannot add {quantity} more. Maximum available: {max_qty - existing_item['quantity']}")
            else:
                # Add new item
                cart_item = {
                    'book_id': book_id,
                    'book_name': selected_book['name'],
                    'author': selected_book.get('author', 'Unknown'),
                    'quantity': quantity,
                    'price_per_unit': price,
                    'total_price': quantity * price,
                    'max_stock': max_qty
                }
                st.session_state.sale_cart.append(cart_item)
                show_success(f"Added {selected_book['name']} to cart")
            
            st.rerun()
    
    # Display cart
    if st.session_state.sale_cart:
        st.markdown("#### 🛒 Cart Items")
        
        cart_data = []
        for i, item in enumerate(st.session_state.sale_cart):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{item['book_name']}**")
                st.write(f"*{item['author']}*")
            
            with col2:
                new_qty = st.number_input(f"Qty", min_value=1, max_value=item['max_stock'], 
                                        value=item['quantity'], key=f"qty_{i}")
                if new_qty != item['quantity']:
                    item['quantity'] = new_qty
                    item['total_price'] = new_qty * item['price_per_unit']
                    st.rerun()
            
            with col3:
                new_price = st.number_input(f"Price", min_value=0.01, 
                                          value=item['price_per_unit'], step=0.01, key=f"price_{i}")
                if new_price != item['price_per_unit']:
                    item['price_per_unit'] = new_price
                    item['total_price'] = item['quantity'] * new_price
                    st.rerun()
            
            with col4:
                st.write(f"**{format_currency(item['total_price'])}**")
            
            with col5:
                st.write(f"Max: {item['max_stock']}")
            
            with col6:
                if st.button("🗑️", key=f"remove_{i}", help="Remove item"):
                    st.session_state.sale_cart.pop(i)
                    st.rerun()
            
            cart_data.append(item)
        
        # Cart totals
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        subtotal = sum(item['total_price'] for item in st.session_state.sale_cart)
        
        with col1:
            discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0, step=0.01)
        
        with col2:
            tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.01)
            tax_amount = (subtotal - discount) * tax_rate / 100
        
        with col3:
            final_amount = subtotal - discount + tax_amount
            st.metric("Final Amount", format_currency(final_amount))
        
        # Sale details
        st.markdown("#### 📝 Sale Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            payment_status = st.selectbox("Payment Status", ["Completed", "Pending"])
            sale_date = st.date_input("Sale Date", value=date.today())
        
        with col2:
            notes = st.text_area("Notes", placeholder="Additional notes for this sale")
        
        # Generate invoice number
        invoice_no = db.generate_invoice_number(company_id)
        st.info(f"📄 Invoice Number: **{invoice_no}**")
        
        # Complete sale
        if st.button("✅ Complete Sale", type="primary", use_container_width=True):
            if st.session_state.sale_cart:
                # Prepare sale data
                sale_data = {
                    'company_id': company_id,
                    'customer_id': customer_id,
                    'invoice_no': invoice_no,
                    'sale_date': sale_date,
                    'total_amount': subtotal,
                    'discount': discount,
                    'tax_amount': tax_amount,
                    'final_amount': final_amount,
                    'payment_status': payment_status,
                    'notes': notes.strip()
                }
                
                # Prepare sale items
                sale_items = []
                for item in st.session_state.sale_cart:
                    sale_items.append({
                        'book_id': item['book_id'],
                        'quantity': item['quantity'],
                        'price_per_unit': item['price_per_unit'],
                        'total_price': item['total_price']
                    })
                
                # Save sale
                if db.add_sale(sale_data, sale_items):
                    show_success(f"Sale completed successfully! Invoice: {invoice_no}")
                    st.balloons()
                    
                    # Clear cart
                    st.session_state.sale_cart = []
                    
                    # Option to generate invoice
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📄 Generate Invoice PDF"):
                            st.session_state.view_sale_id = invoice_no
                            st.switch_page("pages/7_📄_Billing.py")
                    
                    with col2:
                        if st.button("➕ Create Another Sale"):
                            st.rerun()
                else:
                    show_error("Failed to complete sale. Please try again.")
            else:
                show_error("Cart is empty. Please add items before completing the sale.")
    
    else:
        st.info("🛒 Cart is empty. Add books to create a sale.")
        
        # Quick add popular books
        if available_books:
            st.markdown("#### 🔥 Quick Add Popular Books")
            
            # Get most sold books (this is a simplified version)
            popular_books = available_books[:6]  # Show first 6 available books
            
            cols = st.columns(3)
            for i, book in enumerate(popular_books):
                with cols[i % 3]:
                    if st.button(f"📖 {book['name'][:20]}{'...' if len(book['name']) > 20 else ''}", 
                               key=f"quick_{book['id']}", use_container_width=True):
                        # Quick add with default values
                        cart_item = {
                            'book_id': book['id'],
                            'book_name': book['name'],
                            'author': book.get('author', 'Unknown'),
                            'quantity': 1,
                            'price_per_unit': book.get('selling_price', 0),
                            'total_price': book.get('selling_price', 0),
                            'max_stock': book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
                        }
                        st.session_state.sale_cart.append(cart_item)
                        st.rerun()

elif action == "Sales Analytics":
    st.markdown("### 📊 Sales Analytics")
    
    # Get sales based on company filter
    if company_filter == "All Companies":
        all_sales = []
        for company in companies:
            sales = db.get_sales_by_company(company['id'])
            all_sales.extend(sales)
        analysis_title = "All Companies"
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        all_sales = db.get_sales_by_company(selected_company['id'])
        analysis_title = selected_company['name']
    
    if all_sales:
        st.markdown(f"#### Sales Performance for {analysis_title}")
        
        # Summary metrics
        total_sales = len(all_sales)
        total_revenue = sum(sale['final_amount'] for sale in all_sales)
        total_discount = sum(sale.get('discount', 0) for sale in all_sales)
        total_tax = sum(sale.get('tax_amount', 0) for sale in all_sales)
        completed_sales = len([sale for sale in all_sales if sale.get('payment_status') == 'Completed'])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💰 Total Sales", total_sales)
        
        with col2:
            st.metric("💵 Total Revenue", format_currency(total_revenue))
        
        with col3:
            st.metric("💸 Total Discounts", format_currency(total_discount))
        
        with col4:
            st.metric("🏛️ Total Tax", format_currency(total_tax))
        
        with col5:
            completion_rate = (completed_sales / total_sales * 100) if total_sales > 0 else 0
            st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
        
        st.markdown("---")
        
        # Time-based analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Daily Sales Trends")
            
            # Create daily summary
            daily_data = {}
            for sale in all_sales:
                if sale.get('sale_date'):
                    try:
                        sale_date = datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').date()
                        date_key = sale_date.strftime('%Y-%m-%d')
                        
                        if date_key not in daily_data:
                            daily_data[date_key] = {'revenue': 0, 'count': 0}
                        
                        daily_data[date_key]['revenue'] += sale['final_amount']
                        daily_data[date_key]['count'] += 1
                    except:
                        continue
            
            if daily_data:
                daily_df = pd.DataFrame.from_dict(daily_data, orient='index')
                daily_df.index = pd.to_datetime(daily_df.index)
                daily_df = daily_df.sort_index().tail(30)  # Last 30 days
                
                st.line_chart(daily_df['revenue'])
            else:
                st.info("No date-based data available for trends.")
        
        with col2:
            st.markdown("#### 🎯 Payment Status Distribution")
            
            # Payment status analysis
            status_data = {}
            for sale in all_sales:
                status = sale.get('payment_status', 'Unknown')
                if status not in status_data:
                    status_data[status] = {'count': 0, 'amount': 0}
                
                status_data[status]['count'] += 1
                status_data[status]['amount'] += sale['final_amount']
            
            if status_data:
                status_df = pd.DataFrame.from_dict(status_data, orient='index')
                st.bar_chart(status_df['count'])
            else:
                st.info("No payment status data available.")
        
        st.markdown("---")
        
        # Customer analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👥 Top Customers")
            
            customer_sales = {}
            for sale in all_sales:
                customer = sale.get('customer_name', 'Walk-in Customer')
                if customer not in customer_sales:
                    customer_sales[customer] = {'amount': 0, 'count': 0}
                
                customer_sales[customer]['amount'] += sale['final_amount']
                customer_sales[customer]['count'] += 1
            
            # Sort by amount
            sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1]['amount'], reverse=True)[:10]
            
            if sorted_customers:
                customer_df = pd.DataFrame([
                    {
                        'Customer': customer,
                        'Total Amount': format_currency(data['amount']),
                        'Orders': data['count'],
                        'Avg Order': format_currency(data['amount'] / data['count']) if data['count'] > 0 else '₹0.00'
                    }
                    for customer, data in sorted_customers
                ])
                st.dataframe(customer_df, use_container_width=True)
        
        with col2:
            st.markdown("#### 📊 Sales by Month")
            
            # Monthly analysis
            monthly_data = {}
            for sale in all_sales:
                if sale.get('sale_date'):
                    try:
                        sale_date = datetime.strptime(str(sale['sale_date']), '%Y-%m-%d')
                        month_key = sale_date.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'revenue': 0, 'count': 0}
                        
                        monthly_data[month_key]['revenue'] += sale['final_amount']
                        monthly_data[month_key]['count'] += 1
                    except:
                        continue
            
            if monthly_data:
                monthly_df = pd.DataFrame.from_dict(monthly_data, orient='index')
                monthly_df.index = pd.to_datetime(monthly_df.index)
                monthly_df = monthly_df.sort_index()
                
                st.bar_chart(monthly_df['revenue'])
        
        # Export options
        st.markdown("---")
        st.markdown("#### 📥 Export Sales Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Sales Summary", use_container_width=True):
                summary_data = [{
                    'Total Sales': total_sales,
                    'Total Revenue': total_revenue,
                    'Total Discounts': total_discount,
                    'Total Tax': total_tax,
                    'Completed Sales': completed_sales,
                    'Completion Rate': f"{completion_rate:.1f}%",
                    'Analysis Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                
                csv = pd.DataFrame(summary_data).to_csv(index=False)
                st.download_button(
                    label="Download Summary CSV",
                    data=csv,
                    file_name=f"sales_summary_{analysis_title.replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Export Detailed Records", use_container_width=True):
                detailed_data = []
                for sale in all_sales:
                    detailed_data.append({
                        'Invoice No': sale['invoice_no'],
                        'Date': sale.get('sale_date', ''),
                        'Customer': sale.get('customer_name', 'Walk-in Customer'),
                        'Total Amount': sale['total_amount'],
                        'Discount': sale.get('discount', 0),
                        'Tax': sale.get('tax_amount', 0),
                        'Final Amount': sale['final_amount'],
                        'Payment Status': sale.get('payment_status', ''),
                        'Notes': sale.get('notes', '')
                    })
                
                csv = pd.DataFrame(detailed_data).to_csv(index=False)
                st.download_button(
                    label="Download Detailed CSV",
                    data=csv,
                    file_name=f"sales_details_{analysis_title.replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )
    else:
        st.info("No sales records available for analysis.")

# Clear cart button
if st.session_state.sale_cart:
    st.markdown("---")
    if st.button("🗑️ Clear Cart", type="secondary"):
        st.session_state.sale_cart = []
        show_success("Cart cleared!")
        st.rerun()
