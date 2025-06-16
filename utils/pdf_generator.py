from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
from typing import Dict, List, Any

class PDFInvoiceGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_fonts()
        self.setup_custom_styles()
    
    def setup_fonts(self):
        """Setup fonts for Hindi/Unicode support"""
        try:
            # Try to register a Unicode-compatible font
            # Use DejaVu Sans which supports Hindi characters
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
                self.unicode_font = 'DejaVuSans'
                self.unicode_font_bold = 'DejaVuSans-Bold'
            else:
                # Fallback to default fonts
                self.unicode_font = 'Helvetica'
                self.unicode_font_bold = 'Helvetica-Bold'
        except Exception as e:
            print(f"Font setup warning: {e}")
            self.unicode_font = 'Helvetica'
            self.unicode_font_bold = 'Helvetica-Bold'
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.darkblue,
            alignment=1,  # Center alignment
            fontName=self.unicode_font_bold
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkred,
            alignment=1,
            fontName=self.unicode_font_bold
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            alignment=1,
            fontName=self.unicode_font
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue,
            fontName=self.unicode_font_bold
        ))
        
        self.styles.add(ParagraphStyle(
            name='UnicodeNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName=self.unicode_font
        ))
    
    def generate_invoice(self, invoice_data: Dict[str, Any], filename: str = None) -> str:
        """Generate PDF invoice and return the filename"""
        if not filename:
            filename = f"invoice_{invoice_data['sale']['invoice_no']}.pdf"
        
        # Ensure invoices directory exists
        os.makedirs("invoices", exist_ok=True)
        filepath = os.path.join("invoices", filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Company Header
        company_name = Paragraph(f"<b>{invoice_data['company']['name']}</b>", self.styles['CompanyName'])
        story.append(company_name)
        
        if invoice_data['company'].get('address'):
            company_address = Paragraph(invoice_data['company']['address'], self.styles['CompanyDetails'])
            story.append(company_address)
        
        contact_info = []
        if invoice_data['company'].get('phone'):
            contact_info.append(f"Phone: {invoice_data['company']['phone']}")
        if invoice_data['company'].get('email'):
            contact_info.append(f"Email: {invoice_data['company']['email']}")
        if invoice_data['company'].get('gst_no'):
            contact_info.append(f"GST No: {invoice_data['company']['gst_no']}")
        
        if contact_info:
            contact_para = Paragraph(" | ".join(contact_info), self.styles['CompanyDetails'])
            story.append(contact_para)
        
        story.append(Spacer(1, 20))
        
        # Invoice Title
        invoice_title = Paragraph("<b>INVOICE</b>", self.styles['InvoiceTitle'])
        story.append(invoice_title)
        story.append(Spacer(1, 20))
        
        # Invoice Details Table
        invoice_details_data = [
            ['Invoice No:', invoice_data['sale']['invoice_no'], 'Date:', invoice_data['sale']['sale_date']],
            ['Payment Status:', invoice_data['sale']['payment_status'], '', '']
        ]
        
        invoice_details_table = Table(invoice_details_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
        invoice_details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(invoice_details_table)
        story.append(Spacer(1, 20))
        
        # Customer Details
        if invoice_data.get('customer'):
            customer_header = Paragraph("<b>Bill To:</b>", self.styles['SectionHeader'])
            story.append(customer_header)
            
            customer_details = [
                f"<b>{invoice_data['customer']['name']}</b>",
            ]
            
            if invoice_data['customer'].get('address'):
                customer_details.append(invoice_data['customer']['address'])
            if invoice_data['customer'].get('phone'):
                customer_details.append(f"Phone: {invoice_data['customer']['phone']}")
            if invoice_data['customer'].get('email'):
                customer_details.append(f"Email: {invoice_data['customer']['email']}")
            if invoice_data['customer'].get('gst_no'):
                customer_details.append(f"GST No: {invoice_data['customer']['gst_no']}")
            
            for detail in customer_details:
                story.append(Paragraph(detail, self.styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Items Table
        items_header = Paragraph("<b>Items:</b>", self.styles['SectionHeader'])
        story.append(items_header)
        
        # Table headers
        items_data = [['S.No.', 'Book Name', 'Author', 'Qty', 'Rate', 'Amount']]
        
        # Table data
        for i, item in enumerate(invoice_data['items'], 1):
            items_data.append([
                str(i),
                item['book_name'][:30] + ('...' if len(item['book_name']) > 30 else ''),
                item.get('author', '')[:20] + ('...' if len(item.get('author', '')) > 20 else ''),
                str(item['quantity']),
                f"₹{item['price_per_unit']:.2f}",
                f"₹{item['total_price']:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 0.7*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),  # Left align book name and author
            ('FONTNAME', (0, 0), (-1, 0), self.unicode_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.unicode_font),  # Use Unicode font for content
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals Table
        totals_data = [
            ['Subtotal:', f"₹{invoice_data['sale']['total_amount']:.2f}"],
            ['Discount:', f"₹{invoice_data['sale']['discount']:.2f}"],
            ['Tax:', f"₹{invoice_data['sale']['tax_amount']:.2f}"],
            ['Total Amount:', f"₹{invoice_data['sale']['final_amount']:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Notes
        if invoice_data['sale'].get('notes'):
            notes_header = Paragraph("<b>Notes:</b>", self.styles['SectionHeader'])
            story.append(notes_header)
            notes_para = Paragraph(invoice_data['sale']['notes'], self.styles['Normal'])
            story.append(notes_para)
            story.append(Spacer(1, 20))
        
        # Footer
        footer_data = [
            ['Terms & Conditions:', 'Authorized Signature:'],
            ['1. Payment due within 30 days', ''],
            ['2. Goods once sold will not be taken back', ''],
            ['3. Subject to jurisdiction only', '']
        ]
        
        footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        return filepath
    
    def generate_report_pdf(self, report_data: Dict[str, Any], filename: str = None) -> str:
        """Generate PDF report and return the filename"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Ensure reports directory exists
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Report Title
        title = Paragraph(f"<b>{report_data['title']}</b>", self.styles['InvoiceTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Report Period
        if report_data.get('period'):
            period = Paragraph(f"Report Period: {report_data['period']}", self.styles['Normal'])
            story.append(period)
            story.append(Spacer(1, 10))
        
        # Company Name
        if report_data.get('company_name'):
            company = Paragraph(f"Company: {report_data['company_name']}", self.styles['Normal'])
            story.append(company)
            story.append(Spacer(1, 20))
        
        # Summary Table
        if report_data.get('summary'):
            summary_header = Paragraph("<b>Summary:</b>", self.styles['SectionHeader'])
            story.append(summary_header)
            
            summary_data = []
            for key, value in report_data['summary'].items():
                summary_data.append([key, str(value)])
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
        
        # Data Table
        if report_data.get('data') and report_data.get('headers'):
            data_header = Paragraph("<b>Detailed Data:</b>", self.styles['SectionHeader'])
            story.append(data_header)
            
            # Prepare table data
            table_data = [report_data['headers']]
            table_data.extend(report_data['data'])
            
            # Calculate column widths
            num_cols = len(report_data['headers'])
            col_width = 6.5 * inch / num_cols
            
            data_table = Table(table_data, colWidths=[col_width] * num_cols)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(data_table)
        
        # Build PDF
        doc.build(story)
        return filepath
