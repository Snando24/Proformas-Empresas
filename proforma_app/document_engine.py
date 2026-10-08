from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF_DIR = ROOT_DIR / "output" / "pdf"
OUTPUT_DOCX_DIR = ROOT_DIR / "output" / "docx"
HEADER_IMAGES = {
    "pintura": ROOT_DIR / "static" / "assets" / "header_corporate_pintura_v2.png",
    "generales": ROOT_DIR / "static" / "assets" / "header_corporate_generales_v2.png",
}
WATERMARK_IMAGES = {
    "proforma": ROOT_DIR / "static" / "assets" / "watermark_corporate.png",
    "pintura": ROOT_DIR / "static" / "assets" / "watermark_corporate_paint.png",
}
WATERMARK_LAYOUTS = {
    "proforma": {"width": 250, "bottom": 150, "opacity": 0.065},
    "pintura": {"width": 250, "bottom": 150, "opacity": 0.065},
}

LETTER_WIDTH, LETTER_HEIGHT = letter
MONEY_QUANT = Decimal("0.01")

DOCX_STYLE_TOKENS = {
    "preset": "standard_business_brief + branded_header_override",
    "page": {
        "top_margin": Inches(1),
        "right_margin": Inches(1),
        "bottom_margin": Inches(1),
        "left_margin": Inches(1),
        "header_distance": Inches(0.492),
        "footer_distance": Inches(0.492),
    },
    "body_font": ("Calibri", Pt(11)),
    "heading_font": ("Calibri", Pt(16)),
    "table_width_inches": 6.5,
}

DEFAULT_PAYMENT_BCP_ACCOUNT = "0011-0202-0100061544"
DEFAULT_PAYMENT_BCP_CCI = "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L."
DEFAULT_PAYMENT_DETRACCIONES_ACCOUNT = ""
PAYMENT_BANK_LABEL = "Cuenta en Soles BBVA"
OFFER_NOTE_PRIMARY = "Validez de la oferta: 10 dias"
OFFER_NOTE_SECONDARY = "Montos incluye instalacion"
WORKSHOP_ADDRESS = "Planta de Trabajo: Jr. Tarapaca S/N, Pilcomayo - Huancayo"
FISCAL_ADDRESS = "Domicilio: Jr. Tarapaca S/N, Pilcomayo - Huancayo"


def normalize_money(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Monto invalido: {value}") from error


def format_money(value: Decimal) -> str:
    return f"{value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP):.2f}"


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-") or "cliente"


def parse_optional_date(raw_value: str | None) -> date | None:
    if not raw_value:
        return None
    return datetime.strptime(raw_value, "%Y-%m-%d").date()


def format_optional_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def normalize_tax_mode(value: str | None) -> str:
    return "con_igv" if str(value or "").strip().lower() == "con_igv" else "sin_igv"


def normalize_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "on", "yes", "si"}


def get_total_label(tax_mode: str) -> str:
    return "TOTAL:" if normalize_tax_mode(tax_mode) == "con_igv" else "TOTAL (SIN IGV):"


def get_document_kind_label(document_kind: str) -> str:
    return "Contrato" if document_kind == "contrato" else "Proforma"


def get_document_title(document_kind: str) -> str:
    return "CONTRATO DE SERVICIO" if document_kind == "contrato" else "PROFORMA DE SERVICIO"


def get_document_number_label(document_kind: str) -> str:
    return "Nro. Contrato" if document_kind == "contrato" else "Nro. Cotizacion"


def build_document_code(issue_date: date | None, document_kind: str) -> str:
    base_date = issue_date or date.today()
    compact_date = base_date.strftime("%y%m%d")
    prefix = "CTR" if document_kind == "contrato" else "CTZ"
    return f"{prefix}-{compact_date}"


def format_long_date(value: date | None) -> str:
    if not value:
        return ""

    weekdays = [
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    ]
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    weekday = weekdays[value.weekday()]
    month = months[value.month - 1]
    return f"{weekday.title()}, {value.day} de {month} de {value.year}"


def get_description_heading(summary: str, document_kind: str) -> str:
    base = str(summary or "").strip()
    return (base or get_document_title(document_kind)).upper()


def get_recipient_detail_line(ruc: str, phone: str) -> str:
    parts: list[str] = []
    if ruc:
        parts.append(f"RUC: {ruc}")
    if phone:
        parts.append(f"Telefono: {phone}")
    return " | ".join(parts)


def compute_tax_breakdown(total: Decimal, tax_mode: str) -> dict[str, Any]:
    normalized_total = total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    if normalize_tax_mode(tax_mode) == "con_igv":
        taxable = (normalized_total / Decimal("1.18")).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        igv = (normalized_total - taxable).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
        return {
            "taxable_label": "VALOR VENTA",
            "taxable_amount": taxable,
            "tax_label": "IGV",
            "tax_amount": igv,
            "total_label": "TOTAL",
            "total_note": "MONTO EXPRESADO EN SOLES. INCLUYE IGV.",
        }

    return {
        "taxable_label": "SUBTOTAL",
        "taxable_amount": normalized_total,
        "tax_label": "IGV",
        "tax_amount": Decimal("0.00"),
        "total_label": "TOTAL",
        "total_note": "MONTO EXPRESADO EN SOLES. SIN IGV.",
    }


