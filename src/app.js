import { jsPDF } from "jspdf";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import { Capacitor } from "@capacitor/core";
import { Directory, Filesystem } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";
import {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  Header,
  ImageRun,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";

function getTodayIsoDate() {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60 * 1000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10);
}

// Global configuration loaded from API
let currentCompanyConfig = null;
let currentCompanyId = "jc-services";

async function loadCompanyConfig(companyId = "jc-services") {
  try {
    const response = await fetch(`/api/config?company_id=${encodeURIComponent(companyId)}`);
    if (!response.ok) throw new Error(`Failed to load config for ${companyId}`);
    currentCompanyConfig = await response.json();
    currentCompanyId = companyId;
    console.log(`✓ Loaded config for company: ${currentCompanyConfig.company_name}`);
    return currentCompanyConfig;
  } catch (error) {
    console.error("Error loading company config:", error);
    // Fall back to defaults if API fails
    return getDefaultConfig();
  }
}

function getDefaultConfig() {
  return {
    company_id: "jc-services",
    company_name: "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
    payment_bcp_account: "0011-0202-0100061544",
    payment_bcp_cci: "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
    payment_detracciones_account: "",
    payment_bank_label: "Cuenta en Soles BBVA",
    offer_note_primary: "Validez de la oferta: 10 dias",
    offer_note_secondary: "Montos incluye instalacion",
    workshop_address: "Planta de Trabajo: Jr. Tarapaca S/N, Pilcomayo - Huancayo",
    fiscal_address: "Domicilio: Jr. Tarapaca S/N, Pilcomayo - Huancayo",
  };
}

function createDefaultPaymentDetails() {
  if (!currentCompanyConfig) return {};
  return {
    show_payment_details: true,
    payment_bcp_account: currentCompanyConfig.payment_bcp_account,
    payment_bcp_cci: currentCompanyConfig.payment_bcp_cci,
    payment_detracciones_account: currentCompanyConfig.payment_detracciones_account,
    company_id: currentCompanyId,
  };
}

function createEmptyPayload() {
  return {
    customer_name: "",
    phone: "",
    ruc: "",
    issue_date: "",
    document_kind: "proforma",
    tax_mode: "sin_igv",
    header_kind: "generales",
    watermark_kind: "proforma",
    summary: "",
    items: [{ description: "", amount: "" }],
    advance_payments: [],
    ...createDefaultPaymentDetails(),
  };
}

const currencyFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const longDateFormatter = new Intl.DateTimeFormat("es-PE", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});
const PREVIEW_MIN_ITEM_ROWS = 8;

const form = document.getElementById("proforma-form");
const itemsList = document.getElementById("items-list");
const advancePaymentsList = document.getElementById("advance-payments-list");
const liveTotal = document.getElementById("live-total");
const previewScale = document.getElementById("preview-scale");
const previewPaper = document.getElementById("preview-paper");
const paymentDetailsFields = document.getElementById("payment-details-fields");
const importPdfButton = document.getElementById("import-pdf");
const importPdfInput = document.getElementById("import-pdf-input");
const saveProformaButton = document.getElementById("save-proforma");
const newProformaButton = document.getElementById("new-proforma");
const historyList = document.getElementById("history-list");
const historyEmpty = document.getElementById("history-empty");
const currentRecordLabel = document.getElementById("current-record-label");
const saveStatusMessage = document.getElementById("save-status-message");
const historyFilterButtons = [...document.querySelectorAll("[data-history-filter]")];

const PROFORMA_HISTORY_STORAGE_KEY = "proformas-history-v2";
const historyDateTimeFormatter = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "short",
  timeStyle: "short",
});

const headerAssetUrls = {
  pintura: new URL("./assets/header_corporate_pintura_v2.png", window.location.href).toString(),
  generales: new URL("./assets/header_corporate_generales_v2.png", window.location.href).toString(),
};

const watermarkAssetUrls = {
  proforma: new URL("./assets/watermark_corporate.png", window.location.href).toString(),
  pintura: new URL("./assets/watermark_corporate_paint.png", window.location.href).toString(),
};

const watermarkLayouts = {
  proforma: { width: 250, bottom: 150, opacity: 0.065 },
  pintura: { width: 250, bottom: 150, opacity: 0.065 },
};

const tableColumns = [
  { key: "itemNumber", labelLines: ["ITEM"], width: 30, align: "center" },
  { key: "description", labelLines: ["DESCRIPCIÓN"], width: 260, align: "left" },
  { key: "quantity", labelLines: ["CANT."], width: 40, align: "center" },
  { key: "unitPrice", labelLines: ["PRECIO", "UNIT"], width: 72, align: "right" },
  { key: "discount", labelLines: ["Desc."], width: 62, align: "center" },
  { key: "total", labelLines: ["TOTAL"], width: 80, align: "right" },
];

const headerImageDataUrlPromises = {};
const headerImageBufferPromises = {};
const watermarkImageDataUrlPromises = {};
const watermarkImagePropsPromises = {};
let currentRecordId = null;
let currentHistoryFilter = "generales";
let hasUnsavedChanges = false;

