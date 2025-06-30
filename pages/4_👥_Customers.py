import streamlit as st
import pandas as pd
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.customer import Customer
from utils.helpers import show_success, show_error, validate_email, validate_phone, filter_data, paginate_data

st.set_page_config(
    page_title="Customers - Book Inventory",
    page_icon="👥",
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

# Get companies for selection
companies = db.get_all_companies()

if not companies:
    st.warning("⚠️ Please add at least one company before managing customers.")
    if st.button("🏢 Go to Companies"):
        st.switch_page("pages/2_🏢_Companies.py")
    st.stop()

# Sidebar for actions
with st.sidebar:
    st.markdown("### 👤 Customer Actions")
    action = st.selectbox(
        "Choose Action",
        ["View Customers", "Add New Customer", "Edit Customer", "Delete Customer", "Customer History"]
    )
    
    st.markdown("### 🏢 Filter by Company")
    company_filter = st.selectbox(
        "Select Company",
        ["All Companies"] + [f"{comp['name']}" for comp in companies]
    )

# Main content based on selected action
if action == "View Customers":
    st.markdown("### 👥 Customer Directory")
    
    # Get customers based on company filter
    if company_filter == "All Companies":
        customers = db.get_all_customers()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        customers = db.get_customers_by_company(selected_company['id'])
    
    if customers:
        # Search functionality
        search_term = st.text_input("🔍 Search customers...", placeholder="Enter customer name, phone, or email")
        
        # Apply search filter
        if search_term:
            filtered_customers = filter_data(customers, search_term, ['name', 'phone', 'email'])
        else:
            filtered_customers = customers
        
        # Display customer count
        st.write(f"📊 Showing **{len(filtered_customers)}** of **{len(customers)}** customers")
        
        if filtered_customers:
            # Pagination
            page_data, current_page, total_pages = paginate_data(filtered_customers, 10)
            
            # Display customers in cards
            for customer in page_data:
                with st.expander(f"👤 {customer['name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Company:** {customer.get('company_name', 'N/A')}")
                        st.write(f"**Phone:** {customer.get('phone', 'N/A')}")
                        st.write(f"**Email:** {customer.get('email', 'N/A')}")
                    
                    with col2:
                        st.write(f"**GST No:** {customer.get('gst_no', 'N/A')}")
                        st.write(f"**Created:** {customer.get('created_at', 'N/A')}")
                    
                    if customer.get('address'):
                        st.write(f"**Address:** {customer['address']}")
                    
                    # Customer transaction summary
                    sales = db.get_sales_by_company(customer['company_id'])
                    customer_sales = [sale for sale in sales if sale.get('customer_id') == customer['id']]
                    
                    if customer_sales:
                        total_purchases = len(customer_sales)
                        total_amount = sum(sale['final_amount'] for sale in customer_sales)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🛒 Total Purchases", total_purchases)
                        with col2:
                            st.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
                    else:
                        st.info("No purchase history available")
        else:
            st.info("No customers match your search criteria.")
    else:
        st.info("No customers registered yet. Add your first customer!")

elif action == "Add New Customer":
    st.markdown("### ➕ Add New Customer")
    
    with st.form("add_customer_form"):
        st.markdown("#### Customer Information")
        
        # Company selection
        company_options = {f"{comp['name']}": comp['id'] for comp in companies}
        selected_company_name = st.selectbox("Company *", list(company_options.keys()))
        company_id = company_options[selected_company_name]
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name *", placeholder="Enter customer name")
            phone = st.text_input("Phone Number", placeholder="Contact phone number")
            email = st.text_input("Email Address", placeholder="customer@example.com")
        
        with col2:
            gst_no = st.text_input("GST Number", placeholder="Customer GST number (if applicable)")
        
        address = st.text_area("Address", placeholder="Customer's complete address")
        
        submitted = st.form_submit_button("👤 Add Customer", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if not customer_name.strip():
                errors.append("Customer name is required")
            
            if email and not validate_email(email):
                errors.append("Invalid email format")
            
            if phone and not validate_phone(phone):
                errors.append("Invalid phone number format")
            
            if errors:
                for error in errors:
                    show_error(error)
            else:
                # Create customer object
                customer = Customer(
                    company_id=company_id,
                    name=customer_name.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    address=address.strip(),
                    gst_no=gst_no.strip()
                )
                
                # Add to database
                if db.add_customer(customer.to_dict()):
                    show_success(f"Customer '{customer_name}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    show_error("Failed to add customer. Please try again.")

elif action == "Edit Customer":
    st.markdown("### ✏️ Edit Customer")
    
    # Get customers for selection
    if company_filter == "All Companies":
        customers = db.get_all_customers()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        customers = db.get_customers_by_company(selected_company['id'])
    
    if customers:
        customer_options = {f"{cust['name']} - {cust.get('phone', 'No Phone')} (ID: {cust['id']})": cust['id'] for cust in customers}
        selected_customer_key = st.selectbox("Select Customer to Edit", list(customer_options.keys()))
        
        if selected_customer_key:
            customer_id = customer_options[selected_customer_key]
            customer = db.get_customer_by_id(customer_id)
            
            if customer:
                with st.form("edit_customer_form"):
                    st.markdown("#### Update Customer Information")
                    
                    # Company selection
                    company_options = {f"{comp['name']}": comp['id'] for comp in companies}
                    current_company_name = next(comp['name'] for comp in companies if comp['id'] == customer['company_id'])
                    selected_company_name = st.selectbox("Company *", list(company_options.keys()), 
                                                        index=list(company_options.keys()).index(current_company_name))
                    company_id = company_options[selected_company_name]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        customer_name = st.text_input("Customer Name *", value=customer['name'])
                        phone = st.text_input("Phone Number", value=customer.get('phone', ''))
                        email = st.text_input("Email Address", value=customer.get('email', ''))
                    
                    with col2:
                        gst_no = st.text_input("GST Number", value=customer.get('gst_no', ''))
                    
                    address = st.text_area("Address", value=customer.get('address', ''))
                    
                    updated = st.form_submit_button("💾 Update Customer", use_container_width=True)
                    
                    if updated:
                        # Validation
                        errors = []
                        
                        if not customer_name.strip():
                            errors.append("Customer name is required")
                        
                        if email and not validate_email(email):
                            errors.append("Invalid email format")
                        
                        if phone and not validate_phone(phone):
                            errors.append("Invalid phone number format")
                        
                        if errors:
                            for error in errors:
                                show_error(error)
                        else:
                            # Update customer
                            updated_customer = Customer(
                                id=customer_id,
                                company_id=company_id,
                                name=customer_name.strip(),
                                phone=phone.strip(),
                                email=email.strip(),
                                address=address.strip(),
                                gst_no=gst_no.strip()
                            )
                            
                            if db.update_customer(customer_id, updated_customer.to_dict()):
                                show_success(f"Customer '{customer_name}' updated successfully!")
                                st.rerun()
                            else:
                                show_error("Failed to update customer. Please try again.")
    else:
        st.info("No customers available to edit.")

elif action == "Delete Customer":
    st.markdown("### 🗑️ Delete Customer")
    
    # Get customers for selection
    if company_filter == "All Companies":
        customers = db.get_all_customers()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        customers = db.get_customers_by_company(selected_company['id'])
    
    if customers:
        st.warning("⚠️ **Warning:** Deleting a customer will also remove all associated sale records!")
        
        customer_options = {f"{cust['name']} - {cust.get('phone', 'No Phone')} (ID: {cust['id']})": cust['id'] for cust in customers}
        selected_customer_key = st.selectbox("Select Customer to Delete", list(customer_options.keys()))
        
        if selected_customer_key:
            customer_id = customer_options[selected_customer_key]
            customer = db.get_customer_by_id(customer_id)
            
            if customer:
                st.markdown("#### Customer Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {customer['name']}")
                    st.write(f"**Phone:** {customer.get('phone', 'N/A')}")
                    st.write(f"**Email:** {customer.get('email', 'N/A')}")
                
                with col2:
                    st.write(f"**GST No:** {customer.get('gst_no', 'N/A')}")
                    st.write(f"**Address:** {customer.get('address', 'N/A')}")
                
                # Show associated sales count
                sales = db.get_sales_by_company(customer['company_id'])
                customer_sales = [sale for sale in sales if sale.get('customer_id') == customer_id]
                
                st.markdown("#### Associated Data")
                st.metric("💰 Sales Transactions", len(customer_sales))
                
                if customer_sales:
                    total_amount = sum(sale['final_amount'] for sale in customer_sales)
                    st.metric("💵 Total Purchase Amount", f"₹{total_amount:,.2f}")
                
                # Confirmation checkbox
                confirm_delete = st.checkbox(f"I understand that deleting '{customer['name']}' will permanently remove all associated data")
                
                if confirm_delete:
                    if st.button("🗑️ Delete Customer", type="primary", use_container_width=True):
                        if db.delete_customer(customer_id):
                            show_success(f"Customer '{customer['name']}' deleted successfully!")
                            st.rerun()
                        else:
                            show_error("Failed to delete customer. Please try again.")
    else:
        st.info("No customers available to delete.")

elif action == "Customer History":
    st.markdown("### 📊 Customer Purchase History")
    
    # Get customers for selection
    if company_filter == "All Companies":
        customers = db.get_all_customers()
    else:
        selected_company = next(comp for comp in companies if comp['name'] == company_filter)
        customers = db.get_customers_by_company(selected_company['id'])
    
    if customers:
        customer_options = {f"{cust['name']} - {cust.get('phone', 'No Phone')}": cust['id'] for cust in customers}
        selected_customer_name = st.selectbox("Select Customer", list(customer_options.keys()))
        
        if selected_customer_name:
            customer_id = customer_options[selected_customer_name]
            customer = db.get_customer_by_id(customer_id)
            
            if customer:
                # Display customer information
                st.markdown("#### Customer Information")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Name:** {customer['name']}")
                    st.write(f"**Phone:** {customer.get('phone', 'N/A')}")
                
                with col2:
                    st.write(f"**Email:** {customer.get('email', 'N/A')}")
                    st.write(f"**GST No:** {customer.get('gst_no', 'N/A')}")
                
                with col3:
                    st.write(f"**Address:** {customer.get('address', 'N/A')}")
                
                # Get customer sales
                all_sales = db.get_sales_by_company(customer['company_id'])
                customer_sales = [sale for sale in all_sales if sale.get('customer_id') == customer_id]
                
                if customer_sales:
                    st.markdown("#### Purchase Summary")
                    
                    total_purchases = len(customer_sales)
                    total_amount = sum(sale['final_amount'] for sale in customer_sales)
                    total_discount = sum(sale.get('discount', 0) for sale in customer_sales)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🛒 Total Purchases", total_purchases)
                    
                    with col2:
                        st.metric("💰 Total Amount", f"₹{total_amount:,.2f}")
                    
                    with col3:
                        st.metric("💸 Total Discounts", f"₹{total_discount:,.2f}")
                    
                    st.markdown("#### Purchase History")
                    
                    # Display sales in a table
                    sales_data = []
                    for sale in customer_sales:
                        sales_data.append({
                            'Invoice No': sale['invoice_no'],
                            'Date': sale['sale_date'],
                            'Total Amount': f"₹{sale['total_amount']:,.2f}",
                            'Discount': f"₹{sale.get('discount', 0):,.2f}",
                            'Final Amount': f"₹{sale['final_amount']:,.2f}",
                            'Payment Status': sale.get('payment_status', 'N/A')
                        })
                    
                    if sales_data:
                        df = pd.DataFrame(sales_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Option to download customer report
                        if st.button("📥 Download Customer Report", use_container_width=True):
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"customer_report_{customer['name'].replace(' ', '_')}.csv",
                                mime="text/csv"
                            )
                else:
                    st.info("This customer has no purchase history yet.")
    else:
        st.info("No customers available to view history.")

# Customer Statistics
st.markdown("---")
st.markdown("### 📊 Customer Statistics")

if company_filter == "All Companies":
    customers = db.get_all_customers()
    all_sales = []
    for company in companies:
        sales = db.get_sales_by_company(company['id'])
        all_sales.extend(sales)
else:
    selected_company = next(comp for comp in companies if comp['name'] == company_filter)
    customers = db.get_customers_by_company(selected_company['id'])
    all_sales = db.get_sales_by_company(selected_company['id'])

if customers:
    total_customers = len(customers)
    customers_with_purchases = len(set(sale.get('customer_id') for sale in all_sales if sale.get('customer_id')))
    total_customer_revenue = sum(sale['final_amount'] for sale in all_sales if sale.get('customer_id'))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👥 Total Customers", total_customers)
    
    with col2:
        st.metric("🛒 Active Customers", customers_with_purchases)
    
    with col3:
        st.metric("💰 Customer Revenue", f"₹{total_customer_revenue:,.2f}")
else:
    st.info("Add customers to see statistics.")
