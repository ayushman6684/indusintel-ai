import Navbar from "@/components/Navbar";
import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="flex flex-col min-h-full">
      <Navbar title="Analytics" subtitle="Fleet quality trends and validation breakdowns" />
      <div className="p-8">
        <div className="plate rounded p-12 text-center">
          <BarChart3 className="w-8 h-8 text-ink-faint mx-auto mb-3" />
          <p className="text-sm text-ink-muted">
            Charts (quality score trend, validation breakdown, confidence
            distribution) are built out on Day 4 once enough products have
            been processed through the full pipeline.
          </p>
        </div>
      </div>
    </div>
  );
}