@dataclass
class LineItem:
    description: str
    amount: Decimal
    show_amount: bool


@dataclass
class AdvancePayment:
    payment_date: date | None
    amount: Decimal
    show_amount: bool

    @property
    def display_line(self) -> str:
        date_label = format_optional_date(self.payment_date)
        amount_label = format_money(self.amount) if self.show_amount else ""

        if date_label and amount_label:
            return f"A cuenta {date_label}: {amount_label}"
        if date_label:
            return f"A cuenta {date_label}"
        if amount_label:
            return f"A cuenta {amount_label}"
        return ""


@dataclass
class ProformaData:
    customer_name: str
    phone: str
    ruc: str
    issue_date: date | None
    document_kind: str
    tax_mode: str
    header_kind: str
    watermark_kind: str
    summary: str
    items: list[LineItem]
    advance_payments: list[AdvancePayment]
    show_payment_details: bool
    payment_bcp_account: str
    payment_bcp_cci: str
    payment_detracciones_account: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ProformaData":
        items: list[LineItem] = []
        for row in payload.get("items", []):
            description = str(row.get("description", "")).strip()
            amount_raw = str(row.get("amount", "")).strip()
            show_amount = amount_raw != ""
            if not description and not show_amount:
                continue
            items.append(
                LineItem(
                    description=description,
                    amount=normalize_money(amount_raw),
                    show_amount=show_amount,
                )
            )

        raw_advance_payments = payload.get("advance_payments")
        if raw_advance_payments is None and payload.get("advance_payment") not in (None, ""):
            raw_advance_payments = [
                {
                    "payment_date": payload.get("issue_date", ""),
                    "amount": payload.get("advance_payment", ""),
                }
            ]

        advance_payments: list[AdvancePayment] = []
        for row in raw_advance_payments or []:
            payment_date_raw = str(row.get("payment_date", "")).strip()
            amount_raw = str(row.get("amount", "")).strip()
            show_amount = amount_raw != ""
            if not payment_date_raw and not show_amount:
                continue
            advance_payments.append(
                AdvancePayment(
                    payment_date=parse_optional_date(payment_date_raw),
                    amount=normalize_money(amount_raw),
                    show_amount=show_amount,
                )
            )

        document_kind = str(payload.get("document_kind", "proforma")).strip().lower()
        tax_mode = normalize_tax_mode(payload.get("tax_mode"))
        header_kind = str(payload.get("header_kind", "generales")).strip().lower()
        watermark_kind = str(payload.get("watermark_kind", "proforma")).strip().lower()

        if document_kind not in {"proforma", "contrato"}:
            raise ValueError("El tipo de documento debe ser proforma o contrato.")
        if header_kind not in HEADER_IMAGES:
            raise ValueError("El encabezado debe ser pintura o generales.")
        if watermark_kind not in WATERMARK_IMAGES:
            raise ValueError("La marca de agua debe ser proforma o pintura.")

        return cls(
            customer_name=str(payload.get("customer_name", "")).strip(),
            phone=str(payload.get("phone", "")).strip(),
            ruc=str(payload.get("ruc", "")).strip(),
            issue_date=parse_optional_date(payload.get("issue_date")),
            document_kind=document_kind,
            tax_mode=tax_mode,
            header_kind=header_kind,
            watermark_kind=watermark_kind,
            summary=str(payload.get("summary", "")).strip(),
            items=items,
            advance_payments=advance_payments,
            show_payment_details=normalize_bool(payload.get("show_payment_details")),
            payment_bcp_account=str(
                payload.get("payment_bcp_account", DEFAULT_PAYMENT_BCP_ACCOUNT)
            ).strip(),
            payment_bcp_cci=str(payload.get("payment_bcp_cci", DEFAULT_PAYMENT_BCP_CCI)).strip(),
            payment_detracciones_account=str(
                payload.get("payment_detracciones_account", DEFAULT_PAYMENT_DETRACCIONES_ACCOUNT)
            ).strip(),
        )

    @property
    def total(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0.00"))

    @property
    def filename_stem(self) -> str:
        base_date = self.issue_date.isoformat() if self.issue_date else date.today().isoformat()
        label = "proforma" if self.document_kind == "proforma" else "contrato"
        return f"{base_date}-{label}-{slugify(self.customer_name)}"

    @property
    def display_date(self) -> str:
        return format_optional_date(self.issue_date)

    @property
    def payment_rows(self) -> list[tuple[str, str]]:
        return [
            ("Banco BCP", self.payment_bcp_account),
            ("CCI", self.payment_bcp_cci),
            ("Banco de la Nación", self.payment_detracciones_account),
        ]


def ensure_output_dirs() -> None:
    OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DOCX_DIR.mkdir(parents=True, exist_ok=True)


def ensure_reference_template() -> None:
    return None


def ensure_header_image() -> None:
    for header_path in HEADER_IMAGES.values():
        if not header_path.exists():
            raise FileNotFoundError(f"No se encontro el encabezado derivado: {header_path.name}")


def ensure_watermark_image() -> None:
    for watermark_path in WATERMARK_IMAGES.values():
        if not watermark_path.exists():
            raise FileNotFoundError(f"No se encontro la marca de agua: {watermark_path.name}")


def get_watermark_image_path(watermark_kind: str) -> Path:
    return WATERMARK_IMAGES.get(watermark_kind, WATERMARK_IMAGES["proforma"])


def get_header_image_path(header_kind: str) -> Path:
    return HEADER_IMAGES.get(header_kind, HEADER_IMAGES["generales"])


def get_watermark_layout(watermark_kind: str) -> dict[str, float]:
    return WATERMARK_LAYOUTS.get(watermark_kind, WATERMARK_LAYOUTS["proforma"])


def draw_pdf_watermark(pdf: canvas.Canvas, watermark_reader: ImageReader, watermark_kind: str) -> None:
    watermark_width, watermark_height = watermark_reader.getSize()
    layout = get_watermark_layout(watermark_kind)
    rendered_width = layout["width"]
    rendered_height = rendered_width * (watermark_height / watermark_width)
    watermark_x = (LETTER_WIDTH - rendered_width) / 2
    watermark_y = layout["bottom"]

    pdf.saveState()
    if hasattr(pdf, "setFillAlpha"):
        pdf.setFillAlpha(layout["opacity"])
    pdf.drawImage(
        watermark_reader,
        watermark_x,
        watermark_y,
        width=rendered_width,
        height=rendered_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.restoreState()


def draw_pdf_payment_footer(pdf: canvas.Canvas, data: ProformaData) -> None:
    payment_x = 52
    payment_y = 42
    payment_width = 508
    payment_height = 70
    title_height = 20

    pdf.saveState()
    pdf.setStrokeColorRGB(0.22, 0.17, 0.12)
    pdf.setFillColorRGB(1.0, 0.973, 0.925)
    pdf.roundRect(payment_x, payment_y, payment_width, payment_height, 10, stroke=1, fill=1)
    pdf.setFillColorRGB(0.949, 0.749, 0.31)
    pdf.roundRect(
        payment_x,
        payment_y + payment_height - title_height,
        payment_width,
        title_height,
        10,
        stroke=0,
        fill=1,
    )
    pdf.rect(payment_x, payment_y + payment_height - title_height, payment_width, 10, stroke=0, fill=1)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColorRGB(0.16, 0.11, 0.07)
    pdf.drawString(payment_x + 14, payment_y + payment_height - 14, "DATOS PARA EL PAGO")

    divider_x = payment_x + (payment_width / 2)
    content_top = payment_y + payment_height - title_height - 14
    pdf.setStrokeColorRGB(0.79, 0.70, 0.55)
    pdf.line(divider_x, payment_y + 8, divider_x, payment_y + payment_height - title_height - 6)

    pdf.setFont("Helvetica-Bold", 8.8)
    pdf.setFillColorRGB(0.18, 0.14, 0.10)
    pdf.drawString(payment_x + 14, content_top, "Banco BCP")
    pdf.drawString(divider_x + 12, content_top, "Banco de la Nacion")

    pdf.setFont("Helvetica-Bold", 8.2)
    pdf.setFillColorRGB(0.32, 0.25, 0.17)
    pdf.drawString(payment_x + 14, content_top - 14, "Cuenta:")
    pdf.drawString(payment_x + 14, content_top - 27, "CCI:")
    pdf.drawString(divider_x + 12, content_top - 14, "Cuenta de Detracciones")

    pdf.setFillColorRGB(0.09, 0.07, 0.06)
    pdf.drawRightString(divider_x - 14, content_top - 14, data.payment_bcp_account or "-")
    pdf.drawRightString(divider_x - 14, content_top - 27, data.payment_bcp_cci or "-")
    pdf.drawRightString(payment_x + payment_width - 14, content_top - 27, data.payment_detracciones_account or "-")
    pdf.restoreState()


def set_run_font(run, font_name: str, font_size: Pt, bold: bool = False) -> None:
    run.font.name = font_name
    run.font.size = font_size
    run.font.bold = bold
    r_fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), font_name)
    r_fonts.set(qn("w:hAnsi"), font_name)


