"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { AttendanceSummary, StudentProfile, TimetableEntry } from "@/types";
import {
  CalendarCheck2,
  GraduationCap,
  CreditCard,
  Clock,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";

export default function StudentDashboard() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [attendance, setAttendance] = useState<AttendanceSummary | null>(null);
  const [todayClasses, setTodayClasses] = useState<TimetableEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [profData, attData, ttData] = await Promise.all([
          fetchWithAuth("/api/v1/students/me"),
          fetchWithAuth("/api/v1/students/attendance"),
          fetchWithAuth("/api/v1/students/timetable?day=Monday"),
        ]);
        setProfile(profData);
        setAttendance(attData);
        setTodayClasses(ttData);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const isEligible = attendance?.overall_eligible ?? true;
  const overallPct = attendance?.overall_percentage ?? 0;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          {/* Welcome Banner */}
          <div className="p-6 rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl shadow-blue-500/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="text-xs uppercase font-bold tracking-widest text-blue-200">
                {profile?.course} • Semester {profile?.current_semester}
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1">
                Welcome back, {profile?.full_name}!
              </h1>
              <p className="text-sm text-blue-100 mt-1">
                Roll No: <span className="font-mono font-semibold">{profile?.roll_number}</span> • Section {profile?.section}
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/20 text-center">
              <div className="text-xs text-blue-200">Cumulative CGPA</div>
              <div className="text-2xl font-extrabold">{profile?.cgpa} / 10.0</div>
            </div>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Attendance Card */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Attendance Status
                </span>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                    isEligible
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400"
                      : "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400"
                  }`}
                >
                  {isEligible ? "Exam Eligible (≥ 75%)" : "Condonation Needed (< 75%)"}
                </span>
              </div>
              <div className="flex items-baseline space-x-3">
                <div className="text-4xl font-extrabold text-slate-900 dark:text-white">{overallPct}%</div>
                <div className="text-xs text-slate-500">
                  {attendance?.overall_attended_classes} of {attendance?.overall_total_classes} classes
                </div>
              </div>
              <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${isEligible ? "bg-emerald-500" : "bg-amber-500"}`}
                  style={{ width: `${Math.min(100, overallPct)}%` }}
                />
              </div>
              <Link
                href="/attendance"
                className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center space-x-1 hover:underline pt-2"
              >
                <span>Calculate Target Classes</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Today's Schedule Card */}
            <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Classes Today (Monday)
                </span>
                <Clock className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                {todayClasses.length} Scheduled
              </div>
              <div className="text-xs text-slate-500 space-y-1">
                {todayClasses.slice(0, 2).map((c) => (
                  <div key={c.id} className="flex justify-between">
                    <span className="font-medium text-slate-700 dark:text-slate-300">{c.subject_name}</span>
                    <span className="font-mono text-slate-400">{c.start_time} ({c.room_number})</span>
                  </div>
                ))}
              </div>
              <Link
                href="/timetable"
                className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center space-x-1 hover:underline pt-2"
              >
                <span>Full Timetable</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* AI Assistant Quick Callout */}
            <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-slate-800 dark:to-slate-800/50 border border-indigo-100 dark:border-slate-700 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 mb-2">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-wider">AI Powered Assistant</span>
                </div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">Multilingual Campx AI</h3>
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                  Query in English, Telugu script, or Romanized Tenglish. Ask about syllabus, exams, or attendance correction.
                </p>
              </div>
              <div className="mt-4 text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center space-x-1">
                <span>Click the blue bubble anytime ➔</span>
              </div>
            </div>
          </div>

          {/* Subject-wise Attendance Table */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Semester 6 Subject Attendance</h2>
              <Link href="/attendance" className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                View Detailed Simulator
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-semibold text-slate-400 uppercase">
                    <th className="pb-3">Subject</th>
                    <th className="pb-3">Classes</th>
                    <th className="pb-3">Percentage</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {attendance?.subjects.map((s) => (
                    <tr key={s.subject_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="py-3.5 pr-4">
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{s.subject_name}</div>
                        <div className="text-xs text-slate-400 font-mono">{s.subject_code}</div>
                      </td>
                      <td className="py-3.5 text-slate-600 dark:text-slate-300 font-mono text-xs">
                        {s.attended_classes} / {s.total_classes}
                      </td>
                      <td className="py-3.5 font-bold text-slate-800 dark:text-slate-100">{s.percentage}%</td>
                      <td className="py-3.5">
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                            s.percentage >= 75
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                              : s.percentage >= 65
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300"
                              : "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300"
                          }`}
                        >
                          {s.status_indicator}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
