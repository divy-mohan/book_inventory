import streamlit as st
import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.pdf_generator import PDFInvoiceGenerator
from utils.helpers import show_success, show_error, format_currency, format_date, create_download_link, searchable_selectbox

st.set_page_config(
    page_title="Billing - Book Inventory",
    page_icon="📄",
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

# Initialize PDF generator
@st.cache_resource
def get_pdf_generator():
    return PDFInvoiceGenerator()

pdf_generator = get_pdf_generator()

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

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before generating invoices.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Check if there's a specific sale to view (from sales page)
view_sale_id = st.session_state.get('view_sale_id', None)

# Sidebar for actions
with st.sidebar:
    st.markdown("### 📄 Billing Actions")
    action = st.selectbox(
        "Choose Action",
        ["Generate Invoice", "View Invoices", "Invoice Templates"]
    )
    
    st.markdown("### 🏢 Filter by Company")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )

# Main content based on selected action
if action == "Generate Invoice":
    st.markdown("### 📄 Generate Professional Invoice")
    
    # If coming from sales page with specific sale ID
    if view_sale_id:
        st.info(f"📋 Generating invoice for: **{view_sale_id}**")
        
        # Try to find sale by invoice number or ID
        if isinstance(view_sale_id, str):
            # Search by invoice number
            query = "SELECT id FROM sales WHERE invoice_no = ?"
            result = db.execute_query(query, (view_sale_id,))
            if result:
                sale_id = result[0]['id']
            else:
                st.error("Sale not found!")
                st.stop()
        else:
            sale_id = view_sale_id
        
        # Clear the session state
        if 'view_sale_id' in st.session_state:
            del st.session_state.view_sale_id
    else:
        # Manual selection
        st.markdown("#### Select Sale for Invoice")
        
        # Get sales based on company filter
        if company_filter == "All Companies":
            all_sales = []
            for company in companies:
                sales = db.get_sales_by_company(company['id'])
                all_sales.extend(sales)
        else:
            selected_company = next(comp for comp in companies if comp['name'] == company_filter)
            all_sales = db.get_sales_by_company(selected_company['id'])
        
        if not all_sales:
            st.warning("No sales found. Please create a sale first.")
            if st.button("💰 Go to Sales"):
                st.switch_page("pages/6_💰_Sales.py")
            st.stop()
        
        # Sale selection with searchable dropdown
        sale_options = []
        sale_mapping = {}
        
        for sale in all_sales:
            option_text = f"{sale['invoice_no']} - {sale.get('customer_name', 'Walk-in')} - {format_currency(sale['final_amount'])}"
            sale_options.append(option_text)
            sale_mapping[option_text] = sale['id']
        
        selected_sale_key = searchable_selectbox(
            "Sale for Invoice", 
            sale_options,
            key="billing_sale_select",
            placeholder="Search by invoice number or customer name..."
        )
        
        if selected_sale_key:
            sale_id = sale_mapping[selected_sale_key]
        else:
            st.warning("Please select a sale to generate invoice.")
            st.stop()
    
    # Get sale details
    sale_details = db.get_sale_details(sale_id)
    
    if not sale_details['sale']:
        st.error("Sale details not found!")
        st.stop()
    
    sale = sale_details['sale']
    items = sale_details['items']
    
    # Get company details
    company = db.get_company_by_id(sale['company_id'])
    
    # Get customer details (if any)
    customer = None
    if sale.get('customer_id'):
        customer = db.get_customer_by_id(sale['customer_id'])
    
    # Display invoice preview
    st.markdown("### 📋 Invoice Preview")
    
    # Invoice header
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Company:** {company['name']}")
        if company.get('address'):
            st.markdown(f"**Address:** {company['address']}")
        if company.get('phone'):
            st.markdown(f"**Phone:** {company['phone']}")
        if company.get('email'):
            st.markdown(f"**Email:** {company['email']}")
        if company.get('gst_no'):
            st.markdown(f"**GST No:** {company['gst_no']}")
    
    with col2:
        st.markdown(f"**Invoice No:** {sale['invoice_no']}")
        st.markdown(f"**Date:** {format_date(sale['sale_date'])}")
        st.markdown(f"**Payment Status:** {sale.get('payment_status', 'N/A')}")
    
    # Customer details
    if customer:
        st.markdown("#### 👤 Customer Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Name:** {customer['name']}")
            if customer.get('phone'):
                st.markdown(f"**Phone:** {customer['phone']}")
            if customer.get('email'):
                st.markdown(f"**Email:** {customer['email']}")
        
        with col2:
            if customer.get('address'):
                st.markdown(f"**Address:** {customer['address']}")
            if customer.get('gst_no'):
                st.markdown(f"**GST No:** {customer['gst_no']}")
    else:
        st.info("👤 Walk-in Customer - No customer details recorded")
    
    # Invoice items
    st.markdown("#### 📚 Invoice Items")
    
    items_data = []
    for i, item in enumerate(items, 1):
        items_data.append({
            'S.No.': i,
            'Book Name': item['book_name'],
            'Author': item.get('author', 'Unknown'),
            'Quantity': item['quantity'],
            'Rate': format_currency(item['price_per_unit']),
            'Amount': format_currency(item['total_price'])
        })
    
    if items_data:
        items_df = st.dataframe(items_data, use_container_width=True)
    
    # Invoice totals
    st.markdown("#### 💰 Invoice Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Subtotal", format_currency(sale['total_amount']))
        st.metric("Discount", format_currency(sale.get('discount', 0)))
    
    with col2:
        st.metric("Tax Amount", format_currency(sale.get('tax_amount', 0)))
        st.metric("**Final Amount**", format_currency(sale['final_amount']))
    
    with col3:
        if sale.get('notes'):
            st.markdown(f"**Notes:** {sale['notes']}")
    
    # Generate PDF button
    # st.markdown("---")
    
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     if st.button("📄 Generate PDF Invoice", type="primary", use_container_width=True):
    #         try:
    #             # Prepare invoice data
    #             invoice_data = {
    #                 'sale': sale,
    #                 'items': items,
    #                 'company': company,
    #                 'customer': customer
    #             }
                
    #             # Generate PDF
    #             pdf_filename = pdf_generator.generate_invoice(invoice_data)
                
    #             if pdf_filename and os.path.exists(pdf_filename):
    #                 show_success(f"Invoice PDF generated successfully!")
                    
    #                 # Provide download link
    #                 if create_download_link(pdf_filename, f"invoice_{sale['invoice_no']}.pdf"):
    #                     st.success("📥 PDF ready for download!")
    #             else:
    #                 show_error("Failed to generate PDF invoice.")
            
    #         except Exception as e:
    #             show_error(f"Error generating invoice: {str(e)}")
    
    # with col2:
    #     if st.button("📧 Email Invoice", use_container_width=True):
    #         if customer and customer.get('email'):
    #             st.info("📧 Email functionality coming soon!")
    #             # Here you would implement email sending functionality
    #         else:
    #             st.warning("⚠️ Customer email not available for this sale.")

