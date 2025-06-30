import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.helpers import format_currency, generate_dashboard_metrics

st.set_page_config(
    page_title="Dashboard - Book Inventory",
    page_icon="📊",
    layout="wide"
)

from database.db_manager import DatabaseManager
import streamlit as st

@st.cache_resource
def get_database():
    conn_str = "postgresql://neondb_owner:npg_R81aBEUPvtMC@ep-fragrant-tooth-a1j6h75o-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    return DatabaseManager(conn_str)

db = get_database()
# ...rest of your page code...

import streamlit as st
import base64

# 📌 Load and encode logo image
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_data = get_base64_image("static/images/logo.png")

st.markdown(f"""
<div style="
    background: linear-gradient(90deg, #ffe600 0%, #ff9100 60%, #ff0000 100%);
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    display: flex;
    align-items: center;
">
    <div style="flex: 1;">
        <img src="data:image/png;base64,{img_data}" width="80" style="border-radius: 5px;" />
    </div>
    <div style="flex: 6; text-align: center;">
        <h1 style="
            font-size: 6rem;
            font-weight: bold;
            font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', sans-serif;
            margin: 0;
        ">प्रान्तीय युवा प्रकोष्ठ - सुल्तानपुर</h1>
        <p style="margin: 0; font-size: 2rem; font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;">
            पुस्तक स्टॉक व बिक्री रिपोर्ट डैशबोर्ड
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# Get dashboard metrics
metrics = generate_dashboard_metrics(db)

if not metrics:
    st.warning("No data available. Please add companies, books, and transactions to see dashboard metrics.")
    st.stop()

# Key Metrics Row
st.markdown("### 📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🏢 Total Companies",
        value=metrics['total_companies'],
        delta=None
    )

with col2:
    st.metric(
        label="📚 Total Books",
        value=metrics['total_books'],
        delta=None
    )

with col3:
    st.metric(
        label="👥 Total Customers",
        value=metrics['total_customers'],
        delta=None
    )

with col4:
    st.metric(
        label="💰 Total Sales",
        value=metrics['total_sales'],
        delta=None
    )

# Revenue and Stock Value Row
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="💵 Total Revenue",
        value=format_currency(metrics['total_revenue']),
        delta=None
    )

with col2:
    st.metric(
        label="📦 Stock Value",
        value=format_currency(metrics['stock_value']),
        delta=None
    )

st.markdown("---")

# Charts Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Sales by Company")
    
    # Get sales data by company
    companies = db.get_all_companies()
    company_sales = []
    
    for company in companies:
        sales = db.get_sales_by_company(company['id'])
        total_amount = sum(sale['final_amount'] for sale in sales)
        company_sales.append({
            'Company': company['name'],
            'Total Sales': total_amount,
            'Number of Sales': len(sales)
        })
    
    if company_sales:
        df_sales = pd.DataFrame(company_sales)
        fig_sales = px.bar(
            df_sales, 
            x='Company', 
            y='Total Sales',
            title="Sales Revenue by Company",
            color='Total Sales',
            color_continuous_scale='Blues'
        )
        fig_sales.update_layout(height=400)
        st.plotly_chart(fig_sales, use_container_width=True)
    else:
        st.info("No sales data available for chart.")

with col2:
    st.markdown("### 📚 Inventory Distribution")
    
    # Get inventory data by category
    books = db.get_all_books()
    if books:
        category_data = {}
        for book in books:
            category = book.get('category', 'Uncategorized')
            if category in category_data:
                category_data[category] += book['stock_quantity']
            else:
                category_data[category] = book['stock_quantity']
        
        if category_data:
            df_inventory = pd.DataFrame(
                list(category_data.items()), 
                columns=['Category', 'Stock Quantity']
            )
            fig_inventory = px.pie(
                df_inventory, 
                values='Stock Quantity', 
                names='Category',
                title="Stock Distribution by Category"
            )
            fig_inventory.update_layout(height=400)
            st.plotly_chart(fig_inventory, use_container_width=True)
        else:
            st.info("No inventory data available for chart.")
    else:
        st.info("No books available for inventory chart.")

st.markdown("---")

# Low Stock Alert
if metrics['low_stock_count'] > 0:
    st.markdown("### ⚠️ Low Stock Alert")
    st.warning(f"**{metrics['low_stock_count']} books are running low on stock!**")
    
    # Display low stock items
    low_stock_df = pd.DataFrame(metrics['low_stock_items'])
    if not low_stock_df.empty:
        display_columns = ['name', 'author', 'category', 'available_stock']
        st.dataframe(
            low_stock_df[display_columns].rename(columns={
                'name': 'Book Name',
                'author': 'Author',
                'category': 'Category',
                'available_stock': 'Available Stock'
            }),
            use_container_width=True
        )

# Recent Activity Section
st.markdown("### 📋 Recent Activity")

tab1, tab2, tab3 = st.tabs(["Recent Sales", "Recent Purchases", "Recent Books Added"])

with tab1:
    st.markdown("#### 💰 Latest Sales Transactions")
    
    # Get recent sales across all companies
    all_sales = []
    for company in companies:
        sales = db.get_sales_by_company(company['id'])
        all_sales.extend(sales)
    
    # Sort by date and get latest 10
    all_sales.sort(key=lambda x: x['created_at'], reverse=True)
    recent_sales = all_sales[:10]
    
    if recent_sales:
        sales_df = pd.DataFrame(recent_sales)
        display_sales = sales_df[['invoice_no', 'customer_name', 'company_name', 'final_amount', 'sale_date', 'payment_status']]
        display_sales.columns = ['Invoice No', 'Customer', 'Company', 'Amount', 'Date', 'Status']
        display_sales['Amount'] = display_sales['Amount'].apply(format_currency)
        st.dataframe(display_sales, use_container_width=True)
    else:
        st.info("No recent sales to display.")

with tab2:
    st.markdown("#### 🛒 Latest Purchase Transactions")
    
    # Get recent purchases across all companies
    all_purchases = []
    for company in companies:
        purchases = db.get_purchases_by_company(company['id'])
        all_purchases.extend(purchases)
    
    # Sort by date and get latest 10
    all_purchases.sort(key=lambda x: x['created_at'], reverse=True)
    recent_purchases = all_purchases[:10]
    
    if recent_purchases:
        purchase_df = pd.DataFrame(recent_purchases)
        display_purchases = purchase_df[['book_name', 'author', 'supplier_name', 'quantity', 'total_amount', 'purchase_date']]
        display_purchases.columns = ['Book Name', 'Author', 'Supplier', 'Quantity', 'Amount', 'Date']
        display_purchases['Amount'] = display_purchases['Amount'].apply(format_currency)
        st.dataframe(display_purchases, use_container_width=True)
    else:
        st.info("No recent purchases to display.")

with tab3:
    st.markdown("#### 📚 Recently Added Books")
    
    # Get recently added books (latest 10)
    books_query = '''SELECT b.*, c.name as company_name FROM books b
                     JOIN companies c ON b.company_id = c.id
                     ORDER BY b.created_at DESC LIMIT 10'''
    recent_books = db.execute_query(books_query)
    
    if recent_books:
        books_df = pd.DataFrame(recent_books)
        display_books = books_df[['name', 'author', 'category', 'company_name', 'stock_quantity', 'selling_price']]
        display_books.columns = ['Book Name', 'Author', 'Category', 'Company', 'Stock', 'Price']
        display_books['Price'] = display_books['Price'].apply(format_currency)
        st.dataframe(display_books, use_container_width=True)
    else:
        st.info("No recent books to display.")

# Quick Actions
st.markdown("---")
st.markdown("### ⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏢 Add Company", use_container_width=True):
        st.switch_page("pages/2_🏢_Companies.py")

with col2:
    if st.button("📚 Add Book", use_container_width=True):
        st.switch_page("pages/3_📚_Books.py")

with col3:
    if st.button("💰 New Sale", use_container_width=True):
        st.switch_page("pages/6_💰_Sales.py")

with col4:
    if st.button("📄 Generate Bill", use_container_width=True):
        st.switch_page("pages/7_📄_Billing.py")

# Auto-refresh option
st.markdown("---")
if st.button("🔄 Refresh Dashboard"):
    st.cache_resource.clear()
    st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666; margin-top: 2rem;">
    <hr>
    <p><strong>Premium Book Inventory & Billing System</strong></p>
    <p>Dashboard updated: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), unsafe_allow_html=True)

