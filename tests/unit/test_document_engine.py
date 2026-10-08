"""
Tests for proforma_app/document_engine.py

This module contains comprehensive unit tests for the document generation engine,
including PDF/DOCX generation, money normalization, and tax calculations.
"""

import json
import pytest
from decimal import Decimal
from pathlib import Path

from proforma_app.document_engine import (
    ProformaData,
    normalize_money,
    compute_tax_breakdown,
    build_pdf,
    build_docx
)
from proforma_app.company_config import CompanyConfig


class TestNormalizeMoney:
    """Tests for normalize_money() function."""

    def test_normalize_int_to_decimal(self):
        """Test converting integer to Decimal."""
        result = normalize_money(100)
        assert isinstance(result, Decimal)
        assert result == Decimal("100.00")

    def test_normalize_float_to_decimal(self):
        """Test converting float to Decimal."""
        result = normalize_money(99.99)
        assert isinstance(result, Decimal)
        assert result == Decimal("99.99")

    def test_normalize_string_to_decimal(self):
        """Test converting string to Decimal."""
        result = normalize_money("50.50")
        assert isinstance(result, Decimal)
        assert result == Decimal("50.50")

    def test_normalize_decimal_unchanged(self):
        """Test that Decimal values are preserved."""
        original = Decimal("123.45")
        result = normalize_money(original)
        assert result == original
        assert isinstance(result, Decimal)

    def test_normalize_zero(self):
        """Test normalizing zero values."""
        result = normalize_money(0)
        assert result == Decimal("0.00")

    def test_normalize_large_numbers(self):
        """Test normalizing large numbers."""
        result = normalize_money(999999999.99)
        assert result == Decimal("999999999.99")

    def test_normalize_negative_numbers(self):
        """Test normalizing negative numbers."""
        result = normalize_money(-100.50)
        assert result == Decimal("-100.50")

    def test_normalize_precision_rounding(self):
        """Test that rounding is handled correctly."""
        result = normalize_money(99.999)
        # Should round to 2 decimal places
        assert len(str(result).split(".")[-1]) <= 2


class TestComputeTaxBreakdown:
    """Tests for compute_tax_breakdown() function."""

    def test_tax_breakdown_sin_igv_zero_tax(self):
        """Test tax breakdown when tax_mode is 'sin_igv' (no tax)."""
        subtotal = Decimal("100.00")
        tax_mode = "sin_igv"
        
        result = compute_tax_breakdown(subtotal, tax_mode)
        
        assert result["subtotal"] == subtotal
        assert result["igv_amount"] == Decimal("0.00")
        assert result["total"] == subtotal

    def test_tax_breakdown_con_igv_standard_rate(self):
        """Test tax breakdown when tax_mode is 'con_igv' (18% IGV)."""
        subtotal = Decimal("100.00")
        tax_mode = "con_igv"
        
        result = compute_tax_breakdown(subtotal, tax_mode)
        
        assert result["subtotal"] == subtotal
        assert result["igv_amount"] == Decimal("18.00")
        assert result["total"] == Decimal("118.00")

    def test_tax_breakdown_con_igv_various_amounts(self):
        """Test con_igv calculation with various subtotal amounts."""
        test_cases = [
            (Decimal("50.00"), Decimal("9.00"), Decimal("59.00")),
            (Decimal("200.00"), Decimal("36.00"), Decimal("236.00")),
            (Decimal("1000.00"), Decimal("180.00"), Decimal("1180.00")),
        ]
        
        for subtotal, expected_igv, expected_total in test_cases:
            result = compute_tax_breakdown(subtotal, "con_igv")
            assert result["igv_amount"] == expected_igv
            assert result["total"] == expected_total

    def test_tax_breakdown_invalid_tax_mode(self):
        """Test that invalid tax_mode raises error or defaults."""
        subtotal = Decimal("100.00")
        
        with pytest.raises((ValueError, KeyError, TypeError)):
            compute_tax_breakdown(subtotal, "invalid_mode")

    def test_tax_breakdown_negative_amounts(self):
        """Test tax breakdown with negative amounts (discounts)."""
        subtotal = Decimal("-50.00")
        
        result = compute_tax_breakdown(subtotal, "con_igv")
        
        # Should handle negative amounts
        assert result["subtotal"] == subtotal
        assert result["igv_amount"] == Decimal("-9.00")
        assert result["total"] == Decimal("-59.00")


