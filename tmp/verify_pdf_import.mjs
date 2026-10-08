import fs from "node:fs/promises";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";

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
function cleanExtractedValue(value) { return String(value || "").replace(/\s+/g, " ").trim(); }
function escapeRegExp(value) { return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function extractSectionValue(text, startLabel, endLabel) {
  const pattern = new RegExp(`${escapeRegExp(startLabel)}\\s*([\\s\\S]*?)\\s*${escapeRegExp(endLabel)}`, "i");
  const match = text.match(pattern);
  return cleanExtractedValue(match?.[1] || "");
}
function isAmountLine(value) { return /^-?\d{1,3}(?:,\d{3})*(?:\.\d{2})$|^-?\d+(?:\.\d{2})$/.test(String(value || "").trim()); }
function parseTaxModeFromText(text) { return /TOTAL\s*\(SIN IGV\)\s*:/i.test(text) ? "sin_igv" : "con_igv"; }
function parseDocumentKindFromFileName(fileName) { return /contrato/i.test(fileName) ? "contrato" : "proforma"; }
function parseItemsFromImportedBlock(blockText) {
  const lines = normalizeExtractedText(blockText).split("\n").map(cleanExtractedValue).filter(Boolean);
  const items = [];
  for (const line of lines) {
    if (/^A cuenta\b/i.test(line) || /^TOTAL(?:\s*\(SIN IGV\))?:?$/i.test(line)) continue;
    if (isAmountLine(line)) {
      const currentItem = items[items.length - 1];
      if (currentItem && !currentItem.amount) currentItem.amount = line;
      else items.push({ description: "", amount: line });
      continue;
    }
    items.push({ description: line, amount: "" });
  }
  return items.filter((item) => item.description || item.amount);
}
function parseAdvancePaymentsFromText(text) {
  const lines = normalizeExtractedText(text).split("\n").map(cleanExtractedValue).filter((line) => /^A cuenta\b/i.test(line));
  return lines.map((line) => {
    const withDateMatch = line.match(/^A cuenta\s+(\d{2}\/\d{2}\/\d{4})\s*:\s*([0-9.,]+)$/i);
    if (withDateMatch) {
      const [day, month, year] = withDateMatch[1].split("/");
      return { payment_date: `${year}-${month}-${day}`, amount: withDateMatch[2].replace(/,/g, "") };
    }
    const amountOnlyMatch = line.match(/^A cuenta\s+([0-9.,]+)$/i);
    if (amountOnlyMatch) return { payment_date: "", amount: amountOnlyMatch[1].replace(/,/g, "") };
    return { payment_date: "", amount: "" };
  }).filter((entry) => entry.payment_date || entry.amount);
}
function extractSummaryFromText(text) {
  const match = normalizeExtractedText(text).match(/DESCRIPCION:\s*([\s\S]*?)\s*DESCRIPCION\s+TOTAL/i);
  return cleanExtractedValue(match?.[1] || "");
}
async function extractText(path) {
  const data = new Uint8Array(await fs.readFile(path));
  const doc = await pdfjsLib.getDocument({ data, disableWorker: true }).promise;
  const chunks = [];
  for (let pageNumber = 1; pageNumber <= doc.numPages; pageNumber += 1) {
    const page = await doc.getPage(pageNumber);
    const textContent = await page.getTextContent();
    chunks.push(textContent.items.map((item) => item.str).join("\n"));
  }
  return chunks.join("\n---PAGE---\n");
}
const fileName = '2026-07-09-proforma-cliente.pdf';
const text = normalizeExtractedText(await extractText(`output/pdf/${fileName}`));
const itemBlockMatch = text.match(/DESCRIPCION\s+TOTAL\s*([\s\S]*?)\s*TOTAL(?:\s*\(SIN IGV\))?:\s*[0-9.,]+/i);
const payload = {
  customer_name: extractSectionValue(text, 'Señor(a):', 'Teléfono:'),
  phone: extractSectionValue(text, 'Teléfono:', 'RUC:'),
  ruc: extractSectionValue(text, 'RUC:', 'Fecha:'),
  issue_date: extractSectionValue(text, 'Fecha:', 'PROFORMA:'),
  document_kind: parseDocumentKindFromFileName(fileName),
  tax_mode: parseTaxModeFromText(text),
  summary: extractSummaryFromText(text),
  items: parseItemsFromImportedBlock(itemBlockMatch?.[1] || ''),
  advance_payments: parseAdvancePaymentsFromText(itemBlockMatch?.[1] || text),
};
console.log(JSON.stringify(payload, null, 2));
