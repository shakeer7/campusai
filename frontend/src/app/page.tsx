"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAuthToken } from "@/lib/api";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAuthToken();
    const role = localStorage.getItem("campusai_user_role");
    if (!token) {
      router.replace("/login");
    } else if (role === "faculty") {
      router.replace("/faculty");
    } else if (role === "admin") {
      router.replace("/admin");
    } else {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}
