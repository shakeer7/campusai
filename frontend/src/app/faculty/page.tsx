"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { Check, X, ShieldAlert, BookOpen, Users, CheckCircle } from "lucide-react";

export default function FacultyDashboard() {
  const [profile, setProfile] = useState<any>(null);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [pendingCorrections, setPendingCorrections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState("");

  const loadData = async () => {
    try {
      const [p, s, c] = await Promise.all([
        fetchWithAuth("/api/v1/faculty/me"),
        fetchWithAuth("/api/v1/faculty/subjects"),
        fetchWithAuth("/api/v1/faculty/corrections"),
      ]);
      setProfile(p);
      setSubjects(s);
      setPendingCorrections(c);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDecision = async (requestId: number, decision: "approved" | "rejected") => {
    const notes = prompt(`Enter remarks for ${decision.toUpperCase()}:`, decision === "approved" ? "Verified logbook. Present." : "Unexcused absence.");
    if (!notes) return;

    try {
      await fetchWithAuth("/api/v1/faculty/corrections/decide", {
        method: "POST",
        body: JSON.stringify({
          request_id: requestId,
          decision,
          faculty_notes: notes,
        }),
      });
      setActionMsg(`Ticket #${requestId} marked as ${decision.toUpperCase()} successfully.`);
      loadData();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          {/* Faculty Header */}
          <div className="p-6 rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-xl shadow-teal-500/10 flex justify-between items-center">
            <div>
              <span className="text-xs uppercase font-bold tracking-widest text-emerald-200">
                {profile?.department} • {profile?.designation}
              </span>
              <h1 className="text-3xl font-extrabold tracking-tight mt-1">
                Faculty Portal: {profile?.full_name}
              </h1>
              <p className="text-xs text-emerald-100 mt-1">
                Employee ID: <span className="font-mono">{profile?.employee_id}</span> • {profile?.cabin_location}
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/20 text-center">
              <div className="text-xs text-emerald-200">Pending Approvals</div>
              <div className="text-2xl font-extrabold">{pendingCorrections.length}</div>
            </div>
          </div>

          {actionMsg && (
            <div className="p-4 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 rounded-2xl text-emerald-700 dark:text-emerald-300 text-sm">
              {actionMsg}
            </div>
          )}

          {/* Pending Attendance Corrections Queue */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-amber-500" />
                <span>Attendance Correction Review Queue</span>
              </h2>
              <span className="text-xs text-slate-400">Step 9/12: Human-in-the-Loop Verification</span>
            </div>

            {pendingCorrections.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-sm">
                No pending student correction requests at this time. All classes are up-to-date!
              </div>
            ) : (
              <div className="space-y-3">
                {pendingCorrections.map((req) => (
                  <div
                    key={req.id}
                    className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-50/50 dark:bg-slate-800/40"
                  >
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white">
                        {req.student_name} <span className="text-xs font-mono font-normal text-slate-500">({req.roll_number})</span>
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                        <b>{req.subject_name}</b> • Date: <span className="font-mono">{req.attendance_date}</span> (Period {req.period_number})
                      </div>
                      <p className="text-xs text-slate-500 italic mt-1.5">
                        Student Justification: "{req.reason}"
                      </p>
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleDecision(req.id, "approved")}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-xl shadow-md flex items-center space-x-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => handleDecision(req.id, "rejected")}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold text-xs rounded-xl shadow-md flex items-center space-x-1"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Assigned Subjects Overview */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Assigned Subjects & Rosters</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {subjects.map((sub) => (
                <div
                  key={sub.subject_id}
                  className="p-5 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 space-y-2"
                >
                  <span className="text-xs font-mono text-slate-400">{sub.code}</span>
                  <h3 className="font-bold text-slate-900 dark:text-white">{sub.name}</h3>
                  <div className="flex justify-between text-xs text-slate-500 pt-2 border-t border-slate-200/50 dark:border-slate-700">
                    <span>Enrolled: {sub.total_students} students</span>
                    <span>Avg Attendance: <b>{sub.average_attendance}%</b></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