function getField(name) {
  return form.querySelector(`[name="${name}"]`);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function normalizeHeaderKind(value) {
  return value === "pintura" ? "pintura" : "generales";
}

function normalizeWatermarkKind(value) {
  return value === "pintura" ? "pintura" : "proforma";
}

function normalizeTaxMode(value) {
  return value === "con_igv" ? "con_igv" : "sin_igv";
}

function normalizeShowPaymentDetails(value) {
  return value === true || value === "true" || value === "on" || value === 1 || value === "1";
}

function normalizeNumber(value) {
  const numericValue = Number(value || 0);
  return Number.isFinite(numericValue) ? numericValue : 0;
}

function formatMoney(value) {
  return currencyFormatter.format(normalizeNumber(value));
}

function formatDisplayDate(value) {
  return value ? value.split("-").reverse().join("/") : "";
}

function formatLongDisplayDate(value) {
  if (!value) {
    return "";
  }

  const formatted = longDateFormatter.format(new Date(`${value}T00:00:00`));
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

function getDescriptionHeading(payload) {
  const base = String(payload.summary || "").trim();
  return (base || getDocumentTitle(payload.document_kind)).toUpperCase();
}

function getRecipientDetailLine(payload) {
  const parts = [];

  if (payload.ruc) {
    parts.push(`RUC: ${payload.ruc}`);
  }
  if (payload.phone) {
    parts.push(`Telefono: ${payload.phone}`);
  }

  return parts.join(" | ");
}

function getDocumentKindLabel(documentKind) {
  return documentKind === "contrato" ? "Contrato" : "Proforma";
}

function getDocumentTitle(documentKind) {
  return documentKind === "contrato" ? "CONTRATO DE SERVICIO" : "PROFORMA DE SERVICIO";
}

function getDocumentNumberLabel(documentKind) {
  return documentKind === "contrato" ? "Nro. Contrato" : "Nro. Cotizacion";
}

function buildDocumentCode(payload) {
  const baseDate = payload.issue_date || getTodayIsoDate();
  const compactDate = baseDate.replace(/-/g, "").slice(2);
  return `${payload.document_kind === "contrato" ? "CTR" : "CTZ"}-${compactDate}`;
}

function computeTaxBreakdown(total, taxMode) {
  if (normalizeTaxMode(taxMode) === "con_igv") {
    const taxable = total / 1.18;
    const igv = total - taxable;
    return {
      taxableLabel: "Valor venta",
      taxableAmount: taxable,
      taxLabel: "IGV",
      taxAmount: igv,
      totalLabel: "TOTAL",
      totalNote: "Monto expresado en soles. Incluye IGV.",
    };
  }

  return {
    taxableLabel: "Subtotal",
    taxableAmount: total,
    taxLabel: "IGV",
    taxAmount: 0,
    totalLabel: "TOTAL",
    totalNote: "Monto expresado en soles. Sin IGV.",
  };
}

function buildPreviewTableRows(items, minimumRows = PREVIEW_MIN_ITEM_ROWS) {
  const rows = items.map((item, index) => ({
    itemNumber: String(index + 1),
    description: item.description || "",
    quantity: item.description || item.hasAmount ? "1" : "",
    unitPrice: item.hasAmount ? formatMoney(item.amount) : "",
    discount: item.description || item.hasAmount ? "0.00%" : "",
    total: item.hasAmount ? formatMoney(item.amount) : "",
  }));

  const targetLength = Math.max(rows.length, minimumRows);
  while (rows.length < targetLength) {
    rows.push({
      itemNumber: "",
      description: "",
      quantity: "",
      unitPrice: "",
      discount: "",
      total: "",
    });
  }

  return rows;
}

function formatItemAmount(item) {
  return item.hasAmount ? formatMoney(item.amount) : "";
}

function formatAdvancePayment(entry) {
  const dateLabel = formatDisplayDate(entry.payment_date);
  const amountLabel = entry.hasAmount ? formatMoney(entry.amount) : "";

  if (dateLabel && amountLabel) {
    return `A cuenta ${dateLabel}: ${amountLabel}`;
  }
  if (dateLabel) {
    return `A cuenta ${dateLabel}`;
  }
  if (amountLabel) {
    return `A cuenta ${amountLabel}`;
  }
  return "";
}

function getTotalLabel(taxMode) {
  return normalizeTaxMode(taxMode) === "con_igv" ? "TOTAL:" : "TOTAL (SIN IGV):";
}

function normalizePaymentDetailText(value) {
  return String(value || "").trim();
}

function buildPaymentDetails(rawPayload = {}) {
  return {
    show_payment_details: normalizeShowPaymentDetails(rawPayload.show_payment_details),
    payment_bcp_account: defaultPaymentDetails.payment_bcp_account,
    payment_bcp_cci: defaultPaymentDetails.payment_bcp_cci,
    payment_detracciones_account: defaultPaymentDetails.payment_detracciones_account,
  };
}

function setPaymentDetailsVisibility(isVisible) {
  if (paymentDetailsFields) {
    paymentDetailsFields.hidden = !isVisible;
  }
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeExtractedText(value) {
  return String(value || "")
    .replace(/\r/g, "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n[ \t]+/g, "\n")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function cleanExtractedValue(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizeLabelValue(value) {
  return cleanExtractedValue(value)
    .replace(/Ã¡/gi, "a")
    .replace(/Ã©/gi, "e")
    .replace(/Ã­/gi, "i")
    .replace(/Ã³/gi, "o")
    .replace(/Ãº/gi, "u")
    .replace(/Ã±/gi, "n")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9():]/gi, "")
    .toLowerCase();
}

function extractSectionValue(text, startLabel, endLabel) {
  const lines = normalizeExtractedText(text)
    .split("\n")
    .map((line) => cleanExtractedValue(line));
  const normalizedStartLabel = normalizeLabelValue(startLabel);
  const normalizedEndLabel = normalizeLabelValue(endLabel);
  const values = [];
  let collecting = false;

  for (const line of lines) {
    const normalizedLine = normalizeLabelValue(line);

    if (!collecting) {
      if (
        normalizedLine === normalizedStartLabel ||
        normalizedLine.startsWith(normalizedStartLabel)
      ) {
        collecting = true;
        const separatorIndex = line.indexOf(":");
        const inlineValue = separatorIndex >= 0 ? cleanExtractedValue(line.slice(separatorIndex + 1)) : "";
        if (inlineValue) {
          values.push(inlineValue);
        }
      }
      continue;
    }

    if (
      normalizedLine === normalizedEndLabel ||
      normalizedLine.startsWith(normalizedEndLabel)
    ) {
      break;
    }

    if (line) {
      values.push(line);
    }
  }

  return cleanExtractedValue(values.join(" "));
}

function isAmountLine(value) {
  return /^-?\d{1,3}(?:,\d{3})*(?:\.\d{2})$|^-?\d+(?:\.\d{2})$/.test(String(value || "").trim());
}

function parseDocumentKindFromFileName(fileName) {
  return /contrato/i.test(fileName) ? "contrato" : "proforma";
}

function parseTaxModeFromText(text) {
  return /TOTAL\s*\(SIN IGV\)\s*:/i.test(text) ? "sin_igv" : "con_igv";
}

function parseItemsFromImportedBlock(blockText) {
  const lines = normalizeExtractedText(blockText)
    .split("\n")
    .map((line) => cleanExtractedValue(line))
    .filter(Boolean);
  const items = [];

  for (const line of lines) {
    if (/^A cuenta\b/i.test(line) || /^TOTAL(?:\s*\(SIN IGV\))?:?$/i.test(line)) {
      continue;
    }

    if (isAmountLine(line)) {
      const currentItem = items[items.length - 1];
      if (currentItem && !currentItem.amount) {
        currentItem.amount = line;
      } else {
        items.push({ description: "", amount: line });
      }
      continue;
    }

    items.push({ description: line, amount: "" });
  }

  return items.filter((item) => item.description || item.amount);
}

function parseAdvancePaymentsFromText(text) {
  const lines = normalizeExtractedText(text)
    .split("\n")
    .map((line) => cleanExtractedValue(line))
    .filter((line) => /^A cuenta\b/i.test(line));

  return lines.map((line) => {
    const withDateMatch = line.match(/^A cuenta\s+(\d{2}\/\d{2}\/\d{4})\s*:\s*([0-9.,]+)$/i);
    if (withDateMatch) {
      const [day, month, year] = withDateMatch[1].split("/");
      return {
        payment_date: `${year}-${month}-${day}`,
        amount: withDateMatch[2].replace(/,/g, ""),
      };
    }

    const amountOnlyMatch = line.match(/^A cuenta\s+([0-9.,]+)$/i);
    if (amountOnlyMatch) {
      return {
        payment_date: "",
        amount: amountOnlyMatch[1].replace(/,/g, ""),
      };
    }

    const dateOnlyMatch = line.match(/^A cuenta\s+(\d{2}\/\d{2}\/\d{4})$/i);
    if (dateOnlyMatch) {
      const [day, month, year] = dateOnlyMatch[1].split("/");
      return {
        payment_date: `${year}-${month}-${day}`,
        amount: "",
      };
    }

    return {
      payment_date: "",
      amount: "",
    };
  }).filter((entry) => entry.payment_date || entry.amount);
}

function extractSummaryFromText(text) {
  const match = normalizeExtractedText(text).match(/DESCRIPCION:\s*([\s\S]*?)\s*DESCRIPCION\s+TOTAL/i);
  return cleanExtractedValue(match?.[1] || "");
}

function buildImportedPayloadFromText(text, fileName, currentPayload) {
  const normalizedText = normalizeExtractedText(text);
  const itemBlockMatch = normalizedText.match(
    /DESCRIPCION\s+TOTAL\s*([\s\S]*?)\s*TOTAL(?:\s*\(SIN IGV\))?:\s*[0-9.,]+/i,
  );

  return {
    customer_name: extractSectionValue(normalizedText, "Señor(a):", "Teléfono:"),
    phone: extractSectionValue(normalizedText, "Teléfono:", "RUC:"),
    ruc: extractSectionValue(normalizedText, "RUC:", "Fecha:"),
    issue_date: (() => {
      const rawDate = extractSectionValue(normalizedText, "Fecha:", "PROFORMA:");
      const dateMatch = rawDate.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (!dateMatch) {
        return "";
      }
      return `${dateMatch[3]}-${dateMatch[2]}-${dateMatch[1]}`;
    })(),
    document_kind: parseDocumentKindFromFileName(fileName),
    tax_mode: parseTaxModeFromText(normalizedText),
    header_kind: currentPayload.header_kind,
    watermark_kind: currentPayload.watermark_kind,
    summary: extractSummaryFromText(normalizedText),
    items: parseItemsFromImportedBlock(itemBlockMatch?.[1] || ""),
    advance_payments: parseAdvancePaymentsFromText(itemBlockMatch?.[1] || normalizedText),
    ...buildPaymentDetails(currentPayload),
  };
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "cliente";
}

function buildFileName(payload, extension) {
  const issueDate = payload.issue_date || getTodayIsoDate();
  return `${issueDate}-${payload.document_kind}-${slugify(payload.customer_name)}.${extension}`;
}

function computeTotal(items) {
  return items.reduce((sum, item) => sum + item.amount, 0);
}

function formatHistoryDateTime(value) {
  const timestamp = Number(value);

  if (!Number.isFinite(timestamp)) {
    return "Sin registro";
  }

  return historyDateTimeFormatter.format(new Date(timestamp));
}

function generateRecordId() {
  return `proforma-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function cloneRawItems(items = []) {
  return items.map((item) => ({
    description: String(item.description || "").trim(),
    amount: String(item.amount ?? "").trim(),
  }));
}

function cloneRawAdvancePayments(entries = []) {
  return entries.map((entry) => ({
    payment_date: String(entry.payment_date || "").trim(),
    amount: String(entry.amount ?? "").trim(),
  }));
}

function buildStoredPayload(rawPayload) {
  const normalizedPayload = normalizePayload(rawPayload);

  return {
    customer_name: String(rawPayload.customer_name || "").trim(),
    phone: String(rawPayload.phone || "").trim(),
    ruc: String(rawPayload.ruc || "").trim(),
    issue_date: String(rawPayload.issue_date || "").trim(),
    document_kind: normalizedPayload.document_kind,
    tax_mode: normalizedPayload.tax_mode,
    header_kind: normalizedPayload.header_kind,
    watermark_kind: normalizedPayload.watermark_kind,
    summary: String(rawPayload.summary || "").trim(),
    items: cloneRawItems(rawPayload.items || []),
    advance_payments: cloneRawAdvancePayments(rawPayload.advance_payments || []),
    show_payment_details: normalizedPayload.show_payment_details,
    payment_bcp_account: normalizedPayload.payment_bcp_account,
    payment_bcp_cci: normalizedPayload.payment_bcp_cci,
    payment_detracciones_account: normalizedPayload.payment_detracciones_account,
  };
}

function hasMeaningfulContent(rawPayload) {
  const payload = buildStoredPayload(rawPayload);

  return Boolean(
    payload.customer_name ||
      payload.phone ||
      payload.ruc ||
      payload.issue_date ||
      payload.summary ||
      payload.items.some((item) => item.description || item.amount) ||
      payload.advance_payments.some((entry) => entry.payment_date || entry.amount),
  );
}

function readHistoryRecords() {
  try {
    const rawValue = window.localStorage.getItem(PROFORMA_HISTORY_STORAGE_KEY);
    if (!rawValue) {
      return [];
    }

    const parsed = JSON.parse(rawValue);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_error) {
    return [];
  }
}

function writeHistoryRecords(records) {
  const normalizedRecords = [...records].sort((left, right) => Number(right.updated_at) - Number(left.updated_at));
  window.localStorage.setItem(PROFORMA_HISTORY_STORAGE_KEY, JSON.stringify(normalizedRecords));
}

function getCurrentRecord() {
  return readHistoryRecords().find((record) => record.id === currentRecordId) || null;
}

function getRecordTitle(record) {
  return record.customer_name || "Sin cliente";
}

function summarizeRecord(record) {
  const summary = String(record.summary || "").trim();

  if (!summary) {
    return "Sin descripción general.";
  }

  return summary.length > 140 ? `${summary.slice(0, 137)}...` : summary;
}

function updateCurrentRecordState(message = "") {
  const currentRecord = getCurrentRecord();

  if (currentRecord) {
    currentRecordLabel.textContent = `Editando: ${getRecordTitle(currentRecord)}`;
    saveProformaButton.textContent = "Actualizar historial";
  } else {
    currentRecordLabel.textContent = "Nueva proforma";
    saveProformaButton.textContent = "Guardar en historial";
  }

  if (message) {
    saveStatusMessage.textContent = message;
    return;
  }

  if (hasUnsavedChanges) {
    saveStatusMessage.textContent = currentRecord
      ? "Hay cambios sin guardar en esta proforma."
      : "Completa la proforma y guárdala para conservarla en el historial.";
    return;
  }

  if (currentRecord) {
    saveStatusMessage.textContent = `Última actualización: ${formatHistoryDateTime(currentRecord.updated_at)}.`;
    return;
  }

  saveStatusMessage.textContent = "Las proformas guardadas se conservarán en este dispositivo.";
}

function createHistoryCard(record) {
  const article = document.createElement("article");
  article.className = "history-card";
  article.innerHTML = `
    <div class="history-card-header">
      <div>
        <h3 class="history-card-title">${escapeHtml(getRecordTitle(record))}</h3>
        <p class="history-card-subtitle">${escapeHtml(record.issue_date || "Sin fecha")} | ${escapeHtml(record.header_kind === "pintura" ? "Encabezado pintura" : "Encabezado general")}</p>
      </div>
      <span class="history-badge">${escapeHtml(record.document_kind)}</span>
    </div>
    <p class="history-summary">${escapeHtml(summarizeRecord(record))}</p>
    <div class="history-card-meta">
      <div class="history-meta-item">
        <span>Total</span>
        <strong>${formatMoney(record.total)}</strong>
      </div>
      <div class="history-meta-item">
        <span>Fecha</span>
        <strong>${escapeHtml(record.issue_date || "Pendiente")}</strong>
      </div>
      <div class="history-meta-item">
        <span>Actualizada</span>
        <strong>${escapeHtml(formatHistoryDateTime(record.updated_at))}</strong>
      </div>
    </div>
    <div class="history-card-actions">
      <button type="button" class="ghost-button history-open">Editar y revisar</button>
    </div>
  `;

  article.querySelector(".history-open").addEventListener("click", () => {
    currentRecordId = record.id;
    currentHistoryFilter = normalizeHeaderKind(record.header_kind);
    syncHistoryFilterButtons();
    fillForm(record.payload, {
      recordId: record.id,
      statusMessage: "Proforma cargada desde el historial.",
    });
  });

  return article;
}

function renderHistoryList() {
  const records = readHistoryRecords().filter(
    (record) => normalizeHeaderKind(record.header_kind) === currentHistoryFilter,
  );

  historyList.innerHTML = "";

  if (!records.length) {
    historyEmpty.hidden = false;
    return;
  }

  historyEmpty.hidden = true;
  records.forEach((record) => {
    historyList.appendChild(createHistoryCard(record));
  });
}

function syncHistoryFilterButtons() {
  historyFilterButtons.forEach((button) => {
    const isActive = button.dataset.historyFilter === currentHistoryFilter;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function setHistoryFilter(filter) {
  currentHistoryFilter = normalizeHeaderKind(filter);
  syncHistoryFilterButtons();
  renderHistoryList();
}

function saveCurrentProforma(options = {}) {
  const rawPayload = options.payload || getPayload();

  if (!hasMeaningfulContent(rawPayload)) {
    if (!options.silent) {
      window.alert("Completa al menos un dato antes de guardar la proforma.");
    }
    return null;
  }

  const payload = buildStoredPayload(rawPayload);
  const normalizedPayload = normalizePayload(payload);
  const existingRecord = getCurrentRecord();
  const now = Date.now();
  const total = computeTotal(normalizedPayload.items);
  const nextRecord = {
    id: existingRecord?.id || generateRecordId(),
    customer_name: normalizedPayload.customer_name,
    issue_date: normalizedPayload.issue_date,
    document_kind: normalizedPayload.document_kind,
    tax_mode: normalizedPayload.tax_mode,
    header_kind: normalizedPayload.header_kind,
    watermark_kind: normalizedPayload.watermark_kind,
    summary: normalizedPayload.summary,
    total,
    payload,
    created_at: existingRecord?.created_at || now,
    updated_at: now,
  };

  const previousRecords = readHistoryRecords().filter((record) => record.id !== nextRecord.id);
  writeHistoryRecords([nextRecord, ...previousRecords]);

  currentRecordId = nextRecord.id;
  hasUnsavedChanges = false;
  setHistoryFilter(nextRecord.header_kind);
  updateCurrentRecordState(
    options.successMessage ||
      (existingRecord ? "Proforma actualizada en el historial." : "Proforma guardada en el historial."),
  );

  return nextRecord;
}

function markFormAsDirty() {
  hasUnsavedChanges = true;
  updateCurrentRecordState();
}

function resetToNewProforma() {
  currentRecordId = null;
  hasUnsavedChanges = false;
  fillForm(createEmptyPayload(), {
    recordId: null,
    statusMessage: "Formulario listo para una nueva proforma.",
  });
}

function getHeaderImageDataUrl(headerKind) {
  const normalizedKind = normalizeHeaderKind(headerKind);

  if (!headerImageDataUrlPromises[normalizedKind]) {
    headerImageDataUrlPromises[normalizedKind] = fetch(headerAssetUrls[normalizedKind])
      .then((response) => response.blob())
      .then(
        (blob) =>
          new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          }),
      );
  }

  return headerImageDataUrlPromises[normalizedKind];
}

function getHeaderImageBuffer(headerKind) {
  const normalizedKind = normalizeHeaderKind(headerKind);

  if (!headerImageBufferPromises[normalizedKind]) {
    headerImageBufferPromises[normalizedKind] = fetch(headerAssetUrls[normalizedKind]).then((response) =>
      response.arrayBuffer(),
    );
  }

  return headerImageBufferPromises[normalizedKind];
}

function getWatermarkLayout(watermarkKind) {
  return watermarkLayouts[normalizeWatermarkKind(watermarkKind)];
}

function getWatermarkImageDataUrl(watermarkKind) {
  const normalizedKind = normalizeWatermarkKind(watermarkKind);

  if (!watermarkImageDataUrlPromises[normalizedKind]) {
    watermarkImageDataUrlPromises[normalizedKind] = fetch(watermarkAssetUrls[normalizedKind])
      .then((response) => response.blob())
      .then(
        (blob) =>
          new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          }),
      );
  }

  return watermarkImageDataUrlPromises[normalizedKind];
}

function getWatermarkImageProps(doc, watermarkKind, watermarkDataUrl) {
  const normalizedKind = normalizeWatermarkKind(watermarkKind);

  if (!watermarkImagePropsPromises[normalizedKind]) {
    watermarkImagePropsPromises[normalizedKind] = Promise.resolve(doc.getImageProperties(watermarkDataUrl));
  }

  return watermarkImagePropsPromises[normalizedKind];
}

function createItemRow(item = { description: "", amount: "" }) {
  const wrapper = document.createElement("div");
  wrapper.className = "item-row";

  wrapper.innerHTML = `
    <label>
      Descripcion
      <input type="text" name="item_description" value="${escapeHtml(item.description)}" placeholder="Descripcion del trabajo" />
    </label>
    <label>
      Total
      <input type="number" name="item_amount" min="0" step="0.01" value="${escapeHtml(String(item.amount ?? ""))}" placeholder="0.00" />
    </label>
    <button type="button" class="ghost-button remove-item">Quitar</button>
  `;

  wrapper.querySelector(".remove-item").addEventListener("click", () => {
    wrapper.remove();
    updatePreview();
  });

  wrapper.querySelectorAll("input").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });

  itemsList.appendChild(wrapper);
}

function createAdvancePaymentRow(entry = { payment_date: "", amount: "" }) {
  const wrapper = document.createElement("div");
  wrapper.className = "advance-row";

  wrapper.innerHTML = `
    <label>
      Fecha
      <input type="date" name="advance_payment_date" value="${escapeHtml(entry.payment_date || "")}" />
    </label>
    <label>
      Monto
      <input type="number" name="advance_payment_amount" min="0" step="0.01" value="${escapeHtml(String(entry.amount ?? ""))}" placeholder="0.00" />
    </label>
    <button type="button" class="ghost-button remove-advance-payment">Quitar</button>
  `;

  wrapper.querySelector(".remove-advance-payment").addEventListener("click", () => {
    wrapper.remove();
    updatePreview();
  });

  wrapper.querySelectorAll("input").forEach((input) => {
    input.addEventListener("input", updatePreview);
  });

  advancePaymentsList.appendChild(wrapper);
}

function getItems() {
  return [...itemsList.querySelectorAll(".item-row")].map((row) => ({
    description: row.querySelector('input[name="item_description"]').value.trim(),
    amount: row.querySelector('input[name="item_amount"]').value.trim(),
  }));
}

function getAdvancePayments() {
  return [...advancePaymentsList.querySelectorAll(".advance-row")].map((row) => ({
    payment_date: row.querySelector('input[name="advance_payment_date"]').value.trim(),
    amount: row.querySelector('input[name="advance_payment_amount"]').value.trim(),
  }));
}

function normalizeItems(rawItems = []) {
  return rawItems
    .map((item) => {
      const description = String(item.description || "").trim();
      const amountRaw = String(item.amount ?? "").trim();
      return {
        description,
        amount: normalizeNumber(amountRaw),
        hasAmount: amountRaw !== "",
      };
    })
    .filter((item) => item.description || item.hasAmount);
}

function normalizeAdvancePayments(rawAdvancePayments = []) {
  return rawAdvancePayments
    .map((entry) => {
      const paymentDate = String(entry.payment_date || "").trim();
      const amountRaw = String(entry.amount ?? "").trim();
      return {
        payment_date: paymentDate,
        amount: normalizeNumber(amountRaw),
        hasAmount: amountRaw !== "",
      };
    })
    .filter((entry) => entry.payment_date || entry.hasAmount);
}

function getPayload() {
  const customerNameField = getField("customer_name");
  const phoneField = getField("phone");
  const rucField = getField("ruc");
  const issueDateField = getField("issue_date");
  const summaryField = getField("summary");
  const documentKindField = form.querySelector('input[name="document_kind"]:checked');
  const taxModeField = form.querySelector('input[name="tax_mode"]:checked');
  const headerKindField = form.querySelector('input[name="header_kind"]:checked');
  const watermarkKindField = form.querySelector('input[name="watermark_kind"]:checked');
  const showPaymentDetailsField = getField("show_payment_details");

  return {
    customer_name: String(customerNameField?.value || "").trim(),
    phone: String(phoneField?.value || "").trim(),
    ruc: String(rucField?.value || "").trim(),
    issue_date: String(issueDateField?.value || "").trim(),
    document_kind: String(documentKindField?.value || "proforma"),
    tax_mode: normalizeTaxMode(String(taxModeField?.value || "sin_igv")),
    header_kind: normalizeHeaderKind(String(headerKindField?.value || "generales")),
    watermark_kind: normalizeWatermarkKind(String(watermarkKindField?.value || "proforma")),
    summary: String(summaryField?.value || "").trim(),
    items: getItems(),
    advance_payments: getAdvancePayments(),
    ...createDefaultPaymentDetails(),
    show_payment_details: Boolean(showPaymentDetailsField?.checked),
  };
}

function normalizePayload(rawPayload) {
  const items = normalizeItems(rawPayload.items || []);
  const legacyAdvancePayments =
    rawPayload.advance_payment && !rawPayload.advance_payments
      ? [{ payment_date: rawPayload.issue_date || "", amount: rawPayload.advance_payment }]
      : [];

  return {
    customer_name: String(rawPayload.customer_name || "").trim(),
    phone: String(rawPayload.phone || "").trim(),
    ruc: String(rawPayload.ruc || "").trim(),
    issue_date: String(rawPayload.issue_date || "").trim(),
    document_kind: rawPayload.document_kind === "contrato" ? "contrato" : "proforma",
    tax_mode: normalizeTaxMode(rawPayload.tax_mode),
    header_kind: normalizeHeaderKind(rawPayload.header_kind),
    watermark_kind: normalizeWatermarkKind(rawPayload.watermark_kind),
    summary: String(rawPayload.summary || "").trim(),
    items,
    advance_payments: normalizeAdvancePayments(rawPayload.advance_payments || legacyAdvancePayments),
    ...buildPaymentDetails(rawPayload),
  };
}

function updatePreview() {
  const payload = normalizePayload(getPayload());
  const total = computeTotal(payload.items);
  const taxBreakdown = computeTaxBreakdown(total, payload.tax_mode);

  liveTotal.textContent = formatMoney(total);
  previewPaper.dataset.headerKind = payload.header_kind;
  previewPaper.dataset.watermarkKind = payload.watermark_kind;

  document.getElementById("preview-document-title").textContent = getDescriptionHeading(payload);
  document.getElementById("preview-doc-number-label").textContent = getDocumentNumberLabel(payload.document_kind);
  document.getElementById("preview-doc-number").textContent = buildDocumentCode(payload);
  document.getElementById("preview-doc-date-long").textContent = formatLongDisplayDate(payload.issue_date);
  document.getElementById("preview-customer-name").textContent = payload.customer_name;
  document.getElementById("preview-customer-extra").textContent = getRecipientDetailLine(payload);
  document.getElementById("preview-taxable-label").textContent = taxBreakdown.taxableLabel;
  document.getElementById("preview-taxable-total").textContent = formatMoney(taxBreakdown.taxableAmount);
  document.getElementById("preview-tax-label").textContent = taxBreakdown.taxLabel;
  document.getElementById("preview-tax-amount").textContent = formatMoney(taxBreakdown.taxAmount);
  document.getElementById("preview-total-label").textContent = taxBreakdown.totalLabel;
  document.getElementById("preview-total").textContent = formatMoney(total);
  document.getElementById("preview-total-note").textContent = taxBreakdown.totalNote;
  document.getElementById("preview-payment-bcp-account").textContent = payload.payment_bcp_account;
  document.getElementById("preview-payment-bcp-cci").textContent = payload.payment_bcp_cci;

  const previewPaymentFooter = document.getElementById("preview-payment-footer");
  previewPaymentFooter.hidden = !payload.show_payment_details;
  setPaymentDetailsVisibility(payload.show_payment_details);

  const previewItemsBody = document.getElementById("preview-items-body");
  previewItemsBody.innerHTML = "";

  buildPreviewTableRows(payload.items).forEach((item) => {
    const row = document.createElement("div");
    row.className = "preview-item-row";
    row.innerHTML = `
      <span>${escapeHtml(item.itemNumber) || "&nbsp;"}</span>
      <span>${escapeHtml(item.description) || "&nbsp;"}</span>
      <span>${escapeHtml(item.quantity) || "&nbsp;"}</span>
      <span>${escapeHtml(item.unitPrice) || "&nbsp;"}</span>
      <span>${escapeHtml(item.discount) || "&nbsp;"}</span>
      <span>${escapeHtml(item.total) || "&nbsp;"}</span>
    `;
    previewItemsBody.appendChild(row);
  });

  const previewAdvanceLines = document.getElementById("preview-advance-lines");
  const previewAdvanceSection = document.getElementById("preview-advance-section");
  previewAdvanceLines.innerHTML = "";
  payload.advance_payments.forEach((entry) => {
    const line = formatAdvancePayment(entry);
    if (!line) {
      return;
    }
    const node = document.createElement("p");
    node.className = "advance-entry";
    node.textContent = line;
    previewAdvanceLines.appendChild(node);
  });
  previewAdvanceSection.hidden = previewAdvanceLines.childElementCount === 0;

  window.requestAnimationFrame(syncPreviewScale);
}

function fillForm(payload, options = {}) {
  currentRecordId = Object.prototype.hasOwnProperty.call(options, "recordId")
    ? options.recordId
    : currentRecordId;
  hasUnsavedChanges = false;
  getField("customer_name").value = payload.customer_name || "";
  getField("phone").value = payload.phone || "";
  getField("ruc").value = payload.ruc || "";
  getField("issue_date").value = payload.issue_date || "";
  getField("summary").value = payload.summary || "";
  form.querySelector(`input[name="document_kind"][value="${payload.document_kind}"]`).checked = true;
  form.querySelector(`input[name="tax_mode"][value="${normalizeTaxMode(payload.tax_mode)}"]`).checked = true;
  form.querySelector(`input[name="header_kind"][value="${normalizeHeaderKind(payload.header_kind)}"]`).checked = true;
  form.querySelector(`input[name="watermark_kind"][value="${normalizeWatermarkKind(payload.watermark_kind)}"]`).checked = true;
  getField("show_payment_details").checked = normalizeShowPaymentDetails(payload.show_payment_details);

  itemsList.innerHTML = "";
  (payload.items || [{ description: "", amount: "" }]).forEach((item) => createItemRow(item));

  advancePaymentsList.innerHTML = "";
  (payload.advance_payments || []).forEach((entry) => createAdvancePaymentRow(entry));

  setPaymentDetailsVisibility(normalizeShowPaymentDetails(payload.show_payment_details));
  updatePreview();
  updateCurrentRecordState(options.statusMessage || "");
}

function setBusy(buttonId, isBusy, label) {
  const button = document.getElementById(buttonId);
  button.disabled = isBusy;
  button.textContent = isBusy ? label : button.dataset.defaultLabel;
}

function isNativeCapacitorPlatform() {
  return Capacitor.isNativePlatform();
}

function getNativeShareDirectory() {
  return Capacitor.getPlatform() === "android" ? Directory.ExternalCache : Directory.Cache;
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = String(reader.result || "");
      resolve(result.includes(",") ? result.split(",")[1] : result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

function syncPreviewScale() {
  if (!previewScale || !previewPaper) {
    return;
  }
  previewScale.style.width = "";
  previewScale.style.height = "";
  previewPaper.style.transform = "";
}

async function extractTextFromPdfArrayBuffer(arrayBuffer) {
  const loadingTask = pdfjsLib.getDocument({
    data: new Uint8Array(arrayBuffer),
    disableWorker: true,
  });
  const pdf = await loadingTask.promise;
  const chunks = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const textContent = await page.getTextContent();
    chunks.push(textContent.items.map((item) => item.str).join("\n"));
  }

  return chunks.join("\n---PAGE---\n");
}

async function importPdfFile(file) {
  if (!file) {
    return;
  }

  try {
    setBusy("import-pdf", true, "Importando PDF...");
    const arrayBuffer = await file.arrayBuffer();
    const extractedText = await extractTextFromPdfArrayBuffer(arrayBuffer);
    const currentPayload = normalizePayload(getPayload());
    const importedPayload = buildImportedPayloadFromText(extractedText, file.name, currentPayload);

    if (!hasMeaningfulContent(importedPayload)) {
      throw new Error("No pude reconocer datos utiles en ese PDF.");
    }

    fillForm(importedPayload, {
      recordId: null,
      statusMessage: `PDF importado: ${file.name}. Revisa los datos antes de continuar.`,
    });

    saveCurrentProforma({
      payload: importedPayload,
      successMessage: `PDF importado y guardado en el historial: ${file.name}.`,
    });
  } catch (error) {
    window.alert(error.message || "No se pudo importar el PDF.");
  } finally {
    setBusy("import-pdf", false);
    if (importPdfInput) {
      importPdfInput.value = "";
    }
  }
}

async function exportBlob(blob, filename) {
  if (!isNativeCapacitorPlatform()) {
    downloadBlob(blob, filename);
    return;
  }

  const base64Data = await blobToBase64(blob);
  const directory = getNativeShareDirectory();
  const sharedPath = `shared/${Date.now()}/${filename}`;

  const savedFile = await Filesystem.writeFile({
    path: sharedPath,
    data: base64Data,
    directory,
    recursive: true,
  });

  const sharedFile = await Filesystem.getUri({
    path: sharedPath,
    directory,
  });

  let shareSupport = { value: false };
  try {
    shareSupport = await Share.canShare();
  } catch (_error) {
    shareSupport = { value: false };
  }

  if (!shareSupport?.value) {
    window.alert(`Archivo generado en: ${sharedFile.uri || savedFile.uri}`);
    return;
  }

  await Share.share({
    title: filename,
    files: [sharedFile.uri],
    dialogTitle: "Guardar o compartir archivo",
  });
}

async function requestServerDocument(kind, payload) {
  const response = await fetch(`/api/export/${kind}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorMessage = `No se pudo generar el archivo ${kind.toUpperCase()}.`;

    try {
      const errorPayload = await response.json();
      if (errorPayload?.error) {
        errorMessage = errorPayload.error;
      }
    } catch (_error) {
      // Keep the generic message if the response is not JSON.
    }

    throw new Error(errorMessage);
  }

  return response.blob();
}

function isShareCancelled(error) {
  const message = String(error?.message || error || "").toLowerCase();
  return message.includes("cancel");
}

function getPaymentDetailRows(payload) {
  const label = currentCompanyConfig?.payment_bank_label || "Cuenta Bancaria";
  return {
    primaryLine: `${label}: ${payload.payment_bcp_account || "-"} | ${payload.payment_bcp_cci || "-"}`,
  };
}

function drawPdfWatermarkLayer(
  doc,
  watermarkDataUrl,
  watermarkWidth,
  watermarkHeight,
  watermarkX,
  watermarkY,
  watermarkOpacity,
) {
  if (typeof doc.saveGraphicsState === "function") {
    doc.saveGraphicsState();
  }
  if (typeof doc.GState === "function" && typeof doc.setGState === "function") {
    doc.setGState(new doc.GState({ opacity: watermarkOpacity }));
  }
  doc.addImage(watermarkDataUrl, "PNG", watermarkX, watermarkY, watermarkWidth, watermarkHeight, undefined, "FAST");
  if (typeof doc.restoreGraphicsState === "function") {
    doc.restoreGraphicsState();
  }
}

async function buildPdfBlob(payload) {
  const imageDataUrl = await getHeaderImageDataUrl(payload.header_kind);
  const watermarkDataUrl = await getWatermarkImageDataUrl(payload.watermark_kind);
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "pt",
    format: "letter",
  });

  const pageWidth = 612;
  const pageHeight = 792;
  const total = computeTotal(payload.items);
  const taxBreakdown = computeTaxBreakdown(total, payload.tax_mode);
  const headerProps = doc.getImageProperties(imageDataUrl);
  const headerHeight = Math.min(210, pageWidth * (headerProps.height / headerProps.width));
  const watermarkProps = await getWatermarkImageProps(doc, payload.watermark_kind, watermarkDataUrl);
  const watermarkLayout = getWatermarkLayout(payload.watermark_kind);
  const watermarkWidth = watermarkLayout.width;
  const watermarkHeight = watermarkWidth * (watermarkProps.height / watermarkProps.width);
  const watermarkX = (pageWidth - watermarkWidth) / 2;
  const watermarkY = pageHeight - watermarkHeight - watermarkLayout.bottom;
  const columns = tableColumns;
  const tableX = 34;
  const tableWidth = columns.reduce((sum, column) => sum + column.width, 0);
  const notesHeight = 82;
  const paymentHeight = payload.show_payment_details ? 24 : 0;
  const footerReserve = payload.show_payment_details ? 152 : 138;
  const tableRows = buildPreviewTableRows(payload.items, payload.items.length || 4);

  const drawTableHeader = (x, y) => {
    let cursorX = x;
    doc.setDrawColor(122, 152, 191);
    doc.setFont("helvetica", "bold");
    columns.forEach((column) => {
      doc.setFillColor(74, 99, 133);
      doc.rect(cursorX, y, column.width, 34, "FD");
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(column.labelLines.length > 1 ? 8.9 : 9.5);
      const labelLines = column.labelLines || [column.label];
      const labelStartY = y + (labelLines.length > 1 ? 13 : 20);
      labelLines.forEach((line, index) => {
        doc.text(line, cursorX + column.width / 2, labelStartY + index * 9, {
          align: "center",
        });
      });
      cursorX += column.width;
    });
    doc.setTextColor(18, 48, 86);
  };

  const drawRow = (row, x, y) => {
    const splitLines = columns.map((column) =>
      row[column.key] ? doc.splitTextToSize(String(row[column.key]), Math.max(column.width - 8, 1)) : [""],
    );
    const rowHeight = Math.max(
      28,
      ...splitLines.map((lines) => (Array.isArray(lines) ? lines.length : 1) * 11 + 10),
    );
    let cursorX = x;
    doc.setDrawColor(122, 152, 191);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.7);

    columns.forEach((column, index) => {
      doc.rect(cursorX, y, column.width, rowHeight);
      const textLines = splitLines[index];
      const textX =
        column.align === "right"
          ? cursorX + column.width - 6
          : column.align === "center"
            ? cursorX + column.width / 2
            : cursorX + 5;
      let textY = y + 14;
      textLines.forEach((line) => {
        doc.text(line || " ", textX, textY, { align: column.align === "left" ? "left" : column.align, maxWidth: column.width - 8 });
        textY += 10;
      });
      cursorX += column.width;
    });

    return rowHeight;
  };

  const drawFooter = (pageBottomY) => {
    const notesY = pageBottomY - notesHeight;
    const totalsX = 390;
    const totalsWidth = 188;
    const totalsValueWidth = 78;
    const rowHeight = 24;
    const notesWidth = 332;

    doc.setTextColor(18, 48, 86);
    doc.setDrawColor(207, 216, 228);
    doc.roundedRect(34, notesY, notesWidth, notesHeight, 10, 10);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8.2);
    doc.text("OBSERVACIONES", 46, notesY + 14);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.8);
    doc.text(currentCompanyConfig?.offer_note_primary || "", 46, notesY + 34);
    doc.text(currentCompanyConfig?.offer_note_secondary || "", 46, notesY + 49, {
      maxWidth: notesWidth - 24,
    });

    doc.setDrawColor(90, 121, 164);
    doc.rect(totalsX, notesY, totalsWidth, rowHeight * 3);
    const totalRows = [
      [taxBreakdown.taxableLabel.toUpperCase(), formatMoney(taxBreakdown.taxableAmount)],
      [taxBreakdown.taxLabel.toUpperCase(), formatMoney(taxBreakdown.taxAmount)],
      [taxBreakdown.totalLabel, formatMoney(total)],
    ];

    totalRows.forEach(([label, value], index) => {
      const rowY = notesY + index * rowHeight;
      if (index > 0) {
        doc.line(totalsX, rowY, totalsX + totalsWidth, rowY);
      }
      doc.line(totalsX + totalsWidth - totalsValueWidth, rowY, totalsX + totalsWidth - totalsValueWidth, rowY + rowHeight);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(index === 2 ? 10 : 9);
      doc.text(label, totalsX + 10, rowY + 15);
      doc.text(value, totalsX + totalsWidth - 10, rowY + 15, { align: "right" });
    });

    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.5);
    doc.text(taxBreakdown.totalNote.toUpperCase(), totalsX + totalsWidth, notesY + rowHeight * 3 + 8, {
      align: "right",
    });

    if (payload.show_payment_details) {
      const label = currentCompanyConfig?.payment_bank_label || "Cuenta Bancaria";
      const paymentLine = `${label}: ${payload.payment_bcp_account || "-"} | ${payload.payment_bcp_cci || "-"}`;
      const paymentLines = doc.splitTextToSize(paymentLine, pageWidth - 68);
      let paymentY = pageHeight - 44 - ((paymentLines.length - 1) * 7);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.8);
      doc.setTextColor(17, 17, 17);
      paymentLines.forEach((line) => {
        doc.text(line, pageWidth / 2, paymentY, { align: "center" });
        paymentY += 7;
      });
    }

    doc.setFont("helvetica", "bold");
    doc.setFontSize(8.5);
    doc.setTextColor(47, 70, 103);
    doc.text(currentCompanyConfig?.workshop_address || "", pageWidth / 2, pageHeight - 20, { align: "center" });
    doc.text(currentCompanyConfig?.fiscal_address || "", pageWidth / 2, pageHeight - 8, { align: "center" });
    doc.setTextColor(18, 48, 86);
  };

  doc.setFont("helvetica", "normal");
  doc.addImage(imageDataUrl, "PNG", 0, 0, pageWidth, headerHeight, undefined, "FAST");
  drawPdfWatermarkLayer(
    doc,
    watermarkDataUrl,
    watermarkWidth,
    watermarkHeight,
    watermarkX,
    watermarkY,
    watermarkLayout.opacity,
  );
  let y = headerHeight + 18;
  doc.setTextColor(18, 48, 86);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12.4);
  doc.text(getDescriptionHeading(payload), pageWidth / 2, y, {
    align: "center",
    maxWidth: pageWidth - 36,
  });

  y += 28;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10.3);
  doc.text(`${getDocumentNumberLabel(payload.document_kind).toUpperCase()} ${buildDocumentCode(payload)}`, 18, y);
  doc.text(formatLongDisplayDate(payload.issue_date), 594, y, { align: "right" });

  y += 26;
  doc.text("Sres.", 18, y);
  y += 16;
  doc.setFont("helvetica", "bold");
  doc.text(payload.customer_name || "-", 18, y, { maxWidth: pageWidth - 36 });

  const recipientDetailLine = getRecipientDetailLine(payload);
  if (recipientDetailLine) {
    y += 16;
    doc.text(recipientDetailLine.toUpperCase(), 18, y, { maxWidth: pageWidth - 36 });
  }

  y += 20;
  drawTableHeader(tableX, y);
  y += 34;

  tableRows.forEach((row) => {
    const rowHeightEstimate = Math.max(
      28,
      ...columns.map((column) => {
        const lines = row[column.key]
          ? doc.splitTextToSize(String(row[column.key]), Math.max(column.width - 8, 1))
          : [""];
        return lines.length * 11 + 10;
      }),
    );

    if (y + rowHeightEstimate > pageHeight - footerReserve) {
      doc.addPage();
      drawPdfWatermarkLayer(
        doc,
        watermarkDataUrl,
        watermarkWidth,
        watermarkHeight,
        watermarkX,
        watermarkY,
        watermarkLayout.opacity,
      );
      y = 64;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12.4);
      doc.setTextColor(18, 48, 86);
      doc.text(getDescriptionHeading(payload), pageWidth / 2, y - 18, {
        align: "center",
        maxWidth: pageWidth - 36,
      });
      drawTableHeader(tableX, y);
      y += 34;
    }

    y += drawRow(row, tableX, y);
  });

  const advanceLines = payload.advance_payments.map((entry) => formatAdvancePayment(entry)).filter(Boolean);
  if (advanceLines.length) {
    y += 14;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8.2);
    doc.setTextColor(127, 144, 166);
    doc.text("ADELANTOS REGISTRADOS", 34, y);
    y += 14;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.8);
    doc.setTextColor(39, 67, 99);
    advanceLines.forEach((line) => {
      if (y + 12 > pageHeight - footerReserve) {
        doc.addPage();
        drawPdfWatermarkLayer(
          doc,
          watermarkDataUrl,
          watermarkWidth,
          watermarkHeight,
          watermarkX,
          watermarkY,
          watermarkLayout.opacity,
        );
        y = 64;
      }
      doc.text(line, 40, y);
      y += 12;
    });
  }

  drawFooter(pageHeight - 56);

  return doc.output("blob");
}

function docxText(text, options = {}) {
  return new TextRun({
    text,
    font: options.font || "Calibri",
    size: options.size || 22,
    bold: Boolean(options.bold),
  });
}

function borderedCell(children) {
  return new TableCell({
    borders: {
      top: { style: BorderStyle.SINGLE, size: 12, color: "000000" },
      bottom: { style: BorderStyle.SINGLE, size: 12, color: "000000" },
      left: { style: BorderStyle.SINGLE, size: 12, color: "000000" },
      right: { style: BorderStyle.SINGLE, size: 12, color: "000000" },
    },
    width: { size: 68, type: WidthType.PERCENTAGE },
    children,
  });
}

function plainCell(children, widthPercent = 32) {
  return new TableCell({
    borders: {
      top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
      right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
    },
    width: { size: widthPercent, type: WidthType.PERCENTAGE },
    children,
  });
}

async function buildDocxBlob(payload) {
  const imageBuffer = await getHeaderImageBuffer(payload.header_kind);
  const total = computeTotal(payload.items);
  const paymentDetails = getPaymentDetailRows(payload);
  const docxFontSizes = {
    body: 22,
    label: 24,
    heading: 26,
    total: 24,
  };

  const infoTable = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          borderedCell([
            new Paragraph({
              children: [
                docxText("Senor(a): ", { bold: true, size: docxFontSizes.label }),
                docxText(payload.customer_name, { size: docxFontSizes.label }),
              ],
              spacing: { after: 160 },
            }),
            new Paragraph({
              children: [
                docxText("Telefono: ", { bold: true, size: docxFontSizes.body }),
                docxText(payload.phone, { size: docxFontSizes.body }),
              ],
              spacing: { after: 140 },
            }),
            new Paragraph({
              children: [
                docxText("RUC: ", { bold: true, size: docxFontSizes.body }),
                docxText(payload.ruc, { size: docxFontSizes.body }),
              ],
              spacing: { after: 140 },
            }),
            new Paragraph({
              children: [
                docxText("Fecha: ", { bold: true, size: docxFontSizes.label }),
                docxText(formatDisplayDate(payload.issue_date), { size: docxFontSizes.label }),
              ],
            }),
          ]),
          plainCell(
            [
              new Paragraph({
                spacing: { after: 220 },
                children: [
                  docxText("PROFORMA: ", { bold: true, size: docxFontSizes.label }),
                  docxText(payload.document_kind === "proforma" ? "[X]" : "[ ]", {
                    bold: true,
                    size: docxFontSizes.label,
                  }),
                ],
              }),
              new Paragraph({
                children: [
                  docxText("CONTRATO: ", { bold: true, size: docxFontSizes.label }),
                  docxText(payload.document_kind === "contrato" ? "[X]" : "[ ]", {
                    bold: true,
                    size: docxFontSizes.label,
                  }),
                ],
              }),
            ],
            32,
          ),
        ],
      }),
    ],
  });

  const itemsTable = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: 72, type: WidthType.PERCENTAGE },
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [docxText("Descripcion", { bold: true, size: docxFontSizes.heading })],
              }),
            ],
          }),
          new TableCell({
            width: { size: 28, type: WidthType.PERCENTAGE },
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [docxText("Total", { bold: true, size: docxFontSizes.heading })],
              }),
            ],
          }),
        ],
      }),
      ...payload.items.map(
        (item) =>
          new TableRow({
            children: [
              new TableCell({
                width: { size: 72, type: WidthType.PERCENTAGE },
                children: [new Paragraph({ children: [docxText(item.description)] })],
              }),
              new TableCell({
                width: { size: 28, type: WidthType.PERCENTAGE },
                children: [
                  new Paragraph({
                    alignment: AlignmentType.RIGHT,
                    children: [docxText(item.hasAmount ? formatMoney(item.amount) : "")],
                  }),
                ],
              }),
            ],
          }),
      ),
    ],
  });

  const advanceParagraphs = payload.advance_payments
    .map((entry) => formatAdvancePayment(entry))
    .filter(Boolean)
    .map(
      (line) =>
        new Paragraph({
          spacing: { before: 120, after: 40 },
          children: [docxText(line, { size: docxFontSizes.body })],
        }),
    );

  const paymentFooterTable = payload.show_payment_details
    ? new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: [
          new TableRow({
            children: [
              borderedCell([
                new Paragraph({
                  children: [docxText(paymentDetails.primaryLine, { size: 18 })],
                }),
              ]),
              plainCell([], 0),
            ],
          }),
        ],
      })
    : null;

  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440,
              right: 1440,
              bottom: 1440,
              left: 1440,
            },
          },
        },
        headers: {
          default: new Header({
            children: [],
          }),
        },
        footers: {
          default: new Footer({
            children: [],
          }),
        },
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 120 },
            children: [
              new ImageRun({
                data: imageBuffer,
                transformation: { width: 468, height: 184 },
              }),
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { after: 140 },
            children: [docxText(getDescriptionHeading(payload), { bold: true, size: docxFontSizes.heading })],
          }),
          infoTable,
          new Paragraph({
            spacing: { before: 80, after: 120 },
            children: [docxText(`${getDocumentNumberLabel(payload.document_kind)} ${buildDocumentCode(payload)}`, { size: docxFontSizes.body })],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            spacing: { before: 280, after: 160 },
            children: [docxText("DESCRIPCION                     TOTAL", { bold: true, size: docxFontSizes.heading })],
          }),
          itemsTable,
          ...advanceParagraphs,
          ...(paymentFooterTable
            ? [
                paymentFooterTable,
                new Paragraph({
                  alignment: AlignmentType.RIGHT,
                  spacing: { before: 160 },
                  children: [
                    docxText(`${getTotalLabel(payload.tax_mode)} `, { bold: true, size: docxFontSizes.total }),
                    docxText(formatMoney(total), { bold: true, size: docxFontSizes.total }),
                  ],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 180, after: 40 },
                  children: [docxText(currentCompanyConfig?.workshop_address || "", { bold: true, size: 18 })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [docxText(currentCompanyConfig?.fiscal_address || "", { bold: true, size: 18 })],
                }),
              ]
            : [
                new Paragraph({
                  alignment: AlignmentType.RIGHT,
                  spacing: { before: 320 },
                  children: [
                    docxText(`${getTotalLabel(payload.tax_mode)} `, { bold: true, size: docxFontSizes.total }),
                    docxText(formatMoney(total), { bold: true, size: docxFontSizes.total }),
                  ],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 180, after: 40 },
                  children: [docxText(currentCompanyConfig?.workshop_address || "", { bold: true, size: 18 })],
                }),
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [docxText(currentCompanyConfig?.fiscal_address || "", { bold: true, size: 18 })],
                }),
              ]),
        ],
      },
    ],
  });

  return Packer.toBlob(doc);
}

