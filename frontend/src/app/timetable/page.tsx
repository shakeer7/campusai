"use client";
import React, { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";
import ChatDrawer from "@/components/ChatDrawer";
import { fetchWithAuth } from "@/lib/api";
import { TimetableEntry } from "@/types";
import { CalendarDays, MapPin, Clock, User as UserIcon } from "lucide-react";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export default function TimetablePage() {
  const [selectedDay, setSelectedDay] = useState("Monday");
  const [classes, setClasses] = useState<TimetableEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchWithAuth(`/api/v1/students/timetable?day=${selectedDay}`)
      .then(setClasses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedDay]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Academic Timetable</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Semester 6 Class schedules, faculty allocations, and lecture hall locations.
            </p>
          </div>

          {/* Day Selector Pills */}
          <div className="flex space-x-2 border-b border-slate-200 dark:border-slate-800 pb-4 overflow-x-auto">
            {DAYS.map((day) => (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-5 py-2.5 rounded-2xl font-semibold text-sm transition-all ${
                  selectedDay === day
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                    : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                {day}
              </button>
            ))}
          </div>

          {/* Classes Timeline */}
          {loading ? (
            <div className="py-12 flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : classes.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-sm">
              No classes scheduled for {selectedDay}.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {classes.map((c) => (
                <div
                  key={c.id}
                  className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4 hover:border-blue-500/50 transition-all"
                >
                  <div className="flex items-center justify-between text-xs font-mono text-blue-600 dark:text-blue-400 font-bold">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{c.start_time} - {c.end_time}</span>
                    </span>
                    <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-slate-800">{c.room_number}</span>
                  </div>

                  <div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-white">{c.subject_name}</h3>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">{c.subject_code}</div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-300">
                    <UserIcon className="w-3.5 h-3.5 text-slate-400" />
                    <span>{c.faculty_name}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
      <ChatDrawer />
    </div>
  );
}
