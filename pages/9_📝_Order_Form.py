import streamlit as st
import pandas as pd
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.helpers import filter_data

st.set_page_config(
    page_title="Order Form - Book Inventory",
    page_icon="📝",
    layout="wide"
)

@st.cache_resource
def get_database():
    conn_str = "postgresql://neondb_owner:npg_R81aBEUPvtMC@ep-fragrant-tooth-a1j6h75o-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    return DatabaseManager(conn_str)

db = get_database()

import streamlit as st
import base64

# 📌 Load and encode logo image
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_data = get_base64_image("static/images/logo.png")

# 📌 Render Gradient Banner with Logo and Title
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


companies = db.get_all_companies()
company_names = [c['name'] for c in companies]
company = st.selectbox("Select Company", company_names)
company_id = next((c['id'] for c in companies if c['name'] == company), None)

# Add this here:
company_obj = next((c for c in companies if c['name'] == company), {})
company_address = company_obj.get('address', '')
company_phone = company_obj.get('phone', '')

books = db.get_books_by_company(company_id) if company_id else []
# --- Filter UI (like Books page) ---
if books:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search books...", placeholder="Enter book name, author, category, or ISBN")
    with col2:
        language_filter = st.selectbox("Language", ["All", "English", "Hindi", "Other"])
    with col3:
        category_filter = st.selectbox("Category", ["All"] + list(set(book.get('category', 'Uncategorized') for book in books)))

    filtered_books = books
    if search_term:
        filtered_books = filter_data(filtered_books, search_term, ['name', 'author', 'category', 'isbn'])
    if language_filter != "All":
        filtered_books = [book for book in filtered_books if book.get('language', 'English') == language_filter]
    if category_filter != "All":
        filtered_books = [book for book in filtered_books if book.get('category', 'Uncategorized') == category_filter]
else:
    filtered_books = []

order = []

st.write("### Select Books and Quantities to Order")
if filtered_books:
    for book in filtered_books:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{book['name']}** by {book.get('author', '')}")
        with col2:
            qty = st.number_input(
                f"Quantity for {book['name']}", min_value=0, step=1, key=f"qty_{book['id']}"
            )
        if qty > 0:
            order.append({
                "Code": book.get('isbn', ''),  # or use your own code field
                "Book Name": book['name'],
                "Category": book.get('category', ''),
                "Quantity": qty
            })

    if order:
        df = pd.DataFrame(order)
        st.write("### Order Preview")
        st.dataframe(df)

        # --- Generate Hindi HTML for order ---
        hindi_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
            <style>
                @font-face {{
                    font-family: 'Adobe Devanagari';
                    src: url('/static/fonts/AdobeDevanagari-Regular.otf') format('opentype');
                    font-weight: normal;
                    font-style: normal;
                }}
                body {{
                    font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;
                    margin: 40px;
                }}
                h2 {{
                    color: #d2691e;
                    text-align: center;
                    font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    font-size: 1.1em;
                }}
                th, td {{
                    border: 1px solid #888;
                    padding: 8px 12px;
                    text-align: center;
                }}
                th {{
                    background: #ffe600;
                    color: #d2691e;
                }}
                .no-print {{
                    display: block;
                }}
                @media print {{
                    .no-print {{
                        display: none !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="no-print" style="text-align:center; margin-bottom:16px;">
                <button onclick="printOrder()" style="
                    background:#ff9100;
                    color:white;
                    border:none;
                    border-radius:6px;
                    padding:10px 24px;
                    font-size:1.1em;
                    font-weight:bold;
                    margin-right:16px;
                    cursor:pointer;
                ">प्रिंट करें</button>
                <button onclick="downloadPDF()" style="
                    background:#2ecc40;
                    color:white;
                    border:none;
                    border-radius:6px;
                    padding:10px 24px;
                    font-size:1.1em;
                    font-weight:bold;
                    cursor:pointer;
                ">PDF डाउनलोड करें</button>
            </div>
            <div id="order-content">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <div style="flex: 0 0 auto;">
                        <img src="data:image/png;base64,{img_data}" width="80" style="border-radius: 5px; margin-right: 18px;" />
                    </div>
                    <div style="flex: 1 1 auto;">
                        <span style="
                            display: block;
                            text-align: center;
                            font-size: 3rem;
                            font-weight: bold;
                            margin-bottom: 0px;
                            color: #d2691e;
                            font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;
                        ">
                            पुस्तक आदेश प्रपत्र
                        </span>
                        <br/>
                        <span style="
                            display: block;
                            text-align: center;
                            font-size: 2.5rem;
                            color: #d2691e;
                            font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;
                            font-weight: bold;
                        ">
                            {company}
                        </span>
                        <span style="
                            display: block;
                            text-align: center;
                            font-size: 1rem;
                            color: #444;
                            font-family: 'Adobe Devanagari', 'Noto Sans Devanagari', 'Mangal', Arial, sans-serif;
                            margin-top: 0px;
                        ">
                            {company_address}<br>
                            संपर्क: {company_phone}
                        </span>
                    </div>
                </div>
                <table>
                    <tr>
                        <th>क्रमांक</th>
                        <th>कोड</th>
                        <th>पुस्तक का नाम</th>
                        <th>श्रेणी</th>
                        <th>मात्रा</th>
                    </tr>
        """

        for idx, item in enumerate(order, 1):
            hindi_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{item.get('Code', '')}</td>
                    <td>{item['Book Name']}</td>
                    <td>{item.get('Category', '')}</td>
                    <td>{item['Quantity']}</td>
                </tr>
            """

        hindi_html += """
            </table>
            <br>

        </div>
        <script>
            function printOrder() {
                window.print();
            }
            function downloadPDF() {
                var orderContent = document.getElementById('order-content');
                html2canvas(orderContent).then(function(canvas) {
                    var imgData = canvas.toDataURL('image/png');
                    var pdf = new window.jspdf.jsPDF('p', 'pt', 'a4');
                    var pageWidth = pdf.internal.pageSize.getWidth();
                    var pageHeight = pdf.internal.pageSize.getHeight();
                    var imgWidth = pageWidth - 40;
                    var imgHeight = canvas.height * imgWidth / canvas.width;
                    pdf.addImage(imgData, 'PNG', 20, 20, imgWidth, imgHeight);
                    pdf.save('order.pdf');
                });
            }
        </script>
        </body>
        </html>
        """

        st.markdown("#### PDF प्रीव्यू (Print/Download PDF)")
        st.components.v1.html(hindi_html, height=700, scrolling=True)

    else:
        st.info("Select quantities for at least one book to create an order.")
else:
    st.info("No books match your search/filter criteria.")