"use client";
import React, { useState, useRef, useEffect } from "react";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  Wrench,
  BookOpen,
  Volume2,
  ChevronDown,
  Loader2,
} from "lucide-react";
import VoiceRecorder, { playAudioText } from "./VoiceRecorder";
import { fetchWithAuth } from "@/lib/api";
import { ChatMessage, ToolCall, Citation } from "@/types";

export default function ChatDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "intro-1",
      role: "assistant",
      content:
        "Hello! I am **CampusAI**, your intelligent college assistant at CBIT. Ask me in **English, Telugu (తెలుగు), Romanized Telugu (Tenglish), or Hindi** about attendance, timetable, results, syllabus, or raise an attendance correction request!",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputMsg, setInputMsg] = useState("");
  const [selectedLang, setSelectedLang] = useState<string>("auto");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMsg;
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMsg("");
    setIsLoading(true);

    try {
      const payload: any = {
        message: text,
        preferred_language: selectedLang === "auto" ? null : selectedLang,
      };

      const response = await fetchWithAuth("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      const assistantMessage: ChatMessage = {
        id: `msg-resp-${Date.now()}`,
        role: "assistant",
        content: response.message,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        tools_executed: response.tools_executed,
        citations: response.citations,
        detected_language: response.detected_language,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-err-${Date.now()}`,
          role: "assistant",
          content: `⚠️ Error processing query: ${err.message || "Failed to reach backend."}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white p-4 rounded-full shadow-xl shadow-blue-500/30 flex items-center space-x-2 transition-transform transform hover:scale-105"
        >
          <Sparkles className="w-5 h-5" />
          <span className="font-semibold text-sm">Ask CampusAI</span>
        </button>
      )}

      {/* Slide-out Drawer */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="h-16 px-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-sm text-slate-900 dark:text-white flex items-center space-x-1.5">
                  <span>CampusAI Assistant</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">AWS Bedrock • Multilingual RAG</div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <select
                value={selectedLang}
                onChange={(e) => setSelectedLang(e.target.value)}
                className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-slate-700 dark:text-slate-300"
              >
                <option value="auto">🌐 Auto-Detect</option>
                <option value="en">English</option>
                <option value="te">తెలుగు (Telugu)</option>
                <option value="te-Latn">Tenglish (Romanized)</option>
                <option value="hi">हिन्दी (Hindi)</option>
              </select>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m) => {
              const isAssistant = m.role === "assistant";
              return (
                <div key={m.id} className={`flex flex-col ${isAssistant ? "items-start" : "items-end"}`}>
                  <div className="flex items-end space-x-2 max-w-[90%]">
                    {isAssistant && (
                      <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center text-blue-600 dark:text-blue-300 flex-shrink-0">
                        <Bot className="w-4 h-4" />
                      </div>
                    )}
                    <div
                      className={`p-3.5 rounded-2xl text-sm leading-relaxed ${
                        isAssistant
                          ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-sm"
                          : "bg-blue-600 text-white rounded-br-sm"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{m.content}</div>

                      {/* Tool Executions card */}
                      {m.tools_executed && m.tools_executed.length > 0 && (
                        <div className="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-700/60 space-y-1">
                          {m.tools_executed.map((t, idx) => (
                            <div
                              key={idx}
                              className="flex items-center space-x-1.5 text-[11px] font-mono text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900/60 p-1.5 rounded-lg border border-slate-200/50 dark:border-slate-700/50"
                            >
                              <Wrench className="w-3.5 h-3.5 text-blue-500" />
                              <span className="font-semibold text-blue-600 dark:text-blue-400">{t.tool_name}</span>
                              <span>• {t.status}</span>
                              {t.execution_time_ms && <span>({t.execution_time_ms}ms)</span>}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Citations card */}
                      {m.citations && m.citations.length > 0 && (
                        <div className="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-700/60 space-y-1">
                          <div className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 flex items-center space-x-1">
                            <BookOpen className="w-3 h-3 text-indigo-500" />
                            <span>Document Sources:</span>
                          </div>
                          {m.citations.map((c, idx) => (
                            <div
                              key={idx}
                              className="text-[11px] bg-indigo-50/60 dark:bg-slate-900/60 p-1.5 rounded text-slate-600 dark:text-slate-400"
                            >
                              <span className="font-medium text-indigo-700 dark:text-indigo-400">
                                {c.document_title} (Page {c.page_number})
                              </span>
                              <p className="text-[10px] text-slate-500 italic mt-0.5">{c.snippet}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 mt-1 px-1">
                    <span className="text-[10px] text-slate-400">{m.timestamp}</span>
                    {isAssistant && (
                      <button
                        onClick={() => playAudioText(m.content)}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        title="Read aloud"
                      >
                        <Volume2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-center space-x-2 text-slate-500 dark:text-slate-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>CampusAI is reasoning with AWS Bedrock...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="p-2 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 flex space-x-2 overflow-x-auto text-xs">
            <button
              onClick={() => handleSendMessage("What is my attendance?")}
              className="px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 whitespace-nowrap hover:border-blue-500"
            >
              📊 Attendance
            </button>
            <button
              onClick={() => handleSendMessage("How many classes do I need to reach 75%?")}
              className="px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 whitespace-nowrap hover:border-blue-500"
            >
              🎯 75% Target
            </button>
            <button
              onClick={() => handleSendMessage("Naku attendance entha undi?")}
              className="px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 whitespace-nowrap hover:border-blue-500"
            >
              🗣️ Telugu Query
            </button>
            <button
              onClick={() => handleSendMessage("Show today's timetable")}
              className="px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 whitespace-nowrap hover:border-blue-500"
            >
              📅 Timetable
            </button>
          </div>

          {/* Input Box */}
          <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center space-x-2">
            <VoiceRecorder
              onTranscriptReady={(transcript) => handleSendMessage(transcript)}
              isProcessing={isLoading}
            />
            <input
              type="text"
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask attendance, results, timetable..."
              className="flex-1 text-sm bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputMsg.trim() || isLoading}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
