"""
PDF Generator
Handles PDF generation for invoices and reports
"""

import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import black, blue, red, grey
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from num2words import num2words

class PDFGenerator:
    """PDF generation utility class"""
    
    def __init__(self, output_dir='generated_files'):
        self.output_dir = output_dir
        self.ensure_output_dir()
        
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_invoice_pdf(self, invoice, company=None, customer=None):
        """Generate PDF for an invoice"""
        try:
            # Create filename
            filename = f"invoice_{invoice.invoice_number.replace('/', '_')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create document
            doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=blue,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=black,
                alignment=TA_LEFT,
                spaceAfter=10
            )
            
            normal_style = styles['Normal']
            
            # Company Header
            if company:
                story.append(Paragraph(f"<b>{company.name}</b>", title_style))
                
                company_info = []
                if company.address:
                    company_info.append(company.address)
                if company.city and company.state:
                    company_info.append(f"{company.city}, {company.state}")
                if company.pincode:
                    company_info.append(f"PIN: {company.pincode}")
                if company.gstin:
                    company_info.append(f"GSTIN: {company.gstin}")
                if company.contact_phone:
                    company_info.append(f"Phone: {company.contact_phone}")
                if company.email:
                    company_info.append(f"Email: {company.email}")
                
                for info in company_info:
                    story.append(Paragraph(info, normal_style))
                
                story.append(Spacer(1, 20))
            
            # Invoice Title
            story.append(Paragraph("<b>TAX INVOICE</b>", heading_style))
            story.append(Spacer(1, 10))
            
            # Invoice Details Table
            invoice_details = [
                ['Invoice Number:', invoice.invoice_number],
                ['Invoice Date:', invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else ''],
                ['PO Number:', invoice.po_number or ''],
                ['PO Date:', invoice.po_date.strftime('%d-%m-%Y') if invoice.po_date else ''],
                ['Payment Mode:', invoice.payment_mode or ''],
                ['Transport:', invoice.transport or ''],
                ['Dispatch From:', invoice.dispatch_from or '']
            ]
            
            # Customer details
            if customer:
                invoice_details.extend([
                    ['', ''],  # Empty row
                    ['Bill To:', ''],
                    ['Customer:', customer.name],
                    ['Address:', customer.address or ''],
                    ['City, State:', f"{customer.city or ''}, {customer.state or ''}"],
                    ['PIN Code:', customer.pincode or ''],
                    ['GSTIN:', customer.gstin or ''],
                    ['Contact Person:', customer.contact_person or ''],
                    ['Phone:', customer.phone or '']
                ])
            
            invoice_table = Table(invoice_details, colWidths=[2*inch, 4*inch])
            invoice_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Items Table
            if invoice.items:
                # Table headers
                headers = ['S.No.', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'Discount %', 'Amount']
                items_data = [headers]
                
                # Add items
                for i, item in enumerate(invoice.items, 1):
                    hsn_code = ''
                    if item.product and item.product.hsn_code:
                        hsn_code = item.product.hsn_code
                    
                    items_data.append([
                        str(i),
                        item.description or '',
                        hsn_code,
                        f"{float(item.quantity):.2f}" if item.quantity else '0.00',
                        item.unit or '',
                        f"₹{float(item.rate):.2f}" if item.rate else '₹0.00',
                        f"{float(item.discount_percent):.1f}%" if item.discount_percent else '0.0%',
                        f"₹{float(item.amount):.2f}" if item.amount else '₹0.00'
                    ])
                
                # Add totals
                items_data.extend([
                    ['', '', '', '', '', '', 'Subtotal:', f"₹{float(invoice.subtotal):.2f}" if invoice.subtotal else '₹0.00'],
                    ['', '', '', '', '', '', 'GST (18%):', f"₹{float(invoice.gst_amount):.2f}" if invoice.gst_amount else '₹0.00'],
                    ['', '', '', '', '', '', 'Total:', f"₹{float(invoice.total_amount):.2f}" if invoice.total_amount else '₹0.00']
                ])
                
                items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch, 1.2*inch])
                items_table.setStyle(TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    
                    # Data styling
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No. center
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description left
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Numbers right
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.beige, colors.white]),
                    
                    # Totals styling
                    ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(items_table)
                story.append(Spacer(1, 20))
            
            # Amount in words
            if invoice.total_amount:
                amount_words = num2words(float(invoice.total_amount), lang='en_IN').title()
                story.append(Paragraph(f"<b>Amount in Words:</b> {amount_words} Rupees Only", normal_style))
                story.append(Spacer(1, 20))
            
            # Banking details
            if company and company.bank_name:
                story.append(Paragraph("<b>Banking Details:</b>", heading_style))
                banking_details = [
                    ['Bank Name:', company.bank_name],
                    ['Account Number:', company.account_number or ''],
                    ['IFSC Code:', company.ifsc_code or '']
                ]
                
                banking_table = Table(banking_details, colWidths=[2*inch, 4*inch])
                banking_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                story.append(banking_table)
                story.append(Spacer(1, 20))
            
            # Terms and conditions
            terms = [
                "Terms & Conditions:",
                "1. GST 18% extra as applicable.",
                "2. Payment Terms: 30 Days Net from the date of Invoice.",
                "3. Delivery Lead Time: 2-3 Weeks",
                "4. Packing & Forwarding Charges: Nil",
                "5. Freight: Nil",
                "6. Validity: One Year"
            ]
            
            for term in terms:
                style = heading_style if term.startswith('Terms') else normal_style
                story.append(Paragraph(term, style))
            
            story.append(Spacer(1, 30))
            
            # Signature
            story.append(Paragraph("<b>For " + (company.name if company else "Company") + "</b>", normal_style))
            story.append(Spacer(1, 50))
            story.append(Paragraph("Authorized Signatory", normal_style))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")
    
    def generate_invoice_pdf_buffer(self, invoice, company=None, customer=None):
        """Generate PDF for an invoice and return as BytesIO buffer"""
        try:
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=blue,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=black,
                alignment=TA_LEFT,
                spaceAfter=10
            )
            
            normal_style = styles['Normal']
            
            # Company Header
            if company:
                story.append(Paragraph(f"<b>{company.name}</b>", title_style))
                
                company_info = []
                if company.address:
                    company_info.append(company.address)
                if company.city and company.state:
                    company_info.append(f"{company.city}, {company.state}")
                if company.pincode:
                    company_info.append(f"PIN: {company.pincode}")
                if company.gstin:
                    company_info.append(f"GSTIN: {company.gstin}")
                if company.contact_phone:
                    company_info.append(f"Phone: {company.contact_phone}")
                if company.email:
                    company_info.append(f"Email: {company.email}")
                
                for info in company_info:
                    story.append(Paragraph(info, normal_style))
                
                story.append(Spacer(1, 20))
            
            # Invoice Title
            story.append(Paragraph("<b>TAX INVOICE</b>", heading_style))
            story.append(Spacer(1, 10))
            
            # Invoice Details Table
            invoice_details = [
                ['Invoice Number:', invoice.invoice_number],
                ['Invoice Date:', invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else ''],
                ['PO Number:', invoice.po_number or ''],
                ['PO Date:', invoice.po_date.strftime('%d-%m-%Y') if invoice.po_date else ''],
                ['Payment Mode:', invoice.payment_mode or ''],
                ['Transport:', invoice.transport or ''],
                ['Dispatch From:', invoice.dispatch_from or '']
            ]
            
            # Customer details
            if customer:
                invoice_details.extend([
                    ['', ''],  # Empty row
                    ['Bill To:', ''],
                    ['Customer:', customer.name],
                    ['Address:', customer.address or ''],
                    ['City, State:', f"{customer.city or ''}, {customer.state or ''}"],
                    ['PIN Code:', customer.pincode or ''],
                    ['GSTIN:', customer.gstin or ''],
                    ['Contact Person:', customer.contact_person or ''],
                    ['Phone:', customer.phone or '']
                ])
            
            invoice_table = Table(invoice_details, colWidths=[2*inch, 4*inch])
            invoice_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Items Table
            if invoice.items:
                # Table headers
                headers = ['S.No.', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'Discount %', 'Amount']
                items_data = [headers]
                
                # Add items
                for i, item in enumerate(invoice.items, 1):
                    hsn_code = ''
                    if item.product and item.product.hsn_code:
                        hsn_code = item.product.hsn_code
                    
                    items_data.append([
                        str(i),
                        item.description or '',
                        hsn_code,
                        f"{float(item.quantity):.2f}" if item.quantity else '0.00',
                        item.unit or '',
                        f"₹{float(item.rate):.2f}" if item.rate else '₹0.00',
                        f"{float(item.discount_percent):.1f}%" if item.discount_percent else '0.0%',
                        f"₹{float(item.amount):.2f}" if item.amount else '₹0.00'
                    ])
                
                # Add totals
                items_data.extend([
                    ['', '', '', '', '', '', 'Subtotal:', f"₹{float(invoice.subtotal):.2f}" if invoice.subtotal else '₹0.00'],
                    ['', '', '', '', '', '', 'GST (18%):', f"₹{float(invoice.gst_amount):.2f}" if invoice.gst_amount else '₹0.00'],
                    ['', '', '', '', '', '', 'Total:', f"₹{float(invoice.total_amount):.2f}" if invoice.total_amount else '₹0.00']
                ])
                
                items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch, 1.2*inch])
                items_table.setStyle(TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    
                    # Data styling
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No. center
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description left
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Numbers right
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.beige, colors.white]),
                    
                    # Totals styling
                    ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(items_table)
                story.append(Spacer(1, 20))
            
            # Amount in words
            if invoice.total_amount:
                amount_words = num2words(float(invoice.total_amount), lang='en_IN').title()
                story.append(Paragraph(f"<b>Amount in Words:</b> {amount_words} Rupees Only", normal_style))
                story.append(Spacer(1, 20))
            
            # Banking details
            if company and company.bank_name:
                story.append(Paragraph("<b>Banking Details:</b>", heading_style))
                banking_details = [
                    ['Bank Name:', company.bank_name],
                    ['Account Number:', company.account_number or ''],
                    ['IFSC Code:', company.ifsc_code or '']
                ]
                
                banking_table = Table(banking_details, colWidths=[2*inch, 4*inch])
                banking_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                story.append(banking_table)
                story.append(Spacer(1, 20))
            
            # Terms and conditions
            terms = [
                "Terms & Conditions:",
                "1. GST 18% extra as applicable.",
                "2. Payment Terms: 30 Days Net from the date of Invoice.",
                "3. Delivery Lead Time: 2-3 Weeks",
                "4. Packing & Forwarding Charges: Nil",
                "5. Freight: Nil",
                "6. Validity: One Year"
            ]
            
            for term in terms:
                style = heading_style if term.startswith('Terms') else normal_style
                story.append(Paragraph(term, style))
            
            story.append(Spacer(1, 30))
            
            # Signature
            story.append(Paragraph("<b>For " + (company.name if company else "Company") + "</b>", normal_style))
            story.append(Spacer(1, 50))
            story.append(Paragraph("Authorized Signatory", normal_style))
            
            # Build PDF
            doc.build(story)
            
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            raise Exception(f"Error generating PDF buffer: {str(e)}")
    
    def generate_report_pdf(self, title, data, headers=None, filename=None):
        """Generate a generic report PDF"""
        try:
            if not filename:
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Create document
            doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=0.5*inch)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=blue,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Title
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 20))
            
            # Data table
            if data:
                if headers:
                    table_data = [headers] + data
                else:
                    table_data = data
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
            
            # Generated timestamp
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", 
                                 styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Error generating report PDF: {str(e)}")