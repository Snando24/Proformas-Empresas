from proforma_app.document_engine import ProformaData, build_pdf
payload = {
    "customer_name": "Prueba IGV",
    "phone": "",
    "ruc": "",
    "issue_date": "2026-07-15",
    "document_kind": "proforma",
    "tax_mode": "con_igv",
    "header_kind": "generales",
    "watermark_kind": "proforma",
    "summary": "Prueba de etiqueta de total.",
    "items": [{"description": "Servicio", "amount": "100.00"}],
    "advance_payments": []
}
obj = ProformaData.from_payload(payload)
print(build_pdf(obj))
