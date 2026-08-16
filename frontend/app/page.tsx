"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Boxes, CheckCircle2, Gauge, AlertTriangle, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import StatCard from "@/components/StatCard";
import { api, DashboardSummary } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboardSummary()
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="flex flex-col min-h-full">
      <Navbar
        title="Dashboard"
        subtitle="Fleet-wide view of product data quality"
        action={
          <Link
            href="/upload"
            className="text-xs font-mono tracking-wide px-3 py-2 rounded bg-amber text-base-950 font-semibold hover:brightness-110 transition"
          >
            + NEW PRODUCT
          </Link>
        }
      />

      <div className="p-8 space-y-6">
        {error && (
          <div className="plate rounded p-4 border-status-fail/40 text-sm text-status-fail">
            Could not reach the API at the configured NEXT_PUBLIC_API_URL. Is
            the backend running? ({error})
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Products"
            value={summary?.total_products ?? "—"}
            icon={Boxes}
          />
          <StatCard
            label="Products Processed"
            value={summary?.products_processed ?? "—"}
            icon={CheckCircle2}
            tone="steel"
          />
          <StatCard
            label="Average Data Quality"
            value={summary ? `${summary.average_quality}%` : "—"}
            icon={Gauge}
            tone="amber"
          />
          <StatCard
            label="Validation Issues"
            value={summary?.validation_issues ?? "—"}
            icon={AlertTriangle}
            tone="warn"
          />
        </div>

        <div className="plate rounded">
          <div className="px-5 py-4 border-b border-line flex items-center justify-between">
            <h2 className="font-display text-sm font-semibold text-ink">
              Recent Products
            </h2>
            <Link
              href="/products"
              className="text-xs text-steel flex items-center gap-1 hover:underline"
            >
              View all <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          {summary && summary.recent_products.length === 0 && (
            <div className="p-10 text-center">
              <p className="text-sm text-ink-muted mb-4">
                No products yet. Upload a datasheet or load a demo product to
                get started.
              </p>
              <Link
                href="/upload"
                className="inline-block text-xs font-mono px-4 py-2 rounded border border-amber/40 text-amber hover:bg-amber-soft transition"
              >
                GO TO UPLOAD
              </Link>
            </div>
          )}

          {summary && summary.recent_products.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-[10px] tracking-widest text-ink-faint uppercase border-b border-line">
                  <th className="px-5 py-3 font-medium">Product</th>
                  <th className="px-5 py-3 font-medium">Category</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium text-right">Quality</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_products.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-line last:border-0 hover:bg-base-800/60 transition-colors"
                  >
                    <td className="px-5 py-3 text-ink">{p.name}</td>
                    <td className="px-5 py-3 text-ink-muted">
                      {p.category || "Uncategorized"}
                    </td>
                    <td className="px-5 py-3">
                      <span className="status-chip bg-status-passBg text-status-pass">
                        {p.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right font-mono text-ink">
                      {p.quality_score.toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
