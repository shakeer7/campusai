"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { AttendanceSummary, AttendanceTargetResult } from "@/types";
import { Target, Calculator, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";

export default function AttendancePage() {
  const [attendance, setAttendance] = useState<AttendanceSummary | null>(null);
  const [targetPct, setTargetPct] = useState(75.0);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | "">("");
  const [calcResult, setCalcResult] = useState<AttendanceTargetResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  useEffect(() => {
    fetchWithAuth("/api/v1/students/attendance").then(setAttendance).catch(console.error);
  }, []);

  const handleCalculate = async () => {
    setIsCalculating(true);
    try {
      const res = await fetchWithAuth("/api/v1/students/attendance/target", {
        method: "POST",
        body: JSON.stringify({
          subject_id: selectedSubjectId === "" ? null : Number(selectedSubjectId),
          target_percentage: targetPct,
        }),
      });
      setCalcResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsCalculating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Attendance Analytics & 75% Calculator
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Official attendance records from CBIT ERP with automated eligibility projections.
            </p>
          </div>

          {/* Target Calculator Box */}
          <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800/80 rounded-3xl border border-blue-200/60 dark:border-slate-700 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-bold">
              <Calculator className="w-5 h-5" />
              <span>Consecutive Class Target Simulator</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Scope
                </label>
                <select
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value === "" ? "" : Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm text-slate-900 dark:text-white"
                >
                  <option value="">Overall (All Subjects)</option>
                  {attendance?.subjects.map((s) => (
                    <option key={s.subject_id} value={s.subject_id}>
                      {s.subject_name} ({s.percentage}%)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Target Attendance %
                </label>
                <input
                  type="number"
                  min="50"
                  max="100"
                  step="1"
                  value={targetPct}
                  onChange={(e) => setTargetPct(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm text-slate-900 dark:text-white"
                />
              </div>

              <button
                onClick={handleCalculate}
                disabled={isCalculating}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {isCalculating ? "Calculating..." : "Run Target Math"}
              </button>
            </div>

            {calcResult && (
              <div className="mt-4 p-4 rounded-2xl bg-white dark:bg-slate-800 border border-blue-200 dark:border-slate-700 text-sm space-y-2">
                <div className="font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                  <Target className="w-4 h-4 text-blue-500" />
                  <span>Calculation Result for {calcResult.subject_name || "Overall"}</span>
                </div>
                <p className="text-slate-600 dark:text-slate-300">{calcResult.message}</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
                  <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="text-slate-400">Current Rate</div>
                    <div className="font-bold text-base text-slate-800 dark:text-slate-200">
                      {calcResult.current_percentage}%
                    </div>
                  </div>
                  <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="text-slate-400">Target Goal</div>
                    <div className="font-bold text-base text-blue-600 dark:text-blue-400">
                      {calcResult.target_percentage}%
                    </div>
                  </div>
                  <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="text-slate-400">Needed Classes</div>
                    <div className="font-bold text-base text-amber-600 dark:text-amber-400">
                      {calcResult.classes_needed}
                    </div>
                  </div>
                  <div className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <div className="text-slate-400">Safe to Miss</div>
                    <div className="font-bold text-base text-emerald-600 dark:text-emerald-400">
                      {calcResult.can_miss_classes}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Subject Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {attendance?.subjects.map((sub) => (
              <div
                key={sub.subject_id}
                className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-mono text-slate-400">{sub.subject_code}</span>
                    <h3 className="font-bold text-base text-slate-900 dark:text-white">{sub.subject_name}</h3>
                  </div>
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                      sub.percentage >= 75
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                        : "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300"
                    }`}
                  >
                    {sub.percentage}%
                  </span>
                </div>

                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${sub.percentage >= 75 ? "bg-emerald-500" : "bg-amber-500"}`}
                    style={{ width: `${Math.min(100, sub.percentage)}%` }}
                  />
                </div>

                <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                  <span>Attended: {sub.attended_classes}</span>
                  <span>Total Conducted: {sub.total_classes}</span>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