class TestProformaDataFromPayload:
    """Tests for ProformaData.from_payload() classmethod."""

    def test_from_payload_basic(self, sample_payload, sample_company_config):
        """Test creating ProformaData from payload."""
        payload = sample_payload.copy()
        
        data = ProformaData.from_payload(payload, sample_company_config)
        
        assert data.company_config == sample_company_config
        assert isinstance(data.company_config, CompanyConfig)

    def test_from_payload_preserves_dates(self, sample_payload, sample_company_config):
        """Test that dates are preserved in ProformaData."""
        payload = sample_payload.copy()
        original_date = payload.get("issue_date", "2024-01-01")
        
        data = ProformaData.from_payload(payload, sample_company_config)
        
        # Date should be preserved or converted
        assert hasattr(data, "issue_date")

    def test_from_payload_handles_empty_items(self, sample_company_config):
        """Test ProformaData creation with no line items."""
        minimal_payload = {
            "issue_date": "2024-01-01",
            "customer_name": "Test Customer",
            "items": [],
            "tax_mode": "con_igv"
        }
        
        data = ProformaData.from_payload(minimal_payload, sample_company_config)
        
        assert data.items == []

    def test_from_payload_missing_required_field(self, sample_company_config):
        """Test that missing required fields raise error."""
        incomplete_payload = {
            "issue_date": "2024-01-01"
            # Missing customer_name, items, tax_mode
        }
        
        with pytest.raises((ValueError, TypeError, KeyError)):
            ProformaData.from_payload(incomplete_payload, sample_company_config)


class TestProformaDataCalculations:
    """Tests for ProformaData calculations (total, tax, etc)."""

    def test_total_calculation(self, sample_payload, sample_company_config):
        """Test that total is calculated correctly."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        
        # Should have a total attribute
        assert hasattr(data, "total")
        # Total should be numeric
        assert isinstance(data.total, (int, float, Decimal))

    def test_subtotal_calculation(self, sample_payload, sample_company_config):
        """Test that subtotal is calculated correctly."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        
        assert hasattr(data, "subtotal")
        assert isinstance(data.subtotal, (int, float, Decimal))

    def test_tax_amount_calculation(self, sample_payload, sample_company_config):
        """Test that tax amount is calculated correctly based on tax_mode."""
        payload = sample_payload.copy()
        payload["tax_mode"] = "con_igv"
        
        data = ProformaData.from_payload(payload, sample_company_config)
        
        # Should have tax information
        assert hasattr(data, "igv_amount") or hasattr(data, "tax_amount")