async function downloadDocument(kind) {
  try {
    const rawPayload = getPayload();
    const payload = normalizePayload(rawPayload);

    if (hasMeaningfulContent(rawPayload)) {
      saveCurrentProforma({
        payload: rawPayload,
        silent: true,
        successMessage: "Proforma guardada en el historial antes de generar el archivo.",
      });
    }

    if (kind === "pdf") {
      setBusy("download-pdf", true, "Generando PDF...");
      const blob = isNativeCapacitorPlatform()
        ? await buildPdfBlob(payload)
        : await requestServerDocument("pdf", payload);
      await exportBlob(blob, buildFileName(payload, "pdf"));
    } else {
      setBusy("download-docx", true, "Generando Word...");
      const blob = await buildDocxBlob(payload);
      await exportBlob(blob, buildFileName(payload, "docx"));
    }
  } catch (error) {
    if (isShareCancelled(error)) {
      return;
    }
    window.alert(error.message || "No se pudo generar el archivo.");
  } finally {
    setBusy("download-pdf", false);
    setBusy("download-docx", false);
  }
}

importPdfButton.dataset.defaultLabel = "Importar PDF";
document.getElementById("download-pdf").dataset.defaultLabel = "Descargar PDF";
document.getElementById("download-docx").dataset.defaultLabel = "Descargar Word";

document.getElementById("add-item").addEventListener("click", () => {
  createItemRow();
  updatePreview();
});

document.getElementById("add-advance-payment").addEventListener("click", () => {
  createAdvancePaymentRow();
  updatePreview();
});

importPdfButton.addEventListener("click", () => {
  importPdfInput.click();
});

importPdfInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  await importPdfFile(file);
});

saveProformaButton.addEventListener("click", () => {
  saveCurrentProforma();
});

newProformaButton.addEventListener("click", () => {
  resetToNewProforma();
});

historyFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setHistoryFilter(button.dataset.historyFilter || "generales");
  });
});

document.getElementById("download-pdf").addEventListener("click", () => {
  downloadDocument("pdf");
});

document.getElementById("download-docx").addEventListener("click", () => {
  downloadDocument("docx");
});

form.addEventListener("input", updatePreview);
form.addEventListener("change", updatePreview);
form.addEventListener("input", markFormAsDirty);
form.addEventListener("change", markFormAsDirty);
window.addEventListener("resize", syncPreviewScale);
window.addEventListener("load", syncPreviewScale);

fillForm(createEmptyPayload());
setHistoryFilter(currentHistoryFilter);

// Load company configuration on app startup
(async () => {
  try {
    currentCompanyConfig = await loadCompanyConfig(currentCompanyId);
    fillForm(createEmptyPayload());
  } catch (error) {
    console.error("Failed to load company config, using defaults:", error);
    currentCompanyConfig = getDefaultConfig();
    fillForm(createEmptyPayload());
  }
})();

if (!isNativeCapacitorPlatform() && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(() => {
      // PWA support is optional; the app still works without it.
    });
  });
}
