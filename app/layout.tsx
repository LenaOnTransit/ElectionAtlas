import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Election Desk",
  description: "Independent election coverage, analysis, and results.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head><base href="https://election-desk-ltm.caitlynnesman.chatgpt.site/" target="_top" /></head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
