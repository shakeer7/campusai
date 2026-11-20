"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { Activity, Users, Shield, Cpu, Database, CheckCircle2 } from "lucide-react";

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchWithAuth("/api/v1/admin/stats"),
      fetchWithAuth("/api/v1/admin/audit-logs?limit=25"),
    ])
      .then(([st, logs]) => {
        setStats(st);
        setAuditLogs(logs);
      })
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
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">System & AI Administration</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Cluster health, Bedrock LLM metrics, RBAC access governance, and immutable audit trails.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Enrolled Students</span>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">{stats?.total_students || 0}</div>
              <div className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Active Profiles</span>
              </div>
            </div>

            <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Faculty Members</span>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">{stats?.total_faculty || 0}</div>
              <div className="text-xs text-blue-600 dark:text-blue-400">CSE Department HoD & Staff</div>
            </div>

            <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">College Attendance Average</span>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white">{stats?.average_attendance_percentage}%</div>
              <div className="text-xs text-slate-500">Above mandatory 75% threshold</div>
            </div>

            <div className="p-6 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Audit Trail Events</span>
              <div className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">{stats?.total_audit_events || 0}</div>
              <div className="text-xs text-slate-500">Recorded with IP & Timestamps</div>
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Activity className="w-5 h-5 text-indigo-500" />
              <span>Immutable System Audit Trail</span>
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 text-xs font-semibold text-slate-400 uppercase">
                    <th className="pb-3">Timestamp</th>
                    <th className="pb-3">Action</th>
                    <th className="pb-3">Entity Type</th>
                    <th className="pb-3">Entity ID</th>
                    <th className="pb-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 text-xs">
                      <td className="py-3 font-mono text-slate-400">{log.timestamp.slice(0, 19)}</td>
                      <td className="py-3 font-bold text-slate-900 dark:text-white">{log.action}</td>
                      <td className="py-3 font-mono text-slate-600 dark:text-slate-300">{log.entity_type}</td>
                      <td className="py-3 font-mono text-slate-500">#{log.entity_id || "N/A"}</td>
                      <td className="py-3 text-slate-500 font-mono text-[11px] truncate max-w-xs">
                        {JSON.stringify(log.details)}
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
