"use client";
import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { Search, BookOpen, FileText, ArrowRight, Sparkles } from "lucide-react";

export default function ResourcesPage() {
  const [query, setQuery] = useState("What is the attendance criteria for exams?");
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const res = await fetchWithAuth("/api/v1/rag/search", {
        method: "POST",
        body: JSON.stringify({ query, top_k: 4 }),
      });
      setResults(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Academic Documents & RAG</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Semantic vector search across CBIT regulations, syllabus PDFs, and lecture notes.
            </p>
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex gap-2 max-w-3xl">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about syllabus, regulations, attendance rules..."
                className="w-full pl-12 pr-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white shadow-sm"
              />
            </div>
            <button
              type="submit"
              disabled={isSearching}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-2xl shadow-md transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSearching ? "Searching..." : "Semantic Search"}</span>
            </button>
          </form>

          {/* Search Results */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-800 dark:text-slate-200">Retrieved Grounded Documents ({results.length})</h2>
            {results.length === 0 ? (
              <div className="p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl text-center text-slate-400 text-sm">
                Try searching for <i>"attendance criteria"</i>, <i>"cloud computing"</i>, or <i>"strategic management"</i> above.
              </div>
            ) : (
              results.map((r) => (
                <div
                  key={r.chunk_id}
                  className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm space-y-2 hover:border-blue-500/40 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center space-x-1.5">
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>{r.document_title} • Page {r.page_number}</span>
                    </span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                      Score: {r.score}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{r.content}</p>
                </div>
              ))
            )}
          </div>
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
