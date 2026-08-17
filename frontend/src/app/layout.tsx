import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DeepLM",
  description: "Grammar fixer and 12 tenses via FastAPI",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-zinc-950">{children}</body>
    </html>
  );
}
