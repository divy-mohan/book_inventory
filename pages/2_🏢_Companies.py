import streamlit as st
import pandas as pd
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.company import Company
from utils.helpers import show_success, show_error, validate_email, validate_phone

st.set_page_config(
    page_title="Companies - Book Inventory",
    page_icon="🏢",
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
    <h1>🏢 Company Management</h1>
    <p>Manage multiple business entities and their information</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for actions
with st.sidebar:
    st.markdown("### 🔧 Company Actions")
    action = st.selectbox(
        "Choose Action",
        ["View Companies", "Add New Company", "Edit Company", "Delete Company"]
    )

# Main content based on selected action
if action == "View Companies":
    st.markdown("### 📋 All Companies")
    
    companies = db.get_all_companies()
    
    if companies:
        # Search functionality
        search_term = st.text_input("🔍 Search companies...", placeholder="Enter company name, phone, or email")
        
        if search_term:
            filtered_companies = [
                company for company in companies
                if search_term.lower() in company['name'].lower() or
                   search_term.lower() in company.get('phone', '').lower() or
                   search_term.lower() in company.get('email', '').lower()
            ]
        else:
            filtered_companies = companies
        
        if filtered_companies:
            # Display companies in a nice format
            for company in filtered_companies:
                with st.expander(f"🏢 {company['name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Registration No:** {company.get('registration_no', 'N/A')}")
                        st.write(f"**Phone:** {company.get('phone', 'N/A')}")
                        st.write(f"**Email:** {company.get('email', 'N/A')}")
                    
                    with col2:
                        st.write(f"**GST No:** {company.get('gst_no', 'N/A')}")
                        st.write(f"**Created:** {company.get('created_at', 'N/A')}")
                    
                    if company.get('address'):
                        st.write(f"**Address:** {company['address']}")
                    
                    # Quick stats for this company
                    books_count = len(db.get_books_by_company(company['id']))
                    customers_count = len(db.get_customers_by_company(company['id']))
                    sales_count = len(db.get_sales_by_company(company['id']))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📚 Books", books_count)
                    with col2:
                        st.metric("👥 Customers", customers_count)
                    with col3:
                        st.metric("💰 Sales", sales_count)
        else:
            st.info("No companies match your search criteria.")
    else:
        st.info("No companies registered yet. Add your first company!")

elif action == "Add New Company":
    st.markdown("### ➕ Add New Company")
    
    with st.form("add_company_form"):
        st.markdown("#### Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name *", placeholder="Enter company name")
            registration_no = st.text_input("Registration Number", placeholder="Company registration number")
            phone = st.text_input("Phone Number", placeholder="Contact phone number")
        
        with col2:
            email = st.text_input("Email Address", placeholder="company@example.com")
            gst_no = st.text_input("GST Number", placeholder="GST registration number")
        
        address = st.text_area("Address", placeholder="Complete business address")
        
        submitted = st.form_submit_button("🏢 Add Company", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            if not company_name.strip():
                errors.append("Company name is required")
            
            if email and not validate_email(email):
                errors.append("Invalid email format")
            
            if phone and not validate_phone(phone):
                errors.append("Invalid phone number format")
            
            if errors:
                for error in errors:
                    show_error(error)
            else:
                # Create company object
                company = Company(
                    name=company_name.strip(),
                    registration_no=registration_no.strip(),
                    address=address.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    gst_no=gst_no.strip()
                )
                
                # Add to database
                if db.add_company(company.to_dict()):
                    show_success(f"Company '{company_name}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    show_error("Failed to add company. Please try again.")

elif action == "Edit Company":
    st.markdown("### ✏️ Edit Company")
    
    companies = db.get_all_companies()
    
    if companies:
        company_options = {f"{comp['name']} (ID: {comp['id']})": comp['id'] for comp in companies}
        selected_company_key = st.selectbox("Select Company to Edit", list(company_options.keys()))
        
        if selected_company_key:
            company_id = company_options[selected_company_key]
            company = db.get_company_by_id(company_id)
            
            if company:
                with st.form("edit_company_form"):
                    st.markdown("#### Update Company Information")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        company_name = st.text_input("Company Name *", value=company['name'])
                        registration_no = st.text_input("Registration Number", value=company.get('registration_no', ''))
                        phone = st.text_input("Phone Number", value=company.get('phone', ''))
                    
                    with col2:
                        email = st.text_input("Email Address", value=company.get('email', ''))
                        gst_no = st.text_input("GST Number", value=company.get('gst_no', ''))
                    
                    address = st.text_area("Address", value=company.get('address', ''))
                    
                    updated = st.form_submit_button("💾 Update Company", use_container_width=True)
                    
                    if updated:
                        # Validation
                        errors = []
                        
                        if not company_name.strip():
                            errors.append("Company name is required")
                        
                        if email and not validate_email(email):
                            errors.append("Invalid email format")
                        
                        if phone and not validate_phone(phone):
                            errors.append("Invalid phone number format")
                        
                        if errors:
                            for error in errors:
                                show_error(error)
                        else:
                            # Update company
                            updated_company = Company(
                                id=company_id,
                                name=company_name.strip(),
                                registration_no=registration_no.strip(),
                                address=address.strip(),
                                phone=phone.strip(),
                                email=email.strip(),
                                gst_no=gst_no.strip()
                            )
                            
                            if db.update_company(company_id, updated_company.to_dict()):
                                show_success(f"Company '{company_name}' updated successfully!")
                                st.rerun()
                            else:
                                show_error("Failed to update company. Please try again.")
    else:
        st.info("No companies available to edit.")

elif action == "Delete Company":
    st.markdown("### 🗑️ Delete Company")
    
    companies = db.get_all_companies()
    
    if companies:
        st.warning("⚠️ **Warning:** Deleting a company will also delete all associated books, customers, and transactions!")
        
        company_options = {f"{comp['name']} (ID: {comp['id']})": comp['id'] for comp in companies}
        selected_company_key = st.selectbox("Select Company to Delete", list(company_options.keys()))
        
        if selected_company_key:
            company_id = company_options[selected_company_key]
            company = db.get_company_by_id(company_id)
            
            if company:
                st.markdown("#### Company Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {company['name']}")
                    st.write(f"**Registration:** {company.get('registration_no', 'N/A')}")
                    st.write(f"**Phone:** {company.get('phone', 'N/A')}")
                
                with col2:
                    st.write(f"**Email:** {company.get('email', 'N/A')}")
                    st.write(f"**GST No:** {company.get('gst_no', 'N/A')}")
                
                # Show associated data count
                books_count = len(db.get_books_by_company(company_id))
                customers_count = len(db.get_customers_by_company(company_id))
                sales_count = len(db.get_sales_by_company(company_id))
                
                st.markdown("#### Associated Data")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📚 Books", books_count)
                with col2:
                    st.metric("👥 Customers", customers_count)
                with col3:
                    st.metric("💰 Sales", sales_count)
                
                # Confirmation checkbox
                confirm_delete = st.checkbox(f"I understand that deleting '{company['name']}' will permanently remove all associated data")
                
                if confirm_delete:
                    if st.button("🗑️ Delete Company", type="primary", use_container_width=True):
                        if db.delete_company(company_id):
                            show_success(f"Company '{company['name']}' deleted successfully!")
                            st.rerun()
                        else:
                            show_error("Failed to delete company. Please try again.")
    else:
        st.info("No companies available to delete.")

# Company Statistics
st.markdown("---")
st.markdown("### 📊 Company Statistics")

companies = db.get_all_companies()
if companies:
    total_companies = len(companies)
    total_books = sum(len(db.get_books_by_company(comp['id'])) for comp in companies)
    total_customers = sum(len(db.get_customers_by_company(comp['id'])) for comp in companies)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏢 Total Companies", total_companies)
    
    with col2:
        st.metric("📚 Total Books", total_books)
    
    with col3:
        st.metric("👥 Total Customers", total_customers)
else:
    st.info("Add companies to see statistics.")
