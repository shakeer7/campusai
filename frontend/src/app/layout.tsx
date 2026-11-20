import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CampusAI — Production-Grade Agentic College Assistant",
  description: "Multilingual AI Academic Assistant for Chaitanya Bharathi Institute of Technology",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
