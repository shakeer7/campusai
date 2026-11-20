"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CalendarCheck2,
  CalendarDays,
  GraduationCap,
  FileText,
  AlertCircle,
  ShieldCheck,
  Users,
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const [role, setRole] = useState("student");

  useEffect(() => {
    const savedRole = localStorage.getItem("campusai_user_role") || "student";
    setRole(savedRole);
  }, []);

  const studentLinks = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Attendance & 75%", href: "/attendance", icon: CalendarCheck2 },
    { label: "Timetable", href: "/timetable", icon: CalendarDays },
    { label: "Exam Results", href: "/results", icon: GraduationCap },
    { label: "Academic Resources", href: "/resources", icon: FileText },
    { label: "Attendance Tickets", href: "/corrections", icon: AlertCircle },
  ];

  const facultyLinks = [
    { label: "Faculty Dashboard", href: "/faculty", icon: ShieldCheck },
    { label: "Academic Resources", href: "/resources", icon: FileText },
  ];

  const adminLinks = [
    { label: "Admin Portal", href: "/admin", icon: Users },
    { label: "Academic Resources", href: "/resources", icon: FileText },
  ];

  let links = studentLinks;
  if (role === "faculty") links = facultyLinks;
  if (role === "admin") links = adminLinks;

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          Academic Navigation
        </div>
        {links.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all ${
                isActive
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700/60 text-xs">
        <div className="font-semibold text-slate-700 dark:text-slate-200 mb-1">Chaitanya Bharathi</div>
        <div className="text-slate-500 dark:text-slate-400">Autonomous Institute</div>
        <div className="mt-2 text-[10px] text-blue-600 dark:text-blue-400 font-mono">v1.0.0 Production</div>
      </div>
    </aside>
  );
}
