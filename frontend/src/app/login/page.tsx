"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Shield, User as UserIcon, Lock, ArrowRight, CheckCircle2 } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { setAuthSession } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("student@cbit.ac.in");
  const [password, setPassword] = useState("Student@123");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Authentication failed");
      }

      const tokenData = await res.json();
      setAuthSession(tokenData.access_token, tokenData.role, tokenData);

      if (tokenData.role === "faculty") {
        router.push("/faculty");
      } else if (tokenData.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to log in.");
    } finally {
      setIsLoading(false);
    }
  };

  const selectDemoAccount = (accEmail: string, accPass: string) => {
    setEmail(accEmail);
    setPassword(accPass);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-between p-6">
      <div className="flex justify-between items-center max-w-6xl w-full mx-auto">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
            C
          </div>
          <div>
            <div className="font-extrabold text-xl text-slate-900 dark:text-white">CampusAI</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">Chaitanya Bharathi Institute of Technology</div>
          </div>
        </div>
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full mx-auto my-12 bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agentic Academic Assistant</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Sign in to CampusAI</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Enter your institutional credentials or pick a demo role</p>
        </div>

        {errorMsg && (
          <div className="mb-6 p-3 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 rounded-xl text-xs text-red-600 dark:text-red-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Institutional Email</label>
            <div className="relative">
              <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/20 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
          >
            <span>{isLoading ? "Authenticating..." : "Sign In to Portal"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Quick-Switcher */}
        <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 text-center">
            Instant Demo Logins
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => selectDemoAccount("student@cbit.ac.in", "Student@123")}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === "student@cbit.ac.in"
                  ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 font-semibold"
                  : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              <div className="font-bold">Student Rohan</div>
              <div className="text-[10px] text-slate-500">Roll: 160121733001 (78%)</div>
            </button>

            <button
              type="button"
              onClick={() => selectDemoAccount("ananya@cbit.ac.in", "Student@123")}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === "ananya@cbit.ac.in"
                  ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 font-semibold"
                  : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              <div className="font-bold">Student Ananya</div>
              <div className="text-[10px] text-slate-500">Roll: 160121733045 (68%)</div>
            </button>

            <button
              type="button"
              onClick={() => selectDemoAccount("faculty@cbit.ac.in", "Faculty@123")}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === "faculty@cbit.ac.in"
                  ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 font-semibold"
                  : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              <div className="font-bold">Faculty Srinivas</div>
              <div className="text-[10px] text-slate-500">HoD CSE • Approver</div>
            </button>

            <button
              type="button"
              onClick={() => selectDemoAccount("admin@cbit.ac.in", "Admin@123")}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                email === "admin@cbit.ac.in"
                  ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 font-semibold"
                  : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
              }`}
            >
              <div className="font-bold">System Admin</div>
              <div className="text-[10px] text-slate-500">IT Ops • Audit & Stats</div>
            </button>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-slate-400">
        © 2026 Chaitanya Bharathi Institute of Technology. CampusAI is secured by AWS Bedrock & pgvector.
      </div>
    </div>
  );
}