def set_cell_borders(cell, **borders: dict[str, str]) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.first_child_found_in("w:tcBorders")
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)

    for edge, edge_data in borders.items():
        tag = f"w:{edge}"
        element = tc_borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tc_borders.append(element)
        for key, value in edge_data.items():
            element.set(qn(f"w:{key}"), value)


def set_cell_width(cell, width_inches: float) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_width = tc_pr.first_child_found_in("w:tcW")
    if tc_width is None:
        tc_width = OxmlElement("w:tcW")
        tc_pr.append(tc_width)
    width_value = int(width_inches * 1440)
    tc_width.set(qn("w:w"), str(width_value))
    tc_width.set(qn("w:type"), "dxa")
    cell.width = Inches(width_inches)


def build_pdf(data: ProformaData) -> Path:
    ensure_output_dirs()
    ensure_reference_template()
    ensure_header_image()
    ensure_watermark_image()

    output_path = OUTPUT_PDF_DIR / f"{data.filename_stem}.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    pdf.setTitle(f"{data.document_kind.title()} - {data.customer_name or 'Cliente'}")

    header_reader = ImageReader(str(get_header_image_path(data.header_kind)))
    watermark_reader = ImageReader(str(get_watermark_image_path(data.watermark_kind)))
    header_width, header_height = header_reader.getSize()
    rendered_header_height = min(140, LETTER_WIDTH * (header_height / header_width))
    pdf.drawImage(
        header_reader,
        0,
        LETTER_HEIGHT - rendered_header_height,
        width=LETTER_WIDTH,
        height=rendered_header_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)

    left_box_x = 52
    left_box_y = 402
    left_box_width = 300
    left_box_height = 126
    pdf.rect(left_box_x, left_box_y, left_box_width, left_box_height, stroke=1, fill=0)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(60, 502, "Señor(a):")
    pdf.setFont("Helvetica", 18)
    pdf.drawString(145, 502, data.customer_name)

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(60, 470, "Teléfono:")
    pdf.setFont("Helvetica", 15)
    pdf.drawString(145, 470, data.phone)

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(60, 438, "RUC:")
    pdf.setFont("Helvetica", 15)
    pdf.drawString(110, 438, data.ruc)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(60, 406, "Fecha:")
    pdf.setFont("Helvetica", 18)
    pdf.drawString(130, 406, data.display_date)

    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(385, 500, "PROFORMA:")
    pdf.drawString(385, 468, "CONTRATO:")

    for index, label in enumerate(("proforma", "contrato")):
        box_y = 495 - (index * 32)
        pdf.roundRect(507, box_y, 24, 24, 5, stroke=1, fill=0)
        if label == data.document_kind:
            pdf.setLineWidth(2.8)
            pdf.line(511, box_y + 4, 527, box_y + 20)
            pdf.line(511, box_y + 20, 527, box_y + 4)
            pdf.setLineWidth(1)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(82, 356, "DESCRIPCION:")
    pdf.setFont("Helvetica", 12)
    summary_lines = simpleSplit(data.summary, "Helvetica", 12, 420) if data.summary else []
    summary_y = 356
    for line in summary_lines:
        pdf.drawString(180, summary_y, line)
        summary_y -= 15

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(275, 292, "DESCRIPCION")
    pdf.drawCentredString(500, 292, "TOTAL")

    current_y = 254
    item_line_height = 14 if data.show_payment_details else 18
    item_gap = 5 if data.show_payment_details else 10
    bottom_reserve = 126 if data.show_payment_details else 150
    pdf.setFont("Helvetica", 12)
    for item in data.items:
        wrapped = simpleSplit(item.description, "Helvetica", 12, 320) if item.description else [""]
        if current_y < bottom_reserve:
            pdf.showPage()
            draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)
            pdf.setFont("Helvetica-Bold", 18)
            pdf.drawCentredString(275, 742, "DESCRIPCION")
            pdf.drawCentredString(500, 742, "TOTAL")
            pdf.setFont("Helvetica", 12)
            current_y = 704

        for line_index, line in enumerate(wrapped):
            pdf.drawString(90, current_y, line or " ")
            if line_index == 0 and item.show_amount:
                pdf.drawRightString(545, current_y, format_money(item.amount))
            current_y -= item_line_height
        current_y -= item_gap

    advance_lines = [entry.display_line for entry in data.advance_payments if entry.display_line]
    if advance_lines:
        if current_y > (188 if data.show_payment_details else 180):
            current_y = 160 if data.show_payment_details else 150
        for line in advance_lines:
            if current_y < (118 if data.show_payment_details else bottom_reserve):
                pdf.showPage()
                draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)
                current_y = 704
            pdf.drawString(90, current_y, line)
            current_y -= 18 if data.show_payment_details else 24

    if data.show_payment_details:
        total_y = 124 if current_y > 138 else max(current_y - 4, 108)
        if total_y < 108:
            pdf.showPage()
            draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)
            total_y = 124
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(365, total_y, get_total_label(data.tax_mode))
        pdf.drawRightString(545, total_y, format_money(data.total))
        draw_pdf_payment_footer(pdf, data)
    else:
        total_y = 98 if current_y > 120 else max(current_y - 20, 60)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(365, total_y, get_total_label(data.tax_mode))
        pdf.drawRightString(545, total_y, format_money(data.total))

    pdf.save()
    return output_path