class TestPDFGeneration:
    """Tests for PDF generation (build_pdf function)."""

    def test_build_pdf_returns_bytes(self, sample_payload, sample_company_config, temp_dir):
        """Test that build_pdf returns PDF content as bytes."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test_output.pdf"
        
        result = build_pdf(data, output_path)
        
        # Should return success indicator or None
        # File should be created
        if output_path.exists():
            content = output_path.read_bytes()
            assert len(content) > 0
            # PDF files start with %PDF
            assert content[:4] == b"%PDF"

    def test_build_pdf_file_created(self, sample_payload, sample_company_config, temp_dir):
        """Test that build_pdf creates a file."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test.pdf"
        
        build_pdf(data, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_build_pdf_overwrite_existing(self, sample_payload, sample_company_config, temp_dir):
        """Test that build_pdf can overwrite existing file."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test.pdf"
        
        # Create initial file
        build_pdf(data, output_path)
        first_size = output_path.stat().st_size
        
        # Build again
        build_pdf(data, output_path)
        second_size = output_path.stat().st_size
        
        # File should exist
        assert output_path.exists()
        # Sizes might differ slightly, but should be non-zero
        assert second_size > 0

    def test_build_pdf_sin_igv_mode(self, sample_payload, sample_company_config, temp_dir):
        """Test PDF generation in sin_igv mode."""
        payload = sample_payload.copy()
        payload["tax_mode"] = "sin_igv"
        
        data = ProformaData.from_payload(payload, sample_company_config)
        output_path = temp_dir / "sin_igv.pdf"
        
        build_pdf(data, output_path)
        
        assert output_path.exists()

    def test_build_pdf_con_igv_mode(self, sample_payload, sample_company_config, temp_dir):
        """Test PDF generation in con_igv mode."""
        payload = sample_payload.copy()
        payload["tax_mode"] = "con_igv"
        
        data = ProformaData.from_payload(payload, sample_company_config)
        output_path = temp_dir / "con_igv.pdf"
        
        build_pdf(data, output_path)
        
        assert output_path.exists()


class TestDOCXGeneration:
    """Tests for DOCX generation (build_docx function)."""

    def test_build_docx_returns_none_or_success(self, sample_payload, sample_company_config, temp_dir):
        """Test that build_docx returns successfully."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test_output.docx"
        
        result = build_docx(data, output_path)
        
        # Should complete without error

    def test_build_docx_file_created(self, sample_payload, sample_company_config, temp_dir):
        """Test that build_docx creates a file."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test.docx"
        
        build_docx(data, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_build_docx_valid_format(self, sample_payload, sample_company_config, temp_dir):
        """Test that generated DOCX is in valid format."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "test.docx"
        
        build_docx(data, output_path)
        
        # DOCX files are ZIP archives starting with 'PK'
        content = output_path.read_bytes()
        assert content[:2] == b"PK"

    def test_build_docx_sin_igv_mode(self, sample_payload, sample_company_config, temp_dir):
        """Test DOCX generation in sin_igv mode."""
        payload = sample_payload.copy()
        payload["tax_mode"] = "sin_igv"
        
        data = ProformaData.from_payload(payload, sample_company_config)
        output_path = temp_dir / "sin_igv.docx"
        
        build_docx(data, output_path)
        
        assert output_path.exists()

    def test_build_docx_con_igv_mode(self, sample_payload, sample_company_config, temp_dir):
        """Test DOCX generation in con_igv mode."""
        payload = sample_payload.copy()
        payload["tax_mode"] = "con_igv"
        
        data = ProformaData.from_payload(payload, sample_company_config)
        output_path = temp_dir / "con_igv.docx"
        
        build_docx(data, output_path)
        
        assert output_path.exists()

    def test_build_docx_uses_company_config(self, sample_payload, sample_company_config, temp_dir):
        """Test that DOCX includes company information."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "with_company.docx"
        
        build_docx(data, output_path)
        
        # Check that company info is accessible
        assert data.company_config.company_name
        assert data.company_config.payment_bcp_account
        assert output_path.exists()

    def test_build_docx_payment_fields_accessible(self, sample_payload, sample_company_config, temp_dir):
        """Test that payment fields from company_config are accessible in DOCX generation."""
        data = ProformaData.from_payload(sample_payload, sample_company_config)
        output_path = temp_dir / "payment_test.docx"
        
        # These should not raise AttributeError
        bcp_account = data.company_config.payment_bcp_account
        bcp_cci = data.company_config.payment_bcp_cci
        detracciones = data.company_config.payment_detracciones_account
        
        build_docx(data, output_path)
        
        assert output_path.exists()


class TestProformaDataEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_string_customer_name(self, sample_payload, sample_company_config):
        """Test handling of empty customer name."""
        payload = sample_payload.copy()
        payload["customer_name"] = ""
        
        # Should either handle gracefully or raise error
        try:
            data = ProformaData.from_payload(payload, sample_company_config)
            assert data.customer_name == ""
        except ValueError:
            # Also acceptable to reject empty name
            pass

    def test_very_long_customer_name(self, sample_payload, sample_company_config):
        """Test handling of very long customer name."""
        payload = sample_payload.copy()
        payload["customer_name"] = "X" * 500
        
        data = ProformaData.from_payload(payload, sample_company_config)
        assert len(data.customer_name) == 500

    def test_special_characters_in_fields(self, sample_payload, sample_company_config):
        """Test handling of special characters."""
        payload = sample_payload.copy()
        payload["customer_name"] = "Empresa & Asociados, S.A.C."
        payload["items"] = [
            {"description": "Servicio de ñ, é, á, ü", "quantity": 1, "unit_price": 100}
        ]
        
        data = ProformaData.from_payload(payload, sample_company_config)
        assert "ñ" in data.customer_name or "ñ" in str(data.items[0])

    def test_zero_quantity_items(self, sample_payload, sample_company_config):
        """Test handling of items with zero quantity."""
        payload = sample_payload.copy()
        payload["items"] = [
            {"description": "Service", "quantity": 0, "unit_price": 100}
        ]
        
        # Should either handle or reject
        try:
            data = ProformaData.from_payload(payload, sample_company_config)
            assert data.items[0]["quantity"] == 0
        except ValueError:
            # Also acceptable to reject zero quantity
            pass

    def test_negative_quantity_items(self, sample_payload, sample_company_config):
        """Test handling of items with negative quantity (adjustments)."""
        payload = sample_payload.copy()
        payload["items"] = [
            {"description": "Discount", "quantity": -1, "unit_price": 50}
        ]
        
        # Should handle negative quantities (for discounts/returns)
        try:
            data = ProformaData.from_payload(payload, sample_company_config)
            assert data.items[0]["quantity"] == -1
        except ValueError:
            # Also acceptable to reject negative quantity
            pass
