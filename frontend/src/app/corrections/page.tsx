"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { CorrectionRequestItem } from "@/types";
import { AlertCircle, Plus, CheckCircle2, Clock, XCircle, Send } from "lucide-react";

export default function CorrectionsPage() {
  const [tickets, setTickets] = useState<CorrectionRequestItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [subjectInput, setSubjectInput] = useState("Data Structures and Algorithms");
  const [attendanceDate, setAttendanceDate] = useState("2026-11-19");
  const [period, setPeriod] = useState(1);
  const [reason, setReason] = useState("Biometric device glitch at lab entry; attended on-duty.");
  const [previewData, setPreviewData] = useState<any>(null);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchWithAuth("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ message: "What is the status of my attendance correction requests?" }),
    })
      .then((res) => {
        const toolRes = res.tools_executed?.find((t: any) => t.tool_name === "get_correction_request_status");
        if (toolRes && toolRes.tool_output?.requests) {
          setTickets(toolRes.tool_output.requests);
        }
      })
      .catch(console.error);
  }, []);

  const handleDraftRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsDrafting(true);
    try {
      const res = await fetchWithAuth("/api/v1/workflows/correction/draft", {
        method: "POST",
        body: JSON.stringify({
          subject_code_or_name: subjectInput,
          attendance_date: attendanceDate,
          period_number: period,
          reason,
        }),
      });
      setPreviewData(res);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsDrafting(false);
    }
  };

  const handleConfirmSubmit = async () => {
    if (!previewData) return;
    setIsSubmitting(true);
    try {
      const res = await fetchWithAuth("/api/v1/workflows/correction/confirm", {
        method: "POST",
        body: JSON.stringify({
          workflow_id: previewData.workflow_id,
          confirmed: true,
        }),
      });
      setMessage("Ticket submitted successfully! Assigned to faculty for approval.");
      setPreviewData(null);
      setIsModalOpen(false);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Attendance Correction Requests</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Agentic Human-in-the-Loop workflow managed by LangGraph. Requires faculty verification.
              </p>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-2xl shadow-lg shadow-blue-500/20 flex items-center space-x-2 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Raise Correction</span>
            </button>
          </div>

          {message && (
            <div className="p-4 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 rounded-2xl text-emerald-700 dark:text-emerald-300 text-sm">
              {message}
            </div>
          )}

          {/* Tickets List */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Active & Past Requests</h2>
            {tickets.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                No tickets currently found. Click "Raise Correction" above to test the agent workflow!
              </div>
            ) : (
              <div className="space-y-3">
                {tickets.map((t) => (
                  <div
                    key={t.id}
                    className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex justify-between items-start"
                  >
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white">Ticket #{t.id} — {t.subject}</div>
                      <div className="text-xs text-slate-500 mt-0.5">Date: {t.attendance_date} (Period {t.period_number})</div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">Reason: <i>"{t.reason}"</i></p>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400">
                      {t.review_status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Modal */}
          {isModalOpen && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Raise Attendance Discrepancy</h3>

                {!previewData ? (
                  <form onSubmit={handleDraftRequest} className="space-y-3 text-sm">
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Subject Name or Code</label>
                      <input
                        type="text"
                        value={subjectInput}
                        onChange={(e) => setSubjectInput(e.target.value)}
                        required
                        className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-sm"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Class Date</label>
                        <input
                          type="date"
                          value={attendanceDate}
                          onChange={(e) => setAttendanceDate(e.target.value)}
                          required
                          className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Period (1-7)</label>
                        <input
                          type="number"
                          min="1"
                          max="7"
                          value={period}
                          onChange={(e) => setPeriod(Number(e.target.value))}
                          required
                          className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-sm"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Justification Reason</label>
                      <textarea
                        rows={3}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        required
                        className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-sm"
                      />
                    </div>

                    <div className="flex justify-end space-x-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setIsModalOpen(false)}
                        className="px-4 py-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isDrafting}
                        className="px-5 py-2 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isDrafting ? "Drafting..." : "Review Draft Preview"}
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="p-4 bg-blue-50 dark:bg-slate-800 rounded-2xl border border-blue-200 dark:border-slate-700 space-y-2">
                      <div className="font-bold text-slate-900 dark:text-white">AI Agent Draft Preview</div>
                      <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                        <div><b>Student:</b> {previewData.student_name} ({previewData.student_roll})</div>
                        <div><b>Subject:</b> {previewData.subject_name} ({previewData.subject_code})</div>
                        <div><b>Faculty Assigned:</b> {previewData.faculty_name}</div>
                        <div><b>Class Time:</b> {previewData.attendance_date} (Period {previewData.period_number})</div>
                        <div><b>Requested:</b> {previewData.current_status} ➔ {previewData.requested_status}</div>
                        <div><b>Reason:</b> "{previewData.reason}"</div>
                      </div>
                    </div>

                    <p className="text-xs text-slate-500 italic">
                      Step 6/12: Explicit student confirmation is required before submitting ticket.
                    </p>

                    <div className="flex justify-end space-x-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setPreviewData(null)}
                        className="px-4 py-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                      >
                        Edit Draft
                      </button>
                      <button
                        onClick={handleConfirmSubmit}
                        disabled={isSubmitting}
                        className="px-5 py-2 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 disabled:opacity-50"
                      >
                        {isSubmitting ? "Lodging Ticket..." : "Confirm & Submit to Faculty"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
