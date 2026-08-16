"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, PackageSearch } from "lucide-react";
import Navbar from "@/components/Navbar";
import { api, Product } from "@/lib/api";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listProducts()
      .then(setProducts)
      .catch((e) => setError(e.message));
  }, []);

  const filtered = products.filter((p) =>
    `${p.name} ${p.product_code ?? ""} ${p.category ?? ""}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col min-h-full">
      <Navbar title="Products" subtitle={`${products.length} products in catalog`} />

      <div className="p-8 space-y-5">
        <div className="relative max-w-sm">
          <Search className="w-4 h-4 text-ink-faint absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, code, category..."
            className="w-full bg-base-900 border border-line rounded pl-9 pr-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:outline-none focus:border-amber/60"
          />
        </div>

        {error && (
          <div className="plate rounded p-4 text-sm text-status-fail">
            Could not load products: {error}
          </div>
        )}

        {!error && filtered.length === 0 && (
          <div className="plate rounded p-12 text-center">
            <PackageSearch className="w-8 h-8 text-ink-faint mx-auto mb-3" />
            <p className="text-sm text-ink-muted mb-4">
              {products.length === 0
                ? "No products yet. Upload a datasheet to create your first product record."
                : "No products match your search."}
            </p>
            <Link
              href="/upload"
              className="inline-block text-xs font-mono px-4 py-2 rounded border border-amber/40 text-amber hover:bg-amber-soft transition"
            >
              UPLOAD A PRODUCT
            </Link>
          </div>
        )}

        {filtered.length > 0 && (
          <div className="plate rounded overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-[10px] tracking-widest text-ink-faint uppercase border-b border-line">
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Code</th>
                  <th className="px-5 py-3 font-medium">Category</th>
                  <th className="px-5 py-3 font-medium">Manufacturer</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium text-right">Quality</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => (
                  <tr
                    key={p.id}
                    onClick={() => (window.location.href = `/products/${p.id}`)}
                    className="border-b border-line last:border-0 hover:bg-base-800/60 transition-colors cursor-pointer"
                  >
                    <td className="px-5 py-3 text-ink">{p.name}</td>
                    <td className="px-5 py-3 text-ink-muted font-mono text-xs">
                      {p.product_code || "—"}
                    </td>
                    <td className="px-5 py-3 text-ink-muted">
                      {p.category || "Uncategorized"}
                    </td>
                    <td className="px-5 py-3 text-ink-muted">
                      {p.manufacturer || "—"}
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
          </div>
        )}
      </div>
    </div>
  );
}
