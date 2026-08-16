"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import clsx from "clsx";
import {
  Loader2,
  AlertTriangle,
  Sparkles,
  X,
  FileText,
  ShieldCheck,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, ProductDetail, Specification } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  SOURCE_VERIFIED: "Source Verified",
  AI_ENRICHED: "AI Enriched",
  USER_PROVIDED: "User Provided",
  INFERRED: "Inferred",
  UNKNOWN: "Unknown",
};

const STATUS_STYLES: Record<string, string> = {
  PASS: "bg-status-passBg text-status-pass",
  WARNING: "bg-status-warnBg text-status-warn",
  FAIL: "bg-status-failBg text-status-fail",
  UNKNOWN: "bg-base-700 text-ink-faint",
};

function confidenceTone(score: number) {
  if (score >= 90) return "text-status-pass";
  if (score >= 70) return "text-status-warn";
  return "text-status-fail";
}

function fieldLabel(name: string) {
  return name
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function ProductDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processError, setProcessError] = useState<string | null>(null);
  const [activeSpec, setActiveSpec] = useState<Specification | null>(null);

  function load() {
    api
      .getProduct(id)
      .then(setProduct)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (id) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function runProcessing() {
    setProcessing(true);
    setProcessError(null);
    try {
      const updated = await api.processProduct(id);
      setProduct(updated);
    } catch (e: any) {
      setProcessError(e.message || "Processing failed");
    } finally {
      setProcessing(false);
    }
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-full">
        <Navbar title="Product" />
        <div className="p-8">
          <div className="plate rounded p-6 text-status-fail text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex flex-col min-h-full">
        <Navbar title="Loading..." />
        <div className="p-8 flex items-center gap-2 text-ink-muted text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading product...
        </div>
      </div>
    );
  }

  const missingFields = product.specifications.length === 0 && product.status !== "completed";

  return (
    <div className="flex flex-col min-h-full">
      <Navbar
        title={product.name}
        subtitle={`${product.category || "Uncategorized"} · ${product.manufacturer || "Manufacturer unknown"}`}
        action={
          <button
            onClick={runProcessing}
            disabled={processing}
            className="flex items-center gap-2 text-xs font-mono px-4 py-2 rounded bg-amber text-base-950 font-semibold hover:brightness-110 transition disabled:opacity-50"
          >
            {processing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            {processing
              ? "RUNNING AI PIPELINE..."
              : product.specifications.length > 0
              ? "RE-RUN AI STRUCTURING"
              : "RUN AI STRUCTURING"}
          </button>
        }
      />

      <div className="p-8 space-y-6">
        {processError && (
          <div className="plate rounded p-4 text-sm text-status-fail">
            {processError}
            {processError.includes("ANTHROPIC_API_KEY") || processError.includes("GEMINI_API_KEY") ? (
              <p className="text-ink-faint mt-2 text-xs">
                Add your API key to <code className="text-ink">backend/.env</code> and restart
                the backend, then try again.
              </p>
            ) : null}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="plate rounded p-5 lg:col-span-2">
            <h2 className="font-display text-sm font-semibold text-ink mb-3">
              Product Overview
            </h2>
            <dl className="grid grid-cols-2 gap-y-3 text-sm">
              <dt className="text-ink-faint">Product Name</dt>
              <dd className="text-ink">{product.name}</dd>
              <dt className="text-ink-faint">Product Code</dt>
              <dd className="text-ink font-mono">{product.product_code || "—"}</dd>
              <dt className="text-ink-faint">Category</dt>
              <dd className="text-ink">{product.category || "—"}</dd>
              <dt className="text-ink-faint">Manufacturer</dt>
              <dd className="text-ink">{product.manufacturer || "—"}</dd>
              <dt className="text-ink-faint col-span-2 mt-1">Description</dt>
              <dd className="text-ink-muted col-span-2 leading-relaxed">
                {product.description || "No description available yet."}
              </dd>
            </dl>
          </div>

          <div className="plate rounded p-5 flex flex-col justify-between">
            <div>
              <div className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-2">
                IndusIntel Data Quality Score
              </div>
              <div className={clsx("font-display text-4xl font-semibold", confidenceTone(product.quality_score))}>
                {product.quality_score.toFixed(0)}
                <span className="text-lg text-ink-faint">/100</span>
              </div>
            </div>
            <p className="text-xs text-ink-faint mt-4 leading-relaxed">
              Based on average field confidence for now. Full weighted
              completeness/validation/source/normalization/traceability
              scoring lands with the Validation Agent (Day 3).
            </p>
          </div>
        </div>

        {missingFields && (
          <div className="plate rounded p-8 text-center">
            <FileText className="w-8 h-8 text-ink-faint mx-auto mb-3" />
            <p className="text-sm text-ink-muted mb-1">
              This product hasn't been structured yet.
            </p>
            <p className="text-xs text-ink-faint">
              Click "Run AI Structuring" above to extract and structure its
              specifications from the uploaded document(s).
            </p>
          </div>
        )}

        {product.specifications.length > 0 && (
          <div className="plate rounded overflow-hidden">
            <div className="px-5 py-4 border-b border-line flex items-center justify-between">
              <h2 className="font-display text-sm font-semibold text-ink">
                Technical Specifications
              </h2>
              <span className="text-xs text-ink-faint font-mono">
                Click a row for source detail
              </span>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-[10px] tracking-widest text-ink-faint uppercase border-b border-line">
                  <th className="px-5 py-3 font-medium">Field</th>
                  <th className="px-5 py-3 font-medium">Value</th>
                  <th className="px-5 py-3 font-medium">Confidence</th>
                  <th className="px-5 py-3 font-medium">Source</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {product.specifications.map((spec) => (
                  <tr
                    key={spec.id}
                    onClick={() => setActiveSpec(spec)}
                    className="border-b border-line last:border-0 hover:bg-base-800/60 transition-colors cursor-pointer"
                  >
                    <td className="px-5 py-3 text-ink">{fieldLabel(spec.field_name)}</td>
                    <td className="px-5 py-3 text-ink-muted font-mono text-xs">
                      {spec.value || "—"}
                    </td>
                    <td className="px-5 py-3">
                      <span className={clsx("font-mono text-xs", confidenceTone(spec.confidence))}>
                        {spec.confidence.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs text-ink-muted">
                      {SOURCE_LABELS[spec.source] || spec.source}
                    </td>
                    <td className="px-5 py-3">
                      <span className={clsx("status-chip", STATUS_STYLES[spec.status] || STATUS_STYLES.UNKNOWN)}>
                        {spec.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {product.status === "completed" && (
          <div className="plate rounded p-5">
            <div className="flex items-center gap-2 mb-1">
              <ShieldCheck className="w-4 h-4 text-steel" />
              <h2 className="font-display text-sm font-semibold text-ink">
                Validation
              </h2>
            </div>
            <p className="text-xs text-ink-faint">
              Deterministic + AI validation (conflict detection, PASS /
              WARNING / FAIL per field) runs on Day 3 — the fields above are
              currently marked{" "}
              <span className="status-chip bg-base-700 text-ink-faint">UNKNOWN</span>{" "}
              until then.
            </p>
          </div>
        )}
      </div>

      {activeSpec && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setActiveSpec(null)}
        >
          <div
            className="plate rounded-lg w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <h3 className="font-display text-sm font-semibold text-ink">
                {fieldLabel(activeSpec.field_name)}
              </h3>
              <button onClick={() => setActiveSpec(null)} className="text-ink-faint hover:text-ink">
                <X className="w-4 h-4" />
              </button>
            </div>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-1">
                  Value
                </dt>
                <dd className="text-ink">{activeSpec.value || "—"}</dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-1">
                  Source
                </dt>
                <dd className="text-ink">
                  {SOURCE_LABELS[activeSpec.source] || activeSpec.source}
                  {activeSpec.source_page ? ` — Page ${activeSpec.source_page}` : ""}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-1">
                  Confidence
                </dt>
                <dd className={confidenceTone(activeSpec.confidence)}>
                  {activeSpec.confidence.toFixed(0)}%
                </dd>
              </div>
              <div>
                <dt className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-1">
                  Validation
                </dt>
                <dd>
                  <span className={clsx("status-chip", STATUS_STYLES[activeSpec.status] || STATUS_STYLES.UNKNOWN)}>
                    {activeSpec.status}
                  </span>
                </dd>
              </div>
              {activeSpec.source === "AI_ENRICHED" && (
                <div className="flex items-start gap-2 bg-amber-soft border border-amber/30 rounded p-3 text-xs text-amber">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  This value was AI-enriched, not confirmed by the
                  manufacturer source — verify before treating it as fact.
                </div>
              )}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