elif action == "View Invoices":
    st.markdown("### 📋 Invoice History")
    
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
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search invoices...", placeholder="Enter invoice number or customer name")
        
        with col2:
            date_filter = st.selectbox("Date Range", ["All Time", "This Month", "Last 30 Days", "This Year"])
        
        # Apply filters
        filtered_sales = all_sales
        
        if search_term:
            filtered_sales = [
                sale for sale in filtered_sales
                if search_term.lower() in sale['invoice_no'].lower() or
                   search_term.lower() in sale.get('customer_name', '').lower()
            ]
        
        # Apply date filter
        if date_filter != "All Time":
            today = datetime.now().date()
            if date_filter == "This Month":
                filter_date = today.replace(day=1)
            elif date_filter == "Last 30 Days":
                filter_date = today - pd.Timedelta(days=30)
            elif date_filter == "This Year":
                filter_date = today.replace(month=1, day=1)
            
            filtered_sales = [
                sale for sale in filtered_sales 
                if sale.get('sale_date') and 
                datetime.strptime(str(sale['sale_date']), '%Y-%m-%d').date() >= filter_date
            ]
        
        # Display invoice count
        st.write(f"📊 Showing **{len(filtered_sales)}** of **{len(all_sales)}** invoices")
        
        if filtered_sales:
            # Display invoices in a table format
            invoice_data = []
            for sale in filtered_sales:
                invoice_data.append({
                    'Invoice No': sale['invoice_no'],
                    'Date': format_date(sale['sale_date']),
                    'Customer': sale.get('customer_name', 'Walk-in Customer'),
                    'Company': sale.get('company_name', 'N/A'),
                    'Amount': format_currency(sale['final_amount']),
                    'Status': sale.get('payment_status', 'N/A'),
                    'ID': sale['id']  # Hidden column for actions
                })
            
            # Create DataFrame
            df = st.dataframe(
                invoice_data,
                column_config={
                    'ID': None,  # Hide ID column
                    'Invoice No': st.column_config.TextColumn('Invoice No', width='medium'),
                    'Date': st.column_config.TextColumn('Date', width='small'),
                    'Customer': st.column_config.TextColumn('Customer', width='medium'),
                    'Company': st.column_config.TextColumn('Company', width='medium'),
                    'Amount': st.column_config.TextColumn('Amount', width='small'),
                    'Status': st.column_config.TextColumn('Status', width='small')
                },
                use_container_width=True
            )
            
            # # Action buttons for selected invoices
            # st.markdown("#### 🔧 Invoice Actions")
            
            # col1, col2, col3 = st.columns(3)
            
            # with col1:
            #     selected_invoice = st.selectbox(
            #         "Select Invoice for Action",
            #         [f"{sale['invoice_no']} - {sale.get('customer_name', 'Walk-in')}" for sale in filtered_sales]
            #     )
                
            #     if selected_invoice:
            #         selected_sale = next(sale for sale in filtered_sales if f"{sale['invoice_no']} - {sale.get('customer_name', 'Walk-in')}" == selected_invoice)
            
            # with col2:
            #     if st.button("📄 View/Download PDF", use_container_width=True):
            #         st.session_state.view_sale_id = selected_sale['id']
            #         st.rerun()
            
            # with col3:
            #     if st.button("📧 Resend Invoice", use_container_width=True):
            #         st.info("📧 Email functionality coming soon!")
        else:
            st.info("No invoices match your search criteria.")
    else:
        st.info("No invoices found. Create sales to generate invoices.")

