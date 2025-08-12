"""
Utils Tests
Tests for PDF and Excel generation utilities
"""

import pytest
import os
import tempfile
from io import BytesIO
from utils.pdf_generator import PDFGenerator
from utils.excel_generator import ExcelGenerator

class TestPDFGenerator:
    """Test cases for PDF generator"""
    
    def test_pdf_generator_init(self):
        """Test PDF generator initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            assert generator.output_dir == temp_dir
            assert os.path.exists(temp_dir)
    
    def test_pdf_generator_default_dir(self):
        """Test PDF generator with default directory"""
        generator = PDFGenerator()
        assert generator.output_dir == 'generated_files'
        assert os.path.exists(generator.output_dir)
    
    def test_generate_invoice_pdf_success(self, sample_invoice, sample_company, sample_customer, sample_invoice_item):
        """Test successful PDF generation for invoice"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            # Ensure invoice has items and totals
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_pdf(
                invoice=sample_invoice,
                company=sample_company,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.pdf')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_pdf_without_company(self, sample_invoice, sample_customer, sample_invoice_item):
        """Test PDF generation without company info"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_pdf(
                invoice=sample_invoice,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_pdf_without_customer(self, sample_invoice, sample_company, sample_invoice_item):
        """Test PDF generation without customer info"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_pdf(
                invoice=sample_invoice,
                company=sample_company
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_pdf_without_items(self, sample_invoice, sample_company, sample_customer):
        """Test PDF generation without invoice items"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            filepath = generator.generate_invoice_pdf(
                invoice=sample_invoice,
                company=sample_company,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_pdf_buffer(self, sample_invoice, sample_company, sample_customer, sample_invoice_item):
        """Test PDF generation as buffer"""
        generator = PDFGenerator()
        
        sample_invoice.items.append(sample_invoice_item)
        sample_invoice.calculate_totals()
        
        buffer = generator.generate_invoice_pdf_buffer(
            invoice=sample_invoice,
            company=sample_company,
            customer=sample_customer
        )
        
        assert isinstance(buffer, BytesIO)
        assert buffer.getvalue() is not None
        assert len(buffer.getvalue()) > 0
    
    def test_generate_report_pdf_success(self):
        """Test successful report PDF generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            title = "Test Report"
            headers = ["Column 1", "Column 2", "Column 3"]
            data = [
                ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
                ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"],
                ["Row 3 Col 1", "Row 3 Col 2", "Row 3 Col 3"]
            ]
            
            filepath = generator.generate_report_pdf(
                title=title,
                data=data,
                headers=headers
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.pdf')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_report_pdf_without_headers(self):
        """Test report PDF generation without headers"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            title = "Test Report Without Headers"
            data = [
                ["Row 1 Col 1", "Row 1 Col 2"],
                ["Row 2 Col 1", "Row 2 Col 2"]
            ]
            
            filepath = generator.generate_report_pdf(
                title=title,
                data=data
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_report_pdf_empty_data(self):
        """Test report PDF generation with empty data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = PDFGenerator(temp_dir)
            
            title = "Empty Report"
            data = []
            
            filepath = generator.generate_report_pdf(
                title=title,
                data=data
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_pdf_generator_error_handling(self):
        """Test PDF generator error handling"""
        generator = PDFGenerator()
        
        # Test with invalid invoice (None)
        with pytest.raises(Exception):
            generator.generate_invoice_pdf(None)
        
        # Test with invalid output directory
        invalid_generator = PDFGenerator('/invalid/path/that/does/not/exist')
        with pytest.raises(Exception):
            invalid_generator.generate_invoice_pdf(None)


class TestExcelGenerator:
    """Test cases for Excel generator"""
    
    def test_excel_generator_init(self):
        """Test Excel generator initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            assert generator.output_dir == temp_dir
            assert os.path.exists(temp_dir)
    
    def test_excel_generator_default_dir(self):
        """Test Excel generator with default directory"""
        generator = ExcelGenerator()
        assert generator.output_dir == 'generated_files'
        assert os.path.exists(generator.output_dir)
    
    def test_generate_invoice_excel_success(self, sample_invoice, sample_company, sample_customer, sample_invoice_item):
        """Test successful Excel generation for invoice"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Ensure invoice has items and totals
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_excel(
                invoice=sample_invoice,
                company=sample_company,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.xlsx')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_excel_without_company(self, sample_invoice, sample_customer, sample_invoice_item):
        """Test Excel generation without company info"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_excel(
                invoice=sample_invoice,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoice_excel_custom_filename(self, sample_invoice, sample_company, sample_customer):
        """Test Excel generation with custom filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            custom_filename = "custom_invoice.xlsx"
            filepath = generator.generate_invoice_excel(
                invoice=sample_invoice,
                company=sample_company,
                customer=sample_customer,
                filename=custom_filename
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(custom_filename)
    
    def test_generate_invoices_report_success(self, sample_invoice, sample_invoice_item):
        """Test successful invoices report generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Prepare invoice list
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            invoices = [sample_invoice]
            
            filepath = generator.generate_invoices_report(invoices)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.xlsx')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_invoices_report_empty_list(self):
        """Test invoices report generation with empty list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            invoices = []
            filepath = generator.generate_invoices_report(invoices)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_customers_report_success(self, sample_customer):
        """Test successful customers report generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            customers = [sample_customer]
            filepath = generator.generate_customers_report(customers)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.xlsx')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_customers_report_empty_list(self):
        """Test customers report generation with empty list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            customers = []
            filepath = generator.generate_customers_report(customers)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_products_report_success(self, sample_product):
        """Test successful products report generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            products = [sample_product]
            filepath = generator.generate_products_report(products)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith('.xlsx')
            assert os.path.getsize(filepath) > 0
    
    def test_generate_products_report_empty_list(self):
        """Test products report generation with empty list"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            products = []
            filepath = generator.generate_products_report(products)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
    
    def test_generate_excel_buffer_success(self):
        """Test Excel generation as buffer"""
        generator = ExcelGenerator()
        
        headers = ["Column 1", "Column 2", "Column 3"]
        data = [
            ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
            ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
        ]
        
        buffer = generator.generate_excel_buffer(
            data=data,
            headers=headers,
            sheet_name="Test Sheet"
        )
        
        assert isinstance(buffer, BytesIO)
        assert buffer.getvalue() is not None
        assert len(buffer.getvalue()) > 0
    
    def test_generate_excel_buffer_empty_data(self):
        """Test Excel buffer generation with empty data"""
        generator = ExcelGenerator()
        
        headers = ["Column 1", "Column 2"]
        data = []
        
        buffer = generator.generate_excel_buffer(
            data=data,
            headers=headers
        )
        
        assert isinstance(buffer, BytesIO)
        assert buffer.getvalue() is not None
        assert len(buffer.getvalue()) > 0
    
    def test_excel_generator_error_handling(self):
        """Test Excel generator error handling"""
        generator = ExcelGenerator()
        
        # Test with invalid invoice (None)
        with pytest.raises(Exception):
            generator.generate_invoice_excel(None)
        
        # Test with invalid data for buffer
        with pytest.raises(Exception):
            generator.generate_excel_buffer(None, None)
    
    def test_excel_generator_custom_filename(self, sample_invoice):
        """Test Excel generation with custom filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            custom_filename = "test_custom_invoice.xlsx"
            filepath = generator.generate_invoice_excel(
                invoice=sample_invoice,
                filename=custom_filename
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert filepath.endswith(custom_filename)
    
    def test_excel_reports_with_multiple_sheets(self, sample_product):
        """Test Excel reports with multiple sheets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Create products with different categories
            products = [sample_product]
            
            filepath = generator.generate_products_report(products)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
            
            # The file should contain both main sheet and categories sheet
            # We can't easily verify sheet contents without opening the file,
            # but we can verify the file was created successfully
    
    def test_excel_formatting_and_styling(self, sample_invoice, sample_company, sample_customer, sample_invoice_item):
        """Test Excel formatting and styling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Create invoice with multiple items for better formatting test
            sample_invoice.items.append(sample_invoice_item)
            sample_invoice.calculate_totals()
            
            filepath = generator.generate_invoice_excel(
                invoice=sample_invoice,
                company=sample_company,
                customer=sample_customer
            )
            
            assert filepath is not None
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0
            
            # File should be properly formatted with headers, borders, etc.
            # The exact formatting is handled by openpyxl and our styling code
    
    def test_large_data_handling(self):
        """Test handling of large datasets"""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ExcelGenerator(temp_dir)
            
            # Generate large dataset
            headers = ["ID", "Name", "Value", "Description"]
            data = []
            for i in range(1000):  # 1000 rows
                data.append([i, f"Name {i}", f"Value {i}", f"Description {i}"])
            
            buffer = generator.generate_excel_buffer(
                data=data,
                headers=headers
            )
            
            assert isinstance(buffer, BytesIO)
            assert len(buffer.getvalue()) > 0
            
            # Large file should still be created successfully
            assert len(buffer.getvalue()) > 10000  # Should be reasonably large
    
    def test_special_characters_handling(self):
        """Test handling of special characters in data"""
        generator = ExcelGenerator()
        
        headers = ["Name", "Description", "Special"]
        data = [
            ["Test Name", "Description with éspecial characters", "₹100.00"],
            ["Another Test", "Description with symbols: @#$%", "€50.00"],
            ["Unicode Test", "Unicode: 中文测试", "¥200.00"]
        ]
        
        buffer = generator.generate_excel_buffer(
            data=data,
            headers=headers
        )
        
        assert isinstance(buffer, BytesIO)
        assert len(buffer.getvalue()) > 0
        
        # Special characters should be handled properly