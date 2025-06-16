import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.pdf_generator import PDFInvoiceGenerator
from utils.helpers import (
    format_currency, format_date, show_success, show_error,
    calculate_stock_value, get_low_stock_books, export_to_csv
)

st.set_page_config(
    page_title="Reports - Book Inventory",
    page_icon="📈",
    layout="wide"
)

# Initialize database and PDF generator
@st.cache_resource
def get_database():
    return DatabaseManager()

@st.cache_resource
def get_pdf_generator():
    return PDFInvoiceGenerator()

db = get_database()
pdf_generator = get_pdf_generator()

# Page header
st.markdown("""
<div style="background: linear-gradient(90deg, #1f77b4 0%, #2e86de 100%); 
            padding: 2rem; border-radius: 10px; margin-bottom: 2rem; text-align: center; color: white;">
    <h1>📈 Business Reports & Analytics</h1>
    <p>Comprehensive insights and detailed business reports</p>
</div>
""", unsafe_allow_html=True)

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before viewing reports.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Sidebar for report selection
with st.sidebar:
    st.markdown("### 📊 Report Types")
    report_type = st.selectbox(
        "Choose Report",
        [
            "Business Overview",
            "Sales Analysis",
            "Inventory Report",
            "Customer Analysis",
            "Financial Summary",
            "Stock Movement",
            "Profit & Loss"
        ]
    )
    
    st.markdown("### 🏢 Company Filter")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )
    
    st.markdown("### 📅 Date Range")
    date_range = st.selectbox(
        "Select Period",
        ["All Time", "Today", "This Week", "This Month", "This Quarter", "This Year", "Custom Range"]
    )
    
    if date_range == "Custom Range":
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        end_date = st.date_input("End Date", value=date.today())
    else:
        start_date = None
        end_date = None

# Helper function to filter data by date range
def filter_by_date_range(data, date_field='sale_date'):
    if not data:
        return data
    
    today = date.today()
    
    if date_range == "Today":
        return [item for item in data if item.get(date_field) == str(today)]
    elif date_range == "This Week":
        week_start = today - timedelta(days=today.weekday())
        return [item for item in data if item.get(date_field) and 
                datetime.strptime(str(item[date_field]), '%Y-%m-%d').date() >= week_start]
    elif date_range == "This Month":
        month_start = today.replace(day=1)
        return [item for item in data if item.get(date_field) and 
                datetime.strptime(str(item[date_field]), '%Y-%m-%d').date() >= month_start]
    elif date_range == "This Quarter":
        quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
        return [item for item in data if item.get(date_field) and 
                datetime.strptime(str(item[date_field]), '%Y-%m-%d').date() >= quarter_start]
    elif date_range == "This Year":
        year_start = today.replace(month=1, day=1)
        return [item for item in data if item.get(date_field) and 
                datetime.strptime(str(item[date_field]), '%Y-%m-%d').date() >= year_start]
    elif date_range == "Custom Range" and start_date and end_date:
        return [item for item in data if item.get(date_field) and 
                start_date <= datetime.strptime(str(item[date_field]), '%Y-%m-%d').date() <= end_date]
    else:
        return data

# Get filtered data based on company selection
def get_company_data():
    if company_filter == "All Companies":
        all_companies = companies
        all_sales = []
        all_purchases = []
        all_books = []
        all_customers = []
        
        for company in companies:
            sales = db.get_sales_by_company(company['id'])
            purchases = db.get_purchases_by_company(company['id'])
            books = db.get_books_by_company(company['id'])
            customers = db.get_customers_by_company(company['id'])
            
            all_sales.extend(sales)
            all_purchases.extend(purchases)
            all_books.extend(books)
            all_customers.extend(customers)
        
        return {
            'companies': all_companies,
            'sales': all_sales,
            'purchases': all_purchases,
            'books': all_books,
            'customers': all_customers,
            'title': 'All Companies'
        }
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        return {
            'companies': [selected_company],
            'sales': db.get_sales_by_company(selected_company['id']),
            'purchases': db.get_purchases_by_company(selected_company['id']),
            'books': db.get_books_by_company(selected_company['id']),
            'customers': db.get_customers_by_company(selected_company['id']),
            'title': selected_company['name']
        }

