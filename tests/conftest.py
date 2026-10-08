"""Pytest fixtures and configuration for Proformas-Empresas tests."""

import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_payload():
    """Provide a sample proforma payload for testing."""
    return {
        "customer_name": "Cliente Prueba",
        "phone": "987654321",
        "ruc": "10123456789",
        "issue_date": "2026-10-08",
        "document_kind": "proforma",
        "tax_mode": "sin_igv",
        "header_kind": "generales",
        "watermark_kind": "proforma",
        "summary": "Servicio de prueba",
        "items": [
            {"description": "Servicio 1", "amount": "1000.00"},
            {"description": "Servicio 2", "amount": "500.00"}
        ],
        "advance_payments": [
            {"payment_date": "2026-10-15", "amount": "750.00"}
        ],
        "company_id": "jc-services",
        "show_payment_details": True
    }


@pytest.fixture
def sample_company_config():
    """Provide a sample company configuration."""
    return {
        "company_id": "jc-services",
        "company_name": "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
        "payment_bcp_account": "0011-0202-0100061544",
        "payment_bcp_cci": "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
        "payment_detracciones_account": "00-123-456789",
        "payment_bank_label": "Cuenta en Soles BBVA",
        "offer_note_primary": "Validez de la oferta: 10 dias",
        "offer_note_secondary": "Montos incluye instalacion",
        "workshop_address": "Planta de Trabajo: Jr. Tarapaca S/N, Pilcomayo",
        "fiscal_address": "Domicilio: Jr. Tarapaca S/N, Pilcomayo",
        "header_image": "companies/jc-services/header_pintura.png",
        "watermark_image": "companies/jc-services/watermark_general.png"
    }


@pytest.fixture
def mock_config_dir(temp_dir):
    """Create a mock configs/companies directory with sample configs."""
    config_dir = temp_dir / "companies"
    config_dir.mkdir()
    
    # Create jc-services.json
    jc_services_config = {
        "company_id": "jc-services",
        "company_name": "J&C SERVICES",
        "payment_bcp_account": "0011-0202-0100061544",
        "payment_bcp_cci": "MULTISERVICIOS J&C",
        "payment_detracciones_account": "",
        "payment_bank_label": "Cuenta BCP Soles",
        "offer_note_primary": "Validez: 10 días",
        "offer_note_secondary": "Incluye instalación",
        "workshop_address": "Jr. Taller 123",
        "fiscal_address": "Jr. Fiscal 456",
        "header_image": "companies/jc-services/header.png",
        "watermark_image": "companies/jc-services/watermark.png"
    }
    
    with open(config_dir / "jc-services.json", "w") as f:
        json.dump(jc_services_config, f)
    
    return config_dir
