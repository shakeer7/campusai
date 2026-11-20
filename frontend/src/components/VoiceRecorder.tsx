"use client";
import React, { useState, useRef } from "react";
import { Mic, Square, Volume2, Loader2 } from "lucide-react";

interface VoiceRecorderProps {
  onTranscriptReady: (transcript: string) => void;
  isProcessing?: boolean;
}

export default function VoiceRecorder({ onTranscriptReady, isProcessing }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const startListening = () => {
    setErrorMsg(null);
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMsg("Voice input is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-IN";

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          onTranscriptReady(transcript);
        }
      };

      recognition.onerror = (event: any) => {
        setIsRecording(false);
        if (event.error === "not-allowed") {
          setErrorMsg("Microphone permission was denied. Please allow microphone access.");
        } else {
          setErrorMsg(`Voice input error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      setErrorMsg("Could not initiate microphone recording.");
      setIsRecording(false);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="relative inline-flex items-center">
      {isRecording ? (
        <button
          type="button"
          onClick={stopListening}
          className="p-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white animate-pulse transition-all shadow-md shadow-red-500/20"
          title="Stop recording"
        >
          <Square className="w-4 h-4 fill-current" />
        </button>
      ) : (
        <button
          type="button"
          onClick={startListening}
          disabled={isProcessing}
          className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors disabled:opacity-50"
          title="Start voice input"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mic className="w-4 h-4" />}
        </button>
      )}

      {errorMsg && (
        <div className="absolute bottom-12 right-0 w-64 p-2 bg-red-50 dark:bg-red-950/80 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-600 dark:text-red-300 shadow-lg z-50">
          {errorMsg}
        </div>
      )}
    </div>
  );
}

export function playAudioText(text: string, lang: string = "en-IN") {
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}