elif action == "Invoice Templates":
    st.markdown("### 🎨 Invoice Templates & Settings")
    
    st.info("🚧 Template customization features coming soon!")
    
    # Preview of current template
    st.markdown("#### 📋 Current Template Preview")
    
    # Sample invoice data for preview
    sample_company = {
        'name': 'Sample Book Store',
        'address': '123 Book Street, Reading City, 123456',
        'phone': '+91 98765 43210',
        'email': 'info@samplebookstore.com',
        'gst_no': 'GST123456789'
    }
    
    sample_customer = {
        'name': 'John Doe',
        'phone': '+91 87654 32109',
        'email': 'john.doe@email.com',
        'address': '456 Reader Lane, Book Town, 654321',
        'gst_no': 'GST987654321'
    }
    
    sample_sale = {
        'invoice_no': 'INV-001-000001',
        'sale_date': datetime.now().date(),
        'total_amount': 1000.00,
        'discount': 50.00,
        'tax_amount': 95.00,
        'final_amount': 1045.00,
        'payment_status': 'Completed',
        'notes': 'Thank you for your business!'
    }
    
    sample_items = [
        {
            'book_name': 'Python Programming Guide',
            'author': 'Tech Author',
            'quantity': 2,
            'price_per_unit': 300.00,
            'total_price': 600.00
        },
        {
            'book_name': 'Data Science Handbook',
            'author': 'Data Expert',
            'quantity': 1,
            'price_per_unit': 400.00,
            'total_price': 400.00
        }
    ]
    
    # Display sample invoice
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Company Information:**")
        st.write(f"📍 {sample_company['name']}")
        st.write(f"🏠 {sample_company['address']}")
        st.write(f"📞 {sample_company['phone']}")
        st.write(f"📧 {sample_company['email']}")
        st.write(f"🏛️ {sample_company['gst_no']}")
        
        st.markdown("**Customer Information:**")
        st.write(f"👤 {sample_customer['name']}")
        st.write(f"📞 {sample_customer['phone']}")
        st.write(f"📧 {sample_customer['email']}")
    
    with col2:
        st.markdown("**Invoice Details:**")
        st.write(f"📄 Invoice: {sample_sale['invoice_no']}")
        st.write(f"📅 Date: {format_date(sample_sale['sale_date'])}")
        st.write(f"💳 Status: {sample_sale['payment_status']}")
        
        st.markdown("**Summary:**")
        st.write(f"💰 Subtotal: {format_currency(sample_sale['total_amount'])}")
        st.write(f"💸 Discount: {format_currency(sample_sale['discount'])}")
        st.write(f"🏛️ Tax: {format_currency(sample_sale['tax_amount'])}")
        st.write(f"**💵 Total: {format_currency(sample_sale['final_amount'])}**")
    
    # Sample items table
    st.markdown("**Items:**")
    sample_items_df = []
    for i, item in enumerate(sample_items, 1):
        sample_items_df.append({
            'S.No.': i,
            'Book Name': item['book_name'],
            'Author': item['author'],
            'Qty': item['quantity'],
            'Rate': format_currency(item['price_per_unit']),
            'Amount': format_currency(item['total_price'])
        })
    
    st.dataframe(sample_items_df, use_container_width=True)
    
    # Template settings (placeholder)
    st.markdown("---")
    st.markdown("#### ⚙️ Template Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Color Scheme", ["Blue (Default)", "Green", "Red", "Purple"])
        st.selectbox("Font Style", ["Helvetica (Default)", "Arial", "Times New Roman"])
    
    with col2:
        st.checkbox("Include Company Logo", value=False)
        st.checkbox("Include Watermark", value=False)
    
    st.text_area("Invoice Footer Text", 
                value="Terms & Conditions:\n1. Payment due within 30 days\n2. Goods once sold will not be taken back\n3. Subject to jurisdiction only")
    
    if st.button("💾 Save Template Settings", use_container_width=True):
        st.success("✅ Template settings saved! (Feature coming soon)")