# Get data
company_data = get_company_data()

# Apply date filters
filtered_sales = filter_by_date_range(company_data['sales'], 'sale_date')
filtered_purchases = filter_by_date_range(company_data['purchases'], 'purchase_date')

# Main report content
if report_type == "Business Overview":
    st.markdown(f"### 📊 Business Overview - {company_data['title']}")
    st.markdown(f"**Period:** {date_range}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏢 Companies", len(company_data['companies']))
        st.metric("📚 Total Books", len(company_data['books']))
    
    with col2:
        st.metric("👥 Customers", len(company_data['customers']))
        st.metric("💰 Total Sales", len(filtered_sales))
    
    with col3:
        total_revenue = sum(sale['final_amount'] for sale in filtered_sales)
        st.metric("💵 Revenue", format_currency(total_revenue))
    
    with col4:
        total_purchase_cost = sum(purchase['total_amount'] for purchase in filtered_purchases)
        st.metric("🛒 Purchase Cost", format_currency(total_purchase_cost))
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Sales Trend")
        if filtered_sales:
            # Daily sales data
            daily_sales = {}
            for sale in filtered_sales:
                if sale.get('sale_date'):
                    sale_date = sale['sale_date']
                    if sale_date not in daily_sales:
                        daily_sales[sale_date] = {'revenue': 0, 'count': 0}
                    daily_sales[sale_date]['revenue'] += sale['final_amount']
                    daily_sales[sale_date]['count'] += 1
            
            if daily_sales:
                sales_df = pd.DataFrame.from_dict(daily_sales, orient='index')
                sales_df.index = pd.to_datetime(sales_df.index)
                sales_df = sales_df.sort_index()
                
                fig = px.line(sales_df, y='revenue', title='Daily Sales Revenue')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sales data for chart")
        else:
            st.info("No sales in selected period")
    
    with col2:
        st.markdown("#### 📦 Stock Distribution")
        if company_data['books']:
            category_stock = {}
            for book in company_data['books']:
                category = book.get('category', 'Uncategorized')
                available_stock = book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
                
                if category not in category_stock:
                    category_stock[category] = 0
                category_stock[category] += available_stock
            
            if category_stock:
                fig = px.pie(
                    values=list(category_stock.values()),
                    names=list(category_stock.keys()),
                    title='Stock by Category'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No stock data available")
        else:
            st.info("No books data available")
    
    # Top performers
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top Selling Books")
        if filtered_sales:
            # Get sale items for top books
            book_sales = {}
            for sale in filtered_sales:
                sale_details = db.get_sale_details(sale['id'])
                for item in sale_details['items']:
                    book_key = f"{item['book_name']} - {item.get('author', 'Unknown')}"
                    if book_key not in book_sales:
                        book_sales[book_key] = {'quantity': 0, 'revenue': 0}
                    book_sales[book_key]['quantity'] += item['quantity']
                    book_sales[book_key]['revenue'] += item['total_price']
            
            if book_sales:
                top_books = sorted(book_sales.items(), key=lambda x: x[1]['quantity'], reverse=True)[:5]
                top_books_df = pd.DataFrame([
                    {
                        'Book': book,
                        'Quantity Sold': data['quantity'],
                        'Revenue': format_currency(data['revenue'])
                    }
                    for book, data in top_books
                ])
                st.dataframe(top_books_df, use_container_width=True)
            else:
                st.info("No book sales data")
        else:
            st.info("No sales in selected period")
    
    with col2:
        st.markdown("#### 👥 Top Customers")
        if filtered_sales:
            customer_data = {}
            for sale in filtered_sales:
                customer = sale.get('customer_name', 'Walk-in Customer')
                if customer not in customer_data:
                    customer_data[customer] = {'orders': 0, 'revenue': 0}
                customer_data[customer]['orders'] += 1
                customer_data[customer]['revenue'] += sale['final_amount']
            
            if customer_data:
                top_customers = sorted(customer_data.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
                top_customers_df = pd.DataFrame([
                    {
                        'Customer': customer,
                        'Orders': data['orders'],
                        'Revenue': format_currency(data['revenue'])
                    }
                    for customer, data in top_customers
                ])
                st.dataframe(top_customers_df, use_container_width=True)
        else:
            st.info("No customer data")

elif report_type == "Sales Analysis":
    st.markdown(f"### 💰 Sales Analysis - {company_data['title']}")
    st.markdown(f"**Period:** {date_range}")
    
    if not filtered_sales:
        st.info("No sales data available for the selected period.")
    else:
        # Sales metrics
        total_sales = len(filtered_sales)
        total_revenue = sum(sale['final_amount'] for sale in filtered_sales)
        total_discount = sum(sale.get('discount', 0) for sale in filtered_sales)
        average_order_value = total_revenue / total_sales if total_sales > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🛒 Total Orders", total_sales)
        
        with col2:
            st.metric("💰 Total Revenue", format_currency(total_revenue))
        
        with col3:
            st.metric("💸 Total Discounts", format_currency(total_discount))
        
        with col4:
            st.metric("📊 Avg Order Value", format_currency(average_order_value))
        
        # Sales trends
        st.markdown("#### 📈 Sales Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly trend
            monthly_sales = {}
            for sale in filtered_sales:
                if sale.get('sale_date'):
                    month_key = datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').strftime('%Y-%m')
                    if month_key not in monthly_sales:
                        monthly_sales[month_key] = {'revenue': 0, 'count': 0}
                    monthly_sales[month_key]['revenue'] += sale['final_amount']
                    monthly_sales[month_key]['count'] += 1
            
            if monthly_sales:
                monthly_df = pd.DataFrame.from_dict(monthly_sales, orient='index')
                monthly_df.index = pd.to_datetime(monthly_df.index)
                monthly_df = monthly_df.sort_index()
                
                fig = px.bar(monthly_df, y='revenue', title='Monthly Sales Revenue')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Payment status distribution
            payment_status = {}
            for sale in filtered_sales:
                status = sale.get('payment_status', 'Unknown')
                if status not in payment_status:
                    payment_status[status] = {'count': 0, 'amount': 0}
                payment_status[status]['count'] += 1
                payment_status[status]['amount'] += sale['final_amount']
            
            if payment_status:
                fig = px.pie(
                    values=[data['count'] for data in payment_status.values()],
                    names=list(payment_status.keys()),
                    title='Payment Status Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed sales table
        st.markdown("#### 📋 Detailed Sales Data")
        
        sales_table_data = []
        for sale in filtered_sales:
            sales_table_data.append({
                'Invoice No': sale['invoice_no'],
                'Date': format_date(sale['sale_date']),
                'Customer': sale.get('customer_name', 'Walk-in Customer'),
                'Amount': format_currency(sale['final_amount']),
                'Discount': format_currency(sale.get('discount', 0)),
                'Status': sale.get('payment_status', 'N/A')
            })
        
        if sales_table_data:
            st.dataframe(sales_table_data, use_container_width=True)
            
            # Export button
            if st.button("📥 Export Sales Data"):
                csv_data = export_to_csv(sales_table_data, f"sales_analysis_{company_data['title'].replace(' ', '_').lower()}.csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"sales_analysis_{company_data['title'].replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )

elif report_type == "Inventory Report":
    st.markdown(f"### 📚 Inventory Report - {company_data['title']}")
    
    if not company_data['books']:
        st.info("No inventory data available.")
    else:
        # Inventory metrics
        total_books = len(company_data['books'])
        total_stock = sum(book.get('stock_quantity', 0) for book in company_data['books'])
        stock_metrics = calculate_stock_value(company_data['books'])
        low_stock_books = get_low_stock_books(company_data['books'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📖 Total Book Types", total_books)
        
        with col2:
            st.metric("📦 Total Stock Units", total_stock)
        
        with col3:
            st.metric("💰 Stock Value", format_currency(stock_metrics['total_selling_value']))
        
        with col4:
            st.metric("⚠️ Low Stock Items", len(low_stock_books))
        
        # Stock analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Stock by Category")
            category_analysis = {}
            for book in company_data['books']:
                category = book.get('category', 'Uncategorized')
                if category not in category_analysis:
                    category_analysis[category] = {
                        'books': 0,
                        'stock': 0,
                        'value': 0
                    }
                
                available_stock = book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
                category_analysis[category]['books'] += 1
                category_analysis[category]['stock'] += available_stock
                category_analysis[category]['value'] += available_stock * book.get('selling_price', 0)
            
            category_df = pd.DataFrame([
                {
                    'Category': category,
                    'Books': data['books'],
                    'Stock': data['stock'],
                    'Value': format_currency(data['value'])
                }
                for category, data in category_analysis.items()
            ])
            st.dataframe(category_df, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Stock Value Distribution")
            if category_analysis:
                fig = px.bar(
                    x=list(category_analysis.keys()),
                    y=[data['value'] for data in category_analysis.values()],
                    title='Stock Value by Category'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Low stock alert
        if low_stock_books:
            st.markdown("#### ⚠️ Low Stock Alert")
            st.warning(f"**{len(low_stock_books)} books are running low on stock!**")
            
            low_stock_df = pd.DataFrame([
                {
                    'Book Name': book['name'],
                    'Author': book.get('author', 'Unknown'),
                    'Category': book.get('category', 'Uncategorized'),
                    'Available Stock': book['available_stock'],
                    'Selling Price': format_currency(book.get('selling_price', 0))
                }
                for book in low_stock_books
            ])
            st.dataframe(low_stock_df, use_container_width=True)
        
        # Complete inventory table
        st.markdown("#### 📋 Complete Inventory")
        
        inventory_data = []
        for book in company_data['books']:
            available_stock = book.get('stock_quantity', 0) - book.get('damaged_quantity', 0) - book.get('lost_quantity', 0)
            inventory_data.append({
                'Book Name': book['name'],
                'Author': book.get('author', 'Unknown'),
                'Category': book.get('category', 'Uncategorized'),
                'Language': book.get('language', 'English'),
                'Total Stock': book.get('stock_quantity', 0),
                'Available': available_stock,
                'Damaged': book.get('damaged_quantity', 0),
                'Lost': book.get('lost_quantity', 0),
                'Purchase Price': format_currency(book.get('purchase_price', 0)),
                'Selling Price': format_currency(book.get('selling_price', 0)),
                'Stock Value': format_currency(available_stock * book.get('selling_price', 0))
            })
        
        if inventory_data:
            st.dataframe(inventory_data, use_container_width=True)
            
            # Export button
            if st.button("📥 Export Inventory Report"):
                csv_data = export_to_csv(inventory_data, f"inventory_report_{company_data['title'].replace(' ', '_').lower()}.csv")
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"inventory_report_{company_data['title'].replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )

elif report_type == "Customer Analysis":
    st.markdown(f"### 👥 Customer Analysis - {company_data['title']}")
    st.markdown(f"**Period:** {date_range}")
    
    if not company_data['customers'] and not filtered_sales:
        st.info("No customer data available.")
    else:
        # Customer metrics
        total_customers = len(company_data['customers'])
        customers_with_orders = len(set(sale.get('customer_id') for sale in filtered_sales if sale.get('customer_id')))
        total_customer_revenue = sum(sale['final_amount'] for sale in filtered_sales if sale.get('customer_id'))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Total Customers", total_customers)
        
        with col2:
            st.metric("🛒 Active Customers", customers_with_orders)
        
        with col3:
            st.metric("💰 Customer Revenue", format_currency(total_customer_revenue))
        
        # Customer analysis
        customer_analysis = {}
        
        # Analyze customer purchases
        for sale in filtered_sales:
            customer_id = sale.get('customer_id')
            customer_name = sale.get('customer_name', 'Walk-in Customer')
            
            if customer_name not in customer_analysis:
                customer_analysis[customer_name] = {
                    'orders': 0,
                    'revenue': 0,
                    'last_purchase': None
                }
            
            customer_analysis[customer_name]['orders'] += 1
            customer_analysis[customer_name]['revenue'] += sale['final_amount']
            
            # Track last purchase date
            if sale.get('sale_date'):
                if (customer_analysis[customer_name]['last_purchase'] is None or 
                    sale['sale_date'] > customer_analysis[customer_name]['last_purchase']):
                    customer_analysis[customer_name]['last_purchase'] = sale['sale_date']
        
        if customer_analysis:
            # Top customers
            st.markdown("#### 🏆 Top Customers by Revenue")
            
            top_customers = sorted(customer_analysis.items(), key=lambda x: x[1]['revenue'], reverse=True)
            
            top_customers_df = pd.DataFrame([
                {
                    'Customer': customer,
                    'Orders': data['orders'],
                    'Total Revenue': format_currency(data['revenue']),
                    'Avg Order Value': format_currency(data['revenue'] / data['orders']) if data['orders'] > 0 else '₹0.00',
                    'Last Purchase': format_date(data['last_purchase']) if data['last_purchase'] else 'N/A'
                }
                for customer, data in top_customers
            ])
            
            st.dataframe(top_customers_df, use_container_width=True)
            
            # Customer segmentation
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Customer Segmentation")
                
                # Segment customers by order frequency
                segments = {'High Value (5+ orders)': 0, 'Medium Value (2-4 orders)': 0, 'Low Value (1 order)': 0}
                
                for customer, data in customer_analysis.items():
                    if data['orders'] >= 5:
                        segments['High Value (5+ orders)'] += 1
                    elif data['orders'] >= 2:
                        segments['Medium Value (2-4 orders)'] += 1
                    else:
                        segments['Low Value (1 order)'] += 1
                
                fig = px.pie(
                    values=list(segments.values()),
                    names=list(segments.keys()),
                    title='Customer Segments'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 📈 Customer Growth")
                
                # Customer acquisition over time
                if filtered_sales:
                    monthly_customers = {}
                    for sale in filtered_sales:
                        if sale.get('sale_date') and sale.get('customer_id'):
                            month_key = datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').strftime('%Y-%m')
                            if month_key not in monthly_customers:
                                monthly_customers[month_key] = set()
                            monthly_customers[month_key].add(sale['customer_id'])
                    
                    if monthly_customers:
                        monthly_customer_count = {month: len(customers) for month, customers in monthly_customers.items()}
                        
                        fig = px.line(
                            x=list(monthly_customer_count.keys()),
                            y=list(monthly_customer_count.values()),
                            title='Active Customers by Month'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # Export customer analysis
        if customer_analysis:
            st.markdown("---")
            if st.button("📥 Export Customer Analysis"):
                csv_data = export_to_csv(
                    top_customers_df.to_dict('records'),
                    f"customer_analysis_{company_data['title'].replace(' ', '_').lower()}.csv"
                )
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"customer_analysis_{company_data['title'].replace(' ', '_').lower()}.csv",
                    mime="text/csv"
                )

elif report_type == "Financial Summary":
    st.markdown(f"### 💰 Financial Summary - {company_data['title']}")
    st.markdown(f"**Period:** {date_range}")
    
    # Calculate financial metrics
    total_revenue = sum(sale['final_amount'] for sale in filtered_sales)
    total_cost = sum(purchase['total_amount'] for purchase in filtered_purchases)
    gross_profit = total_revenue - total_cost
    total_discounts = sum(sale.get('discount', 0) for sale in filtered_sales)
    total_tax = sum(sale.get('tax_amount', 0) for sale in filtered_sales)
    
    # Financial overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Revenue", format_currency(total_revenue))
    
    with col2:
        st.metric("🛒 Total Cost", format_currency(total_cost))
    
    with col3:
        profit_color = "normal" if gross_profit >= 0 else "inverse"
        st.metric("📈 Gross Profit", format_currency(gross_profit))
    
    with col4:
        margin_percentage = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("📊 Profit Margin", f"{margin_percentage:.1f}%")
    
    # Additional metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💸 Total Discounts", format_currency(total_discounts))
    
    with col2:
        st.metric("🏛️ Total Tax Collected", format_currency(total_tax))
    
    with col3:
        net_profit = gross_profit - total_discounts
        st.metric("💵 Net Profit", format_currency(net_profit))
    
    # Financial charts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Revenue vs Cost")
        
        if total_revenue > 0 or total_cost > 0:
            fig = go.Figure(data=[
                go.Bar(name='Revenue', x=['Financial Performance'], y=[total_revenue]),
                go.Bar(name='Cost', x=['Financial Performance'], y=[total_cost])
            ])
            fig.update_layout(barmode='group', title='Revenue vs Cost Comparison')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🥧 Profit Breakdown")
        
        if total_revenue > 0:
            breakdown_data = {
                'Gross Profit': max(0, gross_profit),
                'Discounts Given': total_discounts,
                'Tax Collected': total_tax
            }
            
            fig = px.pie(
                values=list(breakdown_data.values()),
                names=list(breakdown_data.keys()),
                title='Profit & Expense Breakdown'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Monthly financial trend
    if filtered_sales or filtered_purchases:
        st.markdown("#### 📈 Monthly Financial Trend")
        
        monthly_data = {}
        
        # Process sales
        for sale in filtered_sales:
            if sale.get('sale_date'):
                month_key = datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'revenue': 0, 'cost': 0}
                monthly_data[month_key]['revenue'] += sale['final_amount']
        
        # Process purchases
        for purchase in filtered_purchases:
            if purchase.get('purchase_date'):
                month_key = datetime.strptime(str(purchase['purchase_date']), '%Y-%m-%d').strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'revenue': 0, 'cost': 0}
                monthly_data[month_key]['cost'] += purchase['total_amount']
        
        if monthly_data:
            monthly_df = pd.DataFrame.from_dict(monthly_data, orient='index')
            monthly_df['profit'] = monthly_df['revenue'] - monthly_df['cost']
            monthly_df.index = pd.to_datetime(monthly_df.index)
            monthly_df = monthly_df.sort_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly_df.index, y=monthly_df['revenue'], mode='lines+markers', name='Revenue'))
            fig.add_trace(go.Scatter(x=monthly_df.index, y=monthly_df['cost'], mode='lines+markers', name='Cost'))
            fig.add_trace(go.Scatter(x=monthly_df.index, y=monthly_df['profit'], mode='lines+markers', name='Profit'))
            
            fig.update_layout(title='Monthly Financial Performance', xaxis_title='Month', yaxis_title='Amount (₹)')
            st.plotly_chart(fig, use_container_width=True)

# Export and PDF generation
st.markdown("---")
st.markdown("### 📥 Export Reports")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export to CSV", use_container_width=True):
        # Prepare summary data based on current report
        summary_data = {
            'Report Type': report_type,
            'Company': company_data['title'],
            'Date Range': date_range,
            'Generated On': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        csv_data = export_to_csv([summary_data], f"{report_type.replace(' ', '_').lower()}_summary.csv")
        st.download_button(
            label="Download Summary CSV",
            data=csv_data,
            file_name=f"{report_type.replace(' ', '_').lower()}_summary.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📄 Generate PDF Report", use_container_width=True):
        try:
            # Prepare report data for PDF
            report_data = {
                'title': f"{report_type} - {company_data['title']}",
                'period': f"Period: {date_range}",
                'company_name': company_data['title'],
                'summary': {
                    'Report Type': report_type,
                    'Companies': len(company_data['companies']),
                    'Books': len(company_data['books']),
                    'Customers': len(company_data['customers']),
                    'Sales': len(filtered_sales),
                    'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            # Generate PDF
            pdf_filename = pdf_generator.generate_report_pdf(report_data)
            
            if pdf_filename and os.path.exists(pdf_filename):
                show_success("PDF report generated successfully!")
                
                # Provide download link
                if create_download_link(pdf_filename, f"{report_type.replace(' ', '_').lower()}_report.pdf"):
                    st.success("📥 PDF ready for download!")
            else:
                show_error("Failed to generate PDF report.")
        
        except Exception as e:
            show_error(f"Error generating PDF: {str(e)}")

with col3:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p><strong>Report Generated:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p><strong>Data Range:</strong> {date_range} | <strong>Company:</strong> {company_data['title']}</p>
</div>
""", unsafe_allow_html=True)
