"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { SemesterResult } from "@/types";
import { GraduationCap, Award, BookCheck } from "lucide-react";

export default function ResultsPage() {
  const [results, setResults] = useState<SemesterResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWithAuth("/api/v1/students/results")
      .then(setResults)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Academic Results & CGPA</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Official university examination grades and semester-wise SGPA evaluations.
            </p>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-sm">No exam results recorded.</div>
          ) : (
            results.map((sem) => (
              <div
                key={sem.semester}
                className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-6"
              >
                <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold">
                      {sem.semester}
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900 dark:text-white">Semester {sem.semester} Results</h2>
                      <div className="text-xs text-slate-500">Total Credits Earned: {sem.total_credits}</div>
                    </div>
                  </div>
                  <div className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-bold text-sm shadow-md">
                    SGPA: {sem.sgpa} / 10.0
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="text-xs font-semibold text-slate-400 uppercase border-b border-slate-100 dark:border-slate-800">
                        <th className="pb-3">Subject</th>
                        <th className="pb-3">Internal</th>
                        <th className="pb-3">External</th>
                        <th className="pb-3">Total</th>
                        <th className="pb-3">Grade</th>
                        <th className="pb-3">Grade Points</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {sem.results.map((r, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                          <td className="py-3">
                            <div className="font-semibold text-slate-800 dark:text-slate-200">{r.subject_name}</div>
                            <div className="text-xs font-mono text-slate-400">{r.subject_code}</div>
                          </td>
                          <td className="py-3 font-mono text-slate-600 dark:text-slate-300">{r.internal_marks}</td>
                          <td className="py-3 font-mono text-slate-600 dark:text-slate-300">{r.external_marks}</td>
                          <td className="py-3 font-mono font-bold text-slate-800 dark:text-slate-100">{r.total_marks}</td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                              {r.grade}
                            </span>
                          </td>
                          <td className="py-3 font-mono font-semibold text-slate-700 dark:text-slate-300">{r.grade_points}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
