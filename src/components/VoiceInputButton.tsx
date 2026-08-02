"use client";

import { useEffect, useRef, useState } from "react";

export interface VoiceTranscript {
  transcript: string;
  original?: string;
  intentNote?: string;
  language: string;
}

interface VoiceInputButtonProps {
  onTranscript: (result: VoiceTranscript) => void;
  disabled?: boolean;
}

export default function VoiceInputButton({ onTranscript, disabled }: VoiceInputButtonProps) {
  const [language, setLanguage] = useState<"en-US" | "hi-IN">("en-US");
  const [listening, setListening] = useState(false);
  const [translating, setTranslating] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    return () => {
      try {
        recognitionRef.current?.stop();
      } catch {
        // ignore
      }
    };
  }, []);

  const translateHindi = async (text: string): Promise<{ translated: string; intentNote: string }> => {
    const res = await fetch("/api/forge/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, source_lang: "hi", target_lang: "en" }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || "Translation failed");
    }
    const data = await res.json();
    return {
      translated: data.translated || text,
      intentNote: data.intent_note || "",
    };
  };

  const startListening = () => {
    const SR = (typeof window !== "undefined" &&
      ((window as unknown as { SpeechRecognition?: typeof SpeechRecognition }).SpeechRecognition ||
        (window as unknown as { webkitSpeechRecognition?: typeof SpeechRecognition }).webkitSpeechRecognition)) as
      | (new () => SpeechRecognition)
      | undefined;

    if (!SR) {
      window.alert("Speech recognition is not supported in this browser. Try Chrome or Edge.");
      return;
    }

    const recognition = new SR();
    recognitionRef.current = recognition;
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;

    let finalTranscript = "";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript + " ";
        } else {
          interim += result[0].transcript;
        }
      }
      onTranscript({ transcript: (finalTranscript + interim).trim(), language });
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== "aborted") {
        console.error("Speech recognition error:", event.error);
      }
      setListening(false);
    };

    recognition.onend = async () => {
      setListening(false);
      const hindiText = finalTranscript.trim();
      if (language === "hi-IN" && hindiText) {
        setTranslating(true);
        try {
          const { translated, intentNote } = await translateHindi(hindiText);
          onTranscript({ transcript: translated, original: hindiText, intentNote, language });
        } catch (err) {
          console.error("Hindi translation failed:", err);
          // Fallback: keep the Hindi transcript so the user does not lose input.
          onTranscript({ transcript: hindiText, original: hindiText, intentNote: "Translation failed; kept Hindi.", language });
        } finally {
          setTranslating(false);
        }
      }
    };

    recognition.start();
    setListening(true);
  };

  const stopListening = () => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex shrink-0 items-center gap-1">
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as "en-US" | "hi-IN")}
        disabled={disabled || listening}
        className="h-9 rounded-lg border border-slate-300 bg-white px-2 text-xs outline-none focus:border-slate-500"
      >
        <option value="en-US">English</option>
        <option value="hi-IN">Hindi</option>
      </select>
      <button
        type="button"
        onClick={listening ? stopListening : startListening}
        disabled={disabled || translating}
        className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm transition-colors ${
          listening
            ? "bg-rose-100 text-rose-700 hover:bg-rose-200"
            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
        } disabled:opacity-50`}
        title={listening ? "Stop listening" : "Start voice input"}
      >
        {translating ? "⏳" : listening ? "🎙️" : "🎤"}
      </button>
    </div>
  );
}
