import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME ?? "GH-emails-mxf",
  description: "Outlook email triage dashboard",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-900 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
