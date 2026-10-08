from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class CompanyConfig:
    """Configuración de una empresa para generar proformas."""
    
    company_id: str
    company_name: str
    payment_bcp_account: str
    payment_bcp_cci: str
    payment_detracciones_account: str
    payment_bank_label: str
    offer_note_primary: str
    offer_note_secondary: str
    workshop_address: str
    fiscal_address: str
    header_image: str | None = None
    watermark_image: str | None = None
    
    @classmethod
    def from_json_file(cls, config_path: Path) -> CompanyConfig:
        """Cargar configuración desde archivo JSON."""
        if not config_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(
            company_id=data["company_id"],
            company_name=data["company_name"],
            payment_bcp_account=data["payment_bcp_account"],
            payment_bcp_cci=data["payment_bcp_cci"],
            payment_detracciones_account=data.get("payment_detracciones_account", ""),
            payment_bank_label=data["payment_bank_label"],
            offer_note_primary=data["offer_note_primary"],
            offer_note_secondary=data["offer_note_secondary"],
            workshop_address=data["workshop_address"],
            fiscal_address=data["fiscal_address"],
            header_image=data.get("header_image"),
            watermark_image=data.get("watermark_image"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convertir a diccionario (para JSON API response)."""
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "payment_bcp_account": self.payment_bcp_account,
            "payment_bcp_cci": self.payment_bcp_cci,
            "payment_detracciones_account": self.payment_detracciones_account,
            "payment_bank_label": self.payment_bank_label,
            "offer_note_primary": self.offer_note_primary,
            "offer_note_secondary": self.offer_note_secondary,
            "workshop_address": self.workshop_address,
            "fiscal_address": self.fiscal_address,
            "header_image": self.header_image,
            "watermark_image": self.watermark_image,
        }
