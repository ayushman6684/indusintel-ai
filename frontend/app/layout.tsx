import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

// Fonts are loaded at runtime via a <link> tag (see below) rather than
// next/font/google, since next/font requires internet access to Google
// Fonts at *build* time — which breaks builds in offline/sandboxed CI
// environments. This keeps `npm run build` reliable everywhere.

export const metadata: Metadata = {
  title: "IndusIntel AI — Product Intelligence for Industrial Commerce",
  description:
    "AI-powered platform that turns unstructured industrial product data into validated, commerce-ready product intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=IBM+Plex+Sans:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto scrollbar-thin">{children}</main>
        </div>
      </body>
    </html>
  );
}