def build_pdf(data: ProformaData) -> Path:
    ensure_output_dirs()
    ensure_reference_template()
    ensure_header_image()
    ensure_watermark_image()

    output_path = OUTPUT_PDF_DIR / f"{data.filename_stem}.pdf"
    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    pdf.setTitle(f"{data.document_kind.title()} - {data.customer_name or 'Cliente'}")

    header_reader = ImageReader(str(get_header_image_path(data.header_kind)))
    watermark_reader = ImageReader(str(get_watermark_image_path(data.watermark_kind)))
    header_width, header_height = header_reader.getSize()
    rendered_header_height = min(210, LETTER_WIDTH * (header_height / header_width))
    pdf.drawImage(
        header_reader,
        0,
        LETTER_HEIGHT - rendered_header_height,
        width=LETTER_WIDTH,
        height=rendered_header_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)

    tax_breakdown = compute_tax_breakdown(data.total, data.tax_mode)
    columns = [
        {"key": "item_number", "label_lines": ["ITEM"], "width": 30, "align": "center"},
        {"key": "description", "label_lines": ["DESCRIPCIÓN"], "width": 260, "align": "left"},
        {"key": "quantity", "label_lines": ["CANT."], "width": 40, "align": "center"},
        {"key": "unit_price", "label_lines": ["PRECIO", "UNIT"], "width": 72, "align": "right"},
        {"key": "discount", "label_lines": ["Desc."], "width": 62, "align": "center"},
        {"key": "total", "label_lines": ["TOTAL"], "width": 80, "align": "right"},
    ]
    table_x = 34
    table_width = sum(column["width"] for column in columns)
    footer_reserve = 182 if data.show_payment_details else 168
    page_break_limit = LETTER_HEIGHT - footer_reserve

    def top_to_y(top_value: float) -> float:
        return LETTER_HEIGHT - top_value

    def draw_round_rect_top(x: float, top: float, width: float, height: float, radius: float = 10) -> None:
        pdf.roundRect(x, LETTER_HEIGHT - top - height, width, height, radius, stroke=1, fill=0)

    def draw_table_header(top: float) -> None:
        cursor_x = table_x
        header_y = LETTER_HEIGHT - top - 34
        pdf.setStrokeColorRGB(122 / 255, 152 / 255, 191 / 255)
        pdf.setFont("Helvetica-Bold", 9.5)
        for column in columns:
            pdf.setFillColorRGB(74 / 255, 99 / 255, 133 / 255)
            pdf.rect(cursor_x, header_y, column["width"], 34, stroke=1, fill=1)
            pdf.setFillColorRGB(1, 1, 1)
            label_lines = column["label_lines"]
            baseline_y = header_y + (13 if len(label_lines) > 1 else 20)
            for line_index, line in enumerate(label_lines):
                pdf.drawCentredString(cursor_x + (column["width"] / 2), baseline_y + (line_index * 9), line)
            cursor_x += column["width"]
        pdf.setFillColorRGB(18 / 255, 48 / 255, 86 / 255)

    def draw_table_row(row: dict[str, str], top: float) -> float:
        line_sets: list[list[str]] = []
        row_height = 28
        for column in columns:
            raw_value = row[column["key"]]
            lines = simpleSplit(raw_value, "Helvetica", 8.7, max(column["width"] - 8, 1)) if raw_value else [""]
            line_sets.append(lines)
            row_height = max(row_height, (len(lines) * 11) + 10)

        row_y = LETTER_HEIGHT - top - row_height
        cursor_x = table_x
        pdf.setStrokeColorRGB(122 / 255, 152 / 255, 191 / 255)
        pdf.setFont("Helvetica", 8.7)
        pdf.setFillColorRGB(18 / 255, 48 / 255, 86 / 255)
        for column, lines in zip(columns, line_sets):
            pdf.rect(cursor_x, row_y, column["width"], row_height, stroke=1, fill=0)
            text_y = row_y + row_height - 14
            for line in lines:
                if column["align"] == "right":
                    pdf.drawRightString(cursor_x + column["width"] - 6, text_y, line)
                elif column["align"] == "center":
                    pdf.drawCentredString(cursor_x + (column["width"] / 2), text_y, line)
                else:
                    pdf.drawString(cursor_x + 5, text_y, line)
                text_y -= 10
            cursor_x += column["width"]
        return row_height

    table_rows: list[dict[str, str]] = []
    for index, item in enumerate(data.items, start=1):
        table_rows.append(
            {
                "item_number": str(index),
                "description": item.description or "",
                "quantity": "1" if item.description or item.show_amount else "",
                "unit_price": format_money(item.amount) if item.show_amount else "",
                "discount": "0.00%" if item.description or item.show_amount else "",
                "total": format_money(item.amount) if item.show_amount else "",
            }
        )
    while len(table_rows) < (4 if not data.items else len(table_rows)):
        table_rows.append(
            {
                "item_number": "",
                "description": "",
                "quantity": "",
                "unit_price": "",
                "discount": "",
                "total": "",
            }
        )

    def draw_page_footer() -> None:
        notes_y = 92
        notes_height = 82
        notes_width = 332
        totals_x = 390
        totals_width = 188
        totals_value_width = 78
        row_height = 24

        pdf.setStrokeColorRGB(207 / 255, 216 / 255, 228 / 255)
        pdf.roundRect(34, notes_y, notes_width, notes_height, 10, stroke=1, fill=0)
        pdf.setFillColorRGB(127 / 255, 144 / 255, 166 / 255)
        pdf.setFont("Helvetica-Bold", 8.2)
        pdf.drawString(46, notes_y + notes_height - 14, "OBSERVACIONES")
        pdf.setFont("Helvetica", 8.8)
        pdf.setFillColorRGB(39 / 255, 67 / 255, 99 / 255)
        pdf.drawString(46, notes_y + notes_height - 34, OFFER_NOTE_PRIMARY)
        pdf.drawString(46, notes_y + notes_height - 49, OFFER_NOTE_SECONDARY)

        pdf.setStrokeColorRGB(90 / 255, 121 / 255, 164 / 255)
        pdf.rect(totals_x, notes_y, totals_width, row_height * 3, stroke=1, fill=0)
        total_rows = [
            (tax_breakdown["taxable_label"], format_money(tax_breakdown["taxable_amount"])),
            (tax_breakdown["tax_label"], format_money(tax_breakdown["tax_amount"])),
            (tax_breakdown["total_label"], format_money(data.total)),
        ]
        for index, (label, value) in enumerate(total_rows):
            row_y = notes_y + (row_height * (2 - index))
            if index > 0:
                pdf.line(totals_x, row_y + row_height, totals_x + totals_width, row_y + row_height)
            pdf.line(totals_x + totals_width - totals_value_width, row_y, totals_x + totals_width - totals_value_width, row_y + row_height)
            pdf.setFont("Helvetica-Bold", 10 if index == 2 else 9)
            pdf.setFillColorRGB(18 / 255, 48 / 255, 86 / 255)
            pdf.drawString(totals_x + 10, row_y + 9, label.upper())
            pdf.drawRightString(totals_x + totals_width - 10, row_y + 9, value)

        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawRightString(totals_x + totals_width, notes_y - 8, tax_breakdown["total_note"])

        if data.show_payment_details:
            payment_line = f"{PAYMENT_BANK_LABEL}: {data.payment_bcp_account or '-'} | {data.payment_bcp_cci or '-'}"
            payment_lines = simpleSplit(payment_line, "Helvetica", 6.8, LETTER_WIDTH - 68)
            payment_y = 50 + ((len(payment_lines) - 1) * 7)
            pdf.setFont("Helvetica", 6.8)
            pdf.setFillColorRGB(17 / 255, 17 / 255, 17 / 255)
            for line in payment_lines:
                pdf.drawCentredString(LETTER_WIDTH / 2, payment_y, line)
                payment_y -= 7

        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.setFillColorRGB(47 / 255, 70 / 255, 103 / 255)
        pdf.drawCentredString(LETTER_WIDTH / 2, 20, WORKSHOP_ADDRESS)
        pdf.drawCentredString(LETTER_WIDTH / 2, 8, FISCAL_ADDRESS)

    top_cursor = rendered_header_height + 18
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.setFillColorRGB(18 / 255, 48 / 255, 86 / 255)
    pdf.setFont("Helvetica-Bold", 12.4)
    pdf.drawCentredString(LETTER_WIDTH / 2, top_to_y(top_cursor), get_description_heading(data.summary, data.document_kind))

    top_cursor += 28
    pdf.setFont("Helvetica", 10.3)
    pdf.drawString(18, top_to_y(top_cursor), f"{get_document_number_label(data.document_kind).upper()} {build_document_code(data.issue_date, data.document_kind)}")
    pdf.drawRightString(594, top_to_y(top_cursor), format_long_date(data.issue_date))

    top_cursor += 26
    pdf.drawString(18, top_to_y(top_cursor), "Sres.")
    top_cursor += 16
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(18, top_to_y(top_cursor), data.customer_name or "-")

    recipient_detail_line = get_recipient_detail_line(data.ruc, data.phone)
    if recipient_detail_line:
        top_cursor += 16
        pdf.drawString(18, top_to_y(top_cursor), recipient_detail_line.upper())

    top_cursor += 20
    draw_table_header(top_cursor)
    top_cursor += 34

    for row in table_rows:
        line_counts = []
        for column in columns:
            raw_value = row[column["key"]]
            lines = simpleSplit(raw_value, "Helvetica", 8.7, max(column["width"] - 8, 1)) if raw_value else [""]
            line_counts.append(len(lines))
        row_height = max(28, (max(line_counts) * 11) + 10)

        if top_cursor + row_height > page_break_limit:
            pdf.showPage()
            draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)
            pdf.setFillColorRGB(18 / 255, 48 / 255, 86 / 255)
            pdf.setFont("Helvetica-Bold", 12.4)
            pdf.drawCentredString(LETTER_WIDTH / 2, LETTER_HEIGHT - 46, get_description_heading(data.summary, data.document_kind))
            top_cursor = 64
            draw_table_header(top_cursor)
            top_cursor += 34

        top_cursor += draw_table_row(row, top_cursor)

    advance_lines = [entry.display_line for entry in data.advance_payments if entry.display_line]
    if advance_lines:
        top_cursor += 14
        pdf.setFillColorRGB(127 / 255, 144 / 255, 166 / 255)
        pdf.setFont("Helvetica-Bold", 8.2)
        pdf.drawString(34, top_to_y(top_cursor), "ADELANTOS REGISTRADOS")
        top_cursor += 14
        pdf.setFillColorRGB(39 / 255, 67 / 255, 99 / 255)
        pdf.setFont("Helvetica", 8.8)
        for line in advance_lines:
            if top_cursor + 12 > page_break_limit:
                pdf.showPage()
                draw_pdf_watermark(pdf, watermark_reader, data.watermark_kind)
                top_cursor = 64
            pdf.drawString(40, top_to_y(top_cursor), line)
            top_cursor += 12

    draw_page_footer()

    pdf.save()
    return output_path


