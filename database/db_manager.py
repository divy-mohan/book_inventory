from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional
import traceback  # Add this at the top of your file

class DatabaseManager:
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def get_connection(self):
        import psycopg2
        return psycopg2.connect(self.conn_str, cursor_factory=RealDictCursor)

    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()

    def execute_update(self, query, params=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                conn.commit()
                return True

    def create_tables(self):
        """Create all necessary tables"""
        tables = [
            '''CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                registration_no TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                gst_no TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                company_id INTEGER,
                name TEXT NOT NULL,
                author TEXT,
                category TEXT,
                language TEXT DEFAULT 'English',
                isbn TEXT,
                purchase_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                damaged_quantity INTEGER DEFAULT 0,
                lost_quantity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                company_id INTEGER,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                gst_no TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                company_id INTEGER,
                book_id INTEGER,
                supplier_name TEXT,
                quantity INTEGER NOT NULL,
                price_per_unit REAL NOT NULL,
                total_amount REAL NOT NULL,
                purchase_date DATE DEFAULT CURRENT_DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id),
                FOREIGN KEY (book_id) REFERENCES books (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                company_id INTEGER,
                customer_id INTEGER,
                invoice_no TEXT UNIQUE,
                sale_date DATE DEFAULT CURRENT_DATE,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'Pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS sale_items (
                id SERIAL PRIMARY KEY,
                sale_id INTEGER,
                book_id INTEGER,
                quantity INTEGER NOT NULL,
                price_per_unit REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (book_id) REFERENCES books (id)
            )''',
            '''CREATE TABLE IF NOT EXISTS stock_movements (
                id SERIAL PRIMARY KEY,
                book_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )'''
        ]
        for table_sql in tables:
            self.execute_update(table_sql)

    # Company methods
    def add_company(self, company_data: Dict[str, Any]) -> bool:
        query = '''INSERT INTO companies (name, registration_no, address, phone, email, gst_no)
                   VALUES (%s, %s, %s, %s, %s, %s)'''
        params = (
            company_data['name'],
            company_data.get('registration_no', ''),
            company_data.get('address', ''),
            company_data.get('phone', ''),
            company_data.get('email', ''),
            company_data.get('gst_no', '')
        )
        return self.execute_update(query, params)

    def get_all_companies(self) -> List[Dict[str, Any]]:
        return self.execute_query("SELECT * FROM companies ORDER BY name")

    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        result = self.execute_query("SELECT * FROM companies WHERE id = %s", (company_id,))
        return result[0] if result else None

    def update_company(self, company_id: int, company_data: Dict[str, Any]) -> bool:
        query = '''UPDATE companies SET name = %s, registration_no = %s, address = %s, 
                   phone = %s, email = %s, gst_no = %s WHERE id = %s'''
        params = (
            company_data['name'],
            company_data.get('registration_no', ''),
            company_data.get('address', ''),
            company_data.get('phone', ''),
            company_data.get('email', ''),
            company_data.get('gst_no', ''),
            company_id
        )
        return self.execute_update(query, params)

    def delete_company(self, company_id: int) -> bool:
        return self.execute_update("DELETE FROM companies WHERE id = %s", (company_id,))

    # Book methods
    def add_book(self, book_data: Dict[str, Any]) -> bool:
        query = '''INSERT INTO books (company_id, name, author, category, language, isbn,
                   purchase_price, selling_price, stock_quantity)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        params = (
            book_data['company_id'],
            book_data['name'],
            book_data.get('author', ''),
            book_data.get('category', ''),
            book_data.get('language', 'English'),
            book_data.get('isbn', ''),
            book_data.get('purchase_price', 0),
            book_data.get('selling_price', 0),
            book_data.get('stock_quantity', 0)
        )
        return self.execute_update(query, params)

    def get_books_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        query = '''SELECT b.*, c.name as company_name FROM books b
                   JOIN companies c ON b.company_id = c.id
                   WHERE b.company_id = %s ORDER BY b.name'''
        return self.execute_query(query, (company_id,))

    def get_all_books(self) -> List[Dict[str, Any]]:
        query = '''SELECT b.*, c.name as company_name FROM books b
                   JOIN companies c ON b.company_id = c.id ORDER BY b.name'''
        return self.execute_query(query)

    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        result = self.execute_query("SELECT * FROM books WHERE id = %s", (book_id,))
        return result[0] if result else None

    def update_book(self, book_id: int, book_data: Dict[str, Any]) -> bool:
        query = '''UPDATE books SET name = %s, author = %s, category = %s, language = %s,
                   isbn = %s, purchase_price = %s, selling_price = %s, stock_quantity = %s
                   WHERE id = %s'''
        params = (
            book_data['name'],
            book_data.get('author', ''),
            book_data.get('category', ''),
            book_data.get('language', 'English'),
            book_data.get('isbn', ''),
            book_data.get('purchase_price', 0),
            book_data.get('selling_price', 0),
            book_data.get('stock_quantity', 0),
            book_id
        )
        return self.execute_update(query, params)

    def update_book_stock(self, book_id: int, quantity_change: int, movement_type: str = 'ADJUSTMENT') -> bool:
        query = "UPDATE books SET stock_quantity = stock_quantity + %s WHERE id = %s"
        success = self.execute_update(query, (quantity_change, book_id))
        if success:
            movement_query = '''INSERT INTO stock_movements (book_id, movement_type, quantity, reference_type)
                                VALUES (%s, %s, %s, %s)'''
            self.execute_update(movement_query, (book_id, movement_type, abs(quantity_change), 'ADJUSTMENT'))
        return success

    def delete_book(self, book_id: int) -> bool:
        return self.execute_update("DELETE FROM books WHERE id = %s", (book_id,))

    # Customer methods
    def add_customer(self, customer_data: Dict[str, Any]) -> bool:
        query = '''INSERT INTO customers (company_id, name, phone, email, address, gst_no)
                   VALUES (%s, %s, %s, %s, %s, %s)'''
        params = (
            customer_data['company_id'],
            customer_data['name'],
            customer_data.get('phone', ''),
            customer_data.get('email', ''),
            customer_data.get('address', ''),
            customer_data.get('gst_no', '')
        )
        return self.execute_update(query, params)

    def get_customers_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        query = '''SELECT c.*, comp.name as company_name FROM customers c
                   JOIN companies comp ON c.company_id = comp.id
                   WHERE c.company_id = %s ORDER BY c.name'''
        return self.execute_query(query, (company_id,))

    def get_all_customers(self) -> List[Dict[str, Any]]:
        query = '''SELECT c.*, comp.name as company_name FROM customers c
                   JOIN companies comp ON c.company_id = comp.id ORDER BY c.name'''
        return self.execute_query(query)

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        result = self.execute_query("SELECT * FROM customers WHERE id = %s", (customer_id,))
        return result[0] if result else None

    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        query = '''UPDATE customers SET name = %s, phone = %s, email = %s, address = %s, gst_no = %s
                   WHERE id = %s'''
        params = (
            customer_data['name'],
            customer_data.get('phone', ''),
            customer_data.get('email', ''),
            customer_data.get('address', ''),
            customer_data.get('gst_no', ''),
            customer_id
        )
        return self.execute_update(query, params)

    def delete_customer(self, customer_id: int) -> bool:
        return self.execute_update("DELETE FROM customers WHERE id = %s", (customer_id,))

    # Purchase methods
    def add_purchase(self, purchase_data: Dict[str, Any]) -> bool:
        query = '''INSERT INTO purchases (company_id, book_id, supplier_name, quantity,
                   price_per_unit, total_amount, purchase_date, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
        params = (
            purchase_data['company_id'],
            purchase_data['book_id'],
            purchase_data.get('supplier_name', ''),
            purchase_data['quantity'],
            purchase_data['price_per_unit'],
            purchase_data['total_amount'],
            purchase_data.get('purchase_date', datetime.now().date()),
            purchase_data.get('notes', '')
        )
        success = self.execute_update(query, params)
        if success:
            self.update_book_stock(purchase_data['book_id'], purchase_data['quantity'], 'IN')
        return success

    def get_purchases_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        query = '''SELECT p.*, b.name as book_name, b.author, c.name as company_name
                   FROM purchases p
                   JOIN books b ON p.book_id = b.id
                   JOIN companies c ON p.company_id = c.id
                   WHERE p.company_id = %s ORDER BY p.purchase_date DESC'''
        return self.execute_query(query, (company_id,))

    def get_latest_purchase_price(self, book_id: int) -> float:
        query = '''
            SELECT price_per_unit FROM purchases
            WHERE book_id = %s
            ORDER BY purchase_date DESC, id DESC
            LIMIT 1
        '''
        result = self.execute_query(query, (book_id,))
        return result[0]['price_per_unit'] if result else 0.0

    # Sale methods
    def add_sale(self, sale_data: Dict[str, Any], sale_items: List[Dict[str, Any]]) -> bool:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert sale record
                    sale_query = '''INSERT INTO sales (company_id, customer_id, invoice_no, sale_date,
                                   total_amount, discount, tax_amount, final_amount, payment_status, notes)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id'''
                    sale_params = (
                        sale_data['company_id'],
                        sale_data.get('customer_id'),
                        sale_data['invoice_no'],
                        sale_data.get('sale_date', datetime.now().date()),
                        sale_data['total_amount'],
                        sale_data.get('discount', 0),
                        sale_data.get('tax_amount', 0),
                        sale_data['final_amount'],
                        sale_data.get('payment_status', 'Completed'),
                        sale_data.get('notes', '')
                    )
                    cursor.execute(sale_query, sale_params)
                    sale_id = cursor.fetchone()[0]

                    # Insert sale items and update stock
                    for item in sale_items:
                        item_query = '''INSERT INTO sale_items (sale_id, book_id, quantity, price_per_unit, total_price)
                                       VALUES (%s, %s, %s, %s, %s)'''
                        item_params = (
                            sale_id,
                            item['book_id'],
                            item['quantity'],
                            item['price_per_unit'],
                            item['total_price']
                        )
                        cursor.execute(item_query, item_params)

                        # Update book stock
                        stock_query = "UPDATE books SET stock_quantity = stock_quantity - %s WHERE id = %s"
                        cursor.execute(stock_query, (item['quantity'], item['book_id']))

                        # Record stock movement
                        movement_query = '''INSERT INTO stock_movements (book_id, movement_type, quantity,
                                       reference_type, reference_id) VALUES (%s, %s, %s, %s, %s)'''
                        cursor.execute(movement_query, (item['book_id'], 'OUT', item['quantity'], 'SALE', sale_id))

                    conn.commit()
                    return True
        except Exception as e:
            print(f"Sale transaction error: {e}")
            traceback.print_exc()
            return False

    def get_sales_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        query = '''SELECT s.*, c.name as customer_name, comp.name as company_name
                   FROM sales s
                   LEFT JOIN customers c ON s.customer_id = c.id
                   JOIN companies comp ON s.company_id = comp.id
                   WHERE s.company_id = %s ORDER BY s.sale_date DESC'''
        return self.execute_query(query, (company_id,))

    def get_sale_details(self, sale_id: int) -> Dict[str, Any]:
        sale_query = '''SELECT s.*, c.name as customer_name, c.phone as customer_phone,
                       c.address as customer_address, comp.name as company_name
                       FROM sales s
                       LEFT JOIN customers c ON s.customer_id = c.id
                       JOIN companies comp ON s.company_id = comp.id
                       WHERE s.id = %s'''
        sale_result = self.execute_query(sale_query, (sale_id,))
        items_query = '''SELECT si.*, b.name as book_name, b.author
                        FROM sale_items si
                        JOIN books b ON si.book_id = b.id
                        WHERE si.sale_id = %s'''
        items_result = self.execute_query(items_query, (sale_id,))
        return {
            'sale': sale_result[0] if sale_result else None,
            'items': items_result
        }

    def generate_invoice_number(self, company_id: int) -> str:
        query = "SELECT COUNT(*) as count FROM sales WHERE company_id = %s"
        result = self.execute_query(query, (company_id,))
        count = result[0]['count'] + 1
        return f"INV-{company_id:03d}-{count:06d}"
