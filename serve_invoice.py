from flask import Flask, render_template, request
import sys
import os
import traceback

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

app = Flask(__name__)

@app.route('/invoice.html')
def invoice():
    try:
        print("INVOICE ROUTE CALLED")
        invoice_id = request.args.get('invoice_id')
        conn_str = "postgresql://neondb_owner:npg_R81aBEUPvtMC@ep-fragrant-tooth-a1j6h75o-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
        db = DatabaseManager(conn_str)
        
        sale_result = db.execute_query("SELECT id FROM sales WHERE invoice_no = ?", (invoice_id,))
        print("sale_result:", sale_result)
        if not sale_result:
            return "Invoice not found", 404
        sale_id = sale_result[0]['id']
        
        sale_details = db.get_sale_details(sale_id)
        print("sale_details:", sale_details)
        sale = sale_details['sale']
        items = sale_details['items']
        company = db.get_company_by_id(sale['company_id'])
        print("company:", company)
        customer = db.get_customer_by_id(sale['customer_id']) if sale.get('customer_id') else None
        print("customer:", customer)

        return render_template(
            'invoice.html',
            company_name=company['name'],
            company_address=company.get('address', ''),
            company_phone=company.get('phone', ''),
            company_email=company.get('email', ''),
            company_gst=company.get('gst_no', ''),
            customer_name=customer['name'] if customer else 'Walk-in Customer',
            customer_address=customer.get('address', '') if customer else '',
            customer_phone=customer.get('phone', '') if customer else '',
            customer_email=customer.get('email', '') if customer else '',
            customer_gst=customer.get('gst_no', '') if customer else '',
            invoice_no=sale['invoice_no'],
            invoice_date=sale['sale_date'],
            payment_status=sale.get('payment_status', ''),
            items=items,
            subtotal=sale['total_amount'],
            discount=sale.get('discount', 0),
            tax_amount=sale.get('tax_amount', 0),
            final_amount=sale['final_amount'],
            notes=sale.get('notes', '')
        )
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)