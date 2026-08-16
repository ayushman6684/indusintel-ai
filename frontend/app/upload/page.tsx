"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { UploadCloud, FileText, Loader2, CheckCircle2, ArrowRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, ExtractionResponse } from "@/lib/api";

const STAGES = [
  "Uploading",
  "Extracting",
  "Structuring",
  "Enriching",
  "Validating",
  "Completed",
];

export default function UploadPage() {
  const [mode, setMode] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [manualText, setManualText] = useState("");
  const [productName, setProductName] = useState("");
  const [loading, setLoading] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    if (mode === "file" && !file) {
      setError("Select a PDF, CSV, or text file first.");
      return;
    }
    if (mode === "text" && !manualText.trim()) {
      setError("Enter some product text first.");
      return;
    }

    setLoading(true);
    setStageIndex(0);
    const form = new FormData();
    if (mode === "file" && file) form.append("file", file);
    if (mode === "text") form.append("manual_text", manualText);
    if (productName) form.append("product_name", productName);

    // Simulated staged progress — Day 2+ stages (Structuring, Enriching,
    // Validating) become real once the AI pipeline lands.
    setStageIndex(1);
    try {
      const res = await api.uploadDocument(form);
      // Uploading + Extracting are done here. Structuring/Enriching/
      // Validating happen on the product detail page when the AI pipeline
      // is triggered, so we stop the indicator at "Extracting complete"
      // rather than falsely claiming the later stages ran.
      setStageIndex(2);
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Upload failed");
      setStageIndex(0);
    } finally {
      setLoading(false);
    }
  }

  function loadDemoText() {
    setMode("text");
    setProductName("IndusFlow HCX-500 Centrifugal Pump");
    setManualText(DEMO_TEXT);
  }

  return (
    <div className="flex flex-col min-h-full">
      <Navbar
        title="Upload Product"
        subtitle="Ingest a datasheet, CSV, or raw product text"
      />

      <div className="p-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-5">
          <div className="plate rounded p-5">
            <div className="flex items-center gap-2 mb-4">
              <button
                onClick={() => setMode("file")}
                className={`text-xs font-mono px-3 py-1.5 rounded border ${
                  mode === "file"
                    ? "border-amber text-amber bg-amber-soft"
                    : "border-line text-ink-muted"
                }`}
              >
                FILE UPLOAD
              </button>
              <button
                onClick={() => setMode("text")}
                className={`text-xs font-mono px-3 py-1.5 rounded border ${
                  mode === "text"
                    ? "border-amber text-amber bg-amber-soft"
                    : "border-line text-ink-muted"
                }`}
              >
                MANUAL TEXT
              </button>
              <button
                onClick={loadDemoText}
                className="ml-auto text-xs font-mono px-3 py-1.5 rounded border border-steel/40 text-steel hover:bg-steel-soft transition"
              >
                LOAD DEMO PRODUCT
              </button>
            </div>

            <label className="block text-xs text-ink-muted mb-1.5">
              Product name (optional — inferred from file if left blank)
            </label>
            <input
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="e.g. IndusFlow HCX-500 Centrifugal Pump"
              className="w-full mb-4 bg-base-900 border border-line rounded px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:outline-none focus:border-amber/60"
            />

            {mode === "file" ? (
              <div
                ref={dropRef}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files?.[0];
                  if (f) setFile(f);
                }}
                className="border border-dashed border-line rounded-lg p-10 flex flex-col items-center justify-center text-center hover:border-amber/50 transition-colors"
              >
                <UploadCloud className="w-8 h-8 text-ink-faint mb-3" />
                <p className="text-sm text-ink-muted mb-1">
                  Drag a PDF, CSV, or .txt datasheet here
                </p>
                <p className="text-xs text-ink-faint mb-4">or</p>
                <label className="text-xs font-mono px-4 py-2 rounded border border-line text-ink hover:border-amber/50 cursor-pointer transition">
                  BROWSE FILES
                  <input
                    type="file"
                    accept=".pdf,.csv,.txt,.md"
                    className="hidden"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
                {file && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-ink">
                    <FileText className="w-4 h-4 text-amber" />
                    {file.name}
                  </div>
                )}
              </div>
            ) : (
              <textarea
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                rows={12}
                placeholder="Paste raw product specifications, a description, or datasheet text..."
                className="w-full bg-base-900 border border-line rounded px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:outline-none focus:border-amber/60 font-mono"
              />
            )}

            {error && (
              <p className="text-status-fail text-sm mt-3">{error}</p>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="mt-5 w-full py-2.5 rounded bg-amber text-base-950 font-semibold text-sm font-mono tracking-wide hover:brightness-110 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? "PROCESSING..." : "RUN EXTRACTION"}
            </button>
          </div>

          {result && (
            <div className="plate rounded p-5">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-status-pass" />
                <h3 className="font-display text-sm font-semibold text-ink">
                  Extracted Text
                </h3>
                <span className="ml-auto text-xs font-mono text-ink-faint">
                  {result.char_count} chars
                  {result.page_count ? ` · ${result.page_count} pages` : ""}
                </span>
              </div>
              <pre className="text-xs text-ink-muted font-mono whitespace-pre-wrap max-h-96 overflow-y-auto scrollbar-thin bg-base-900 border border-line rounded p-4">
                {result.extracted_text}
              </pre>
              {result.product_id && (
                <Link
                  href={`/products/${result.product_id}`}
                  className="mt-4 inline-flex items-center gap-1.5 text-xs font-mono px-4 py-2 rounded bg-amber text-base-950 font-semibold hover:brightness-110 transition"
                >
                  VIEW PRODUCT & RUN AI STRUCTURING <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              )}
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          <div className="plate rounded p-5 sticky top-8">
            <h3 className="font-display text-sm font-semibold text-ink mb-4">
              Pipeline Progress
            </h3>
            <ol className="space-y-3">
              {STAGES.map((stage, i) => {
                const done = i < stageIndex;
                const active = i === stageIndex && loading;
                return (
                  <li key={stage} className="flex items-center gap-3">
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono border ${
                        done
                          ? "bg-status-pass border-status-pass text-base-950"
                          : active
                          ? "border-amber text-amber"
                          : "border-line text-ink-faint"
                      }`}
                    >
                      {done ? "✓" : i + 1}
                    </span>
                    <span
                      className={`text-sm ${
                        done ? "text-ink" : active ? "text-amber" : "text-ink-faint"
                      }`}
                    >
                      {stage}
                    </span>
                    {active && (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-amber ml-auto" />
                    )}
                  </li>
                );
              })}
            </ol>
            <div className="mt-5 pt-4 border-t border-line text-xs text-ink-faint leading-relaxed">
              Uploading and Extracting run here. Structuring runs on the
              product page (click "View Product &amp; Run AI Structuring"
              above) — Enriching and Validating activate on Day 3.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const DEMO_TEXT = `INDUSFLOW INDUSTRIES
Technical Datasheet

Product: IndusFlow HCX-500 Centrifugal Pump
Product Code: HCX-500
Category: Industrial Pumps
Manufacturer: IndusFlow Industries

Description:
Heavy-duty end-suction centrifugal pump designed for water transfer,
chemical processing, and industrial cooling applications.

Technical Specifications:
- Material: Cast Iron body, Stainless Steel 316 impeller
- Dimensions: Length 450 mm, Width 300 mm, Height 380 mm
- Weight: 42 kg
- Voltage: 415V, 3-phase
- Power: 7.5 kW
- Maximum operating pressure: 10 bar
- Flow rate: 250 L/min
- Operating temperature range: -10C to 90C

Certifications: CE, ISO 9001
`;