def build_docx(data: ProformaData) -> Path:
    ensure_output_dirs()
    ensure_reference_template()
    ensure_header_image()

    output_path = OUTPUT_DOCX_DIR / f"{data.filename_stem}.docx"
    doc = Document()

    section = doc.sections[0]
    section.start_type = WD_SECTION.NEW_PAGE
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = DOCX_STYLE_TOKENS["page"]["top_margin"]
    section.right_margin = DOCX_STYLE_TOKENS["page"]["right_margin"]
    section.bottom_margin = DOCX_STYLE_TOKENS["page"]["bottom_margin"]
    section.left_margin = DOCX_STYLE_TOKENS["page"]["left_margin"]
    section.header_distance = DOCX_STYLE_TOKENS["page"]["header_distance"]
    section.footer_distance = DOCX_STYLE_TOKENS["page"]["footer_distance"]

    normal_style = doc.styles["Normal"]
    normal_style.font.name = DOCX_STYLE_TOKENS["body_font"][0]
    normal_style.font.size = DOCX_STYLE_TOKENS["body_font"][1]

    image_paragraph = doc.add_paragraph()
    image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    image_run = image_paragraph.add_run()
    image_run.add_picture(str(get_header_image_path(data.header_kind)), width=Inches(DOCX_STYLE_TOKENS["table_width_inches"]))

    heading_paragraph = doc.add_paragraph()
    heading_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading_run = heading_paragraph.add_run(get_description_heading(data.summary, data.document_kind))
    set_run_font(heading_run, "Calibri", Pt(16), bold=True)

    info_table = doc.add_table(rows=1, cols=2)
    info_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    info_table.autofit = False

    left_cell = info_table.rows[0].cells[0]
    right_cell = info_table.rows[0].cells[1]
    set_cell_width(left_cell, 4.35)
    set_cell_width(right_cell, 2.15)

    set_cell_borders(
        left_cell,
        top={"val": "single", "sz": "12", "color": "000000"},
        bottom={"val": "single", "sz": "12", "color": "000000"},
        left={"val": "single", "sz": "12", "color": "000000"},
        right={"val": "single", "sz": "12", "color": "000000"},
    )
    set_cell_borders(
        right_cell,
        top={"val": "nil"},
        bottom={"val": "nil"},
        left={"val": "nil"},
        right={"val": "nil"},
    )

    left_cell.text = ""
    right_cell.text = ""

    client_lines = [
        ("Señor(a): ", data.customer_name),
        ("Teléfono: ", data.phone),
        ("RUC: ", data.ruc),
        ("Fecha: ", data.display_date),
    ]

    for index, (label, value) in enumerate(client_lines):
        paragraph = left_cell.paragraphs[0] if index == 0 else left_cell.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(6)
        label_run = paragraph.add_run(label)
        set_run_font(label_run, "Calibri", Pt(16), bold=True)
        value_run = paragraph.add_run(value or " ")
        set_run_font(value_run, "Calibri", Pt(16), bold=False)

    right_lines = [
        ("PROFORMA:", "[X]" if data.document_kind == "proforma" else "[ ]"),
        ("CONTRATO:", "[X]" if data.document_kind == "contrato" else "[ ]"),
    ]
    for index, (label, checkbox) in enumerate(right_lines):
        paragraph = right_cell.paragraphs[0] if index == 0 else right_cell.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(10)
        label_run = paragraph.add_run(label + " ")
        set_run_font(label_run, "Calibri", Pt(15), bold=True)
        value_run = paragraph.add_run(checkbox)
        set_run_font(value_run, "Calibri", Pt(15), bold=True)

    summary_paragraph = doc.add_paragraph()
    summary_paragraph.paragraph_format.space_before = Pt(8)
    summary_value = summary_paragraph.add_run(
        f"{get_document_number_label(data.document_kind)} {build_document_code(data.issue_date, data.document_kind)}"
    )
    set_run_font(summary_value, "Calibri", Pt(12), bold=False)

    heading_paragraph = doc.add_paragraph()
    heading_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading_run = heading_paragraph.add_run("DESCRIPCION                     TOTAL")
    set_run_font(heading_run, "Calibri", Pt(16), bold=True)

    items_table = doc.add_table(rows=1, cols=2)
    items_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    items_table.autofit = False
    header_cells = items_table.rows[0].cells
    set_cell_width(header_cells[0], 4.9)
    set_cell_width(header_cells[1], 1.6)
    header_cells[0].text = "Descripcion"
    header_cells[1].text = "Total"

    for cell in header_cells:
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.runs[0]
        set_run_font(run, "Calibri", Pt(12), bold=True)

    for item in data.items:
        row_cells = items_table.add_row().cells
        set_cell_width(row_cells[0], 4.9)
        set_cell_width(row_cells[1], 1.6)
        row_cells[0].text = item.description
        row_cells[1].text = format_money(item.amount) if item.show_amount else ""
        row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    for row in items_table.rows:
        for cell in row.cells:
            set_cell_borders(
                cell,
                top={"val": "nil"},
                bottom={"val": "nil"},
                left={"val": "nil"},
                right={"val": "nil"},
            )

    for entry in data.advance_payments:
        line = entry.display_line
        if not line:
            continue
        advance_paragraph = doc.add_paragraph()
        advance_run = advance_paragraph.add_run(line)
        set_run_font(advance_run, "Calibri", Pt(12), bold=False)

    if data.show_payment_details:
        footer_table = doc.add_table(rows=1, cols=1)
        footer_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        footer_table.autofit = False

        payment_cell = footer_table.rows[0].cells[0]
        set_cell_width(payment_cell, 6.5)

        set_cell_borders(
            payment_cell,
            top={"val": "single", "sz": "12", "color": "000000"},
            bottom={"val": "single", "sz": "12", "color": "000000"},
            left={"val": "single", "sz": "12", "color": "000000"},
            right={"val": "single", "sz": "12", "color": "000000"},
        )

        payment_cell.text = ""

        title_paragraph = payment_cell.paragraphs[0]
        title_run = title_paragraph.add_run("DATOS PARA EL PAGO")
        set_run_font(title_run, "Calibri", Pt(12), bold=True)

        bcp_title = payment_cell.add_paragraph()
        bcp_title.paragraph_format.space_after = Pt(4)
        bcp_title_run = bcp_title.add_run("Banco BCP")
        set_run_font(bcp_title_run, "Calibri", Pt(11), bold=True)

        bcp_account = payment_cell.add_paragraph()
        bcp_account.paragraph_format.space_after = Pt(4)
        bcp_account_label = bcp_account.add_run("Cuenta: ")
        set_run_font(bcp_account_label, "Calibri", Pt(11), bold=True)
        bcp_account_value = bcp_account.add_run(data.payment_bcp_account or "-")
        set_run_font(bcp_account_value, "Calibri", Pt(11), bold=False)

        bcp_cci = payment_cell.add_paragraph()
        bcp_cci.paragraph_format.space_after = Pt(6)
        bcp_cci_label = bcp_cci.add_run("CCI: ")
        set_run_font(bcp_cci_label, "Calibri", Pt(11), bold=True)
        bcp_cci_value = bcp_cci.add_run(data.payment_bcp_cci or "-")
        set_run_font(bcp_cci_value, "Calibri", Pt(11), bold=False)

        nation_title = payment_cell.add_paragraph()
        nation_title.paragraph_format.space_after = Pt(4)
        nation_title_run = nation_title.add_run("Banco de la Nación")
        set_run_font(nation_title_run, "Calibri", Pt(11), bold=True)

        nation_label = payment_cell.add_paragraph()
        nation_label.paragraph_format.space_after = Pt(4)
        nation_label_run = nation_label.add_run("Cuenta de Detracciones")
        set_run_font(nation_label_run, "Calibri", Pt(11), bold=True)

        nation_value = payment_cell.add_paragraph()
        nation_value_run = nation_value.add_run(data.payment_detracciones_account or "-")
        set_run_font(nation_value_run, "Calibri", Pt(11), bold=False)

        total_paragraph = doc.add_paragraph()
        total_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        total_paragraph.paragraph_format.space_before = Pt(8)
        total_label = total_paragraph.add_run(f"{get_total_label(data.tax_mode)} ")
        set_run_font(total_label, "Calibri", Pt(14), bold=True)
        total_value = total_paragraph.add_run(format_money(data.total))
        set_run_font(total_value, "Calibri", Pt(14), bold=True)
    else:
        total_paragraph = doc.add_paragraph()
        total_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        total_label = total_paragraph.add_run(f"{get_total_label(data.tax_mode)} ")
        set_run_font(total_label, "Calibri", Pt(14), bold=True)
        total_value = total_paragraph.add_run(format_money(data.total))
        set_run_font(total_value, "Calibri", Pt(14), bold=True)

    doc.save(str(output_path))
    return output_path
