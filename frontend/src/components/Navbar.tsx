"use client";
import React, { useEffect, useState } from "react";
import { Bell, LogOut, User as UserIcon, Sparkles } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import { clearAuthSession } from "@/lib/api";

export default function Navbar() {
  const [userName, setUserName] = useState("Student User");
  const [userRole, setUserRole] = useState("STUDENT");

  useEffect(() => {
    const role = localStorage.getItem("campusai_user_role") || "student";
    setUserRole(role.toUpperCase());
    try {
      const data = JSON.parse(localStorage.getItem("campusai_user_data") || "{}");
      if (data.full_name) setUserName(data.full_name);
    } catch {}
  }, []);

  const handleLogout = () => {
    clearAuthSession();
    window.location.href = "/login";
  };

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 px-6 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
          C
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">CampusAI</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300">
              CBIT
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-800/60 px-3 py-1.5 rounded-lg border border-blue-200/50 dark:border-slate-700">
          <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">Bedrock AI Ready</span>
        </div>

        <ThemeToggle />

        <div className="h-6 w-[1px] bg-slate-200 dark:bg-slate-700" />

        <div className="flex items-center space-x-3">
          <div className="text-right hidden sm:block">
            <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">{userName}</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">{userRole}</div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 transition-colors"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