# Invoice Statistics
st.markdown("---")
st.markdown("### 📊 Billing Statistics")

# Get all sales for statistics
if company_filter == "All Companies":
    all_sales = []
    for company in companies:
        sales = db.get_sales_by_company(company['id'])
        all_sales.extend(sales)
else:
    selected_company = next(comp for comp in companies if comp['name'] == company_filter)
    all_sales = db.get_sales_by_company(selected_company['id'])

if all_sales:
    total_invoices = len(all_sales)
    total_revenue = sum(sale['final_amount'] for sale in all_sales)
    paid_invoices = len([sale for sale in all_sales if sale.get('payment_status') == 'Completed'])
    pending_invoices = total_invoices - paid_invoices
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Total Invoices", total_invoices)
    
    with col2:
        st.metric("💰 Total Revenue", format_currency(total_revenue))
    
    with col3:
        st.metric("✅ Paid Invoices", paid_invoices)
    
    with col4:
        st.metric("⏳ Pending Invoices", pending_invoices)
else:
    st.info("Create sales to see billing statistics.")

invoice_id = sale['invoice_no']  # or whatever uniquely identifies the invoice
invoice_url = f"http://127.0.0.1:5001/invoice.html?invoice_id={invoice_id}"

if st.button("🌐 Go to Invoice Webpage", use_container_width=True):
    st.markdown(
        f"""
        <meta http-equiv="refresh" content="0; url='{invoice_url}'" />
        <script>
            window.location.href = "{invoice_url}";
        </script>
        """,
        unsafe_allow_html=True
    )
