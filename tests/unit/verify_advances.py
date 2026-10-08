from proforma_app.document_engine import ProformaData, build_pdf, build_docx
payload = {
    "customer_name": "",
    "phone": "",
    "ruc": "",
    "issue_date": "",
    "document_kind": "proforma",
    "header_kind": "pintura",
    "watermark_kind": "proforma",
    "summary": "",
    "items": [
        {"description": "Trabajo parcial", "amount": "1200.00"},
        {"description": "", "amount": ""},
    ],
    "advance_payments": [
        {"payment_date": "2026-07-09", "amount": "500.00"},
        {"payment_date": "2026-07-11", "amount": "250.00"},
        {"payment_date": "", "amount": "100.00"},
    ],
}
obj = ProformaData.from_payload(payload)
pdf = build_pdf(obj)
docx = build_docx(obj)
print(pdf)
print(docx)
