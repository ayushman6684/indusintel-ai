"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, UploadCloud, Boxes, BarChart3, Radar } from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutGrid },
  { href: "/products", label: "Products", icon: Boxes },
  { href: "/upload", label: "Upload", icon: UploadCloud },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 border-r border-line bg-base-900 flex flex-col">
      <div className="h-16 flex items-center gap-2 px-5 border-b border-line">
        <Radar className="w-5 h-5 text-amber" strokeWidth={2} />
        <div className="leading-tight">
          <div className="font-display font-semibold text-[15px] tracking-tight text-ink">
            IndusIntel
          </div>
          <div className="font-mono text-[10px] text-ink-faint tracking-widest">
            AI · v0.1
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map((item) => {
          const active =
            item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors",
                active
                  ? "bg-amber-soft text-amber border border-amber/30"
                  : "text-ink-muted hover:text-ink hover:bg-base-800 border border-transparent"
              )}
            >
              <Icon className="w-4 h-4" strokeWidth={2} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-line">
        <div className="plate rounded p-3">
          <div className="font-mono text-[10px] text-ink-faint tracking-wider mb-1">
            PIPELINE STATUS
          </div>
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-status-pass" />
            Extraction engine online
          </div>
        </div>
      </div>
    </aside>
  );
}
