import streamlit as st
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from utils.helpers import init_session_state

# Page configuration
st.set_page_config(
    page_title="Premium Book Inventory & Billing System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    db = DatabaseManager()
    db.create_tables()
    return db

# Initialize session state
init_session_state()

# Initialize database
db = init_database()

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #2e86de 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
        margin: 1rem 0;
    }
    
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>📚 Premium Book Inventory & Billing System</h1>
    <p>Professional Multi-Company Book Management Solution</p>
</div>
""", unsafe_allow_html=True)

# Welcome message and instructions
st.markdown("""
## Welcome to your Professional Book Management System

This comprehensive system provides everything you need to manage your book inventory and billing operations:

### 🎯 Key Features:
- **Multi-Company Management**: Handle multiple business entities
- **Complete Book Inventory**: Track books in Hindi/English with full details
- **Purchase & Sales Tracking**: Monitor all transactions and stock movements
- **Professional Billing**: Generate branded PDF invoices automatically
- **Customer Management**: Maintain detailed customer records
- **Advanced Reports**: Get insights with comprehensive analytics

### 🚀 Getting Started:
1. **Setup Companies**: Add your business entities in the Companies section
2. **Add Books**: Build your inventory with detailed book information
3. **Register Customers**: Add customer details for billing
4. **Record Transactions**: Track purchases and sales
5. **Generate Bills**: Create professional invoices with PDF export
6. **Monitor Reports**: Analyze your business performance

### 📱 Navigation:
Use the sidebar menu to access different modules of the system. Each section is designed for specific business operations.
""")

# Quick stats if companies exist
companies = db.get_all_companies()
if companies:
    st.markdown("### 📊 Quick Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Companies", len(companies))
    
    with col2:
        total_books = db.execute_query("SELECT COUNT(*) as count FROM books")[0]['count']
        st.metric("Total Books", total_books)
    
    with col3:
        total_customers = db.execute_query("SELECT COUNT(*) as count FROM customers")[0]['count']
        st.metric("Total Customers", total_customers)
    
    with col4:
        total_sales = db.execute_query("SELECT COUNT(*) as count FROM sales")[0]['count']
        st.metric("Total Sales", total_sales)

else:
    st.info("👋 Welcome! Please start by adding your first company in the Companies section.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>© 2025 Premium Book Inventory & Billing System | Professional Business Solution</p>
</div>
""", unsafe_allow_html=True)
