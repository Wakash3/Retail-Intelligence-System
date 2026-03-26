"use client";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { postWithAuth } from "@/lib/api";
import styles from "./NuruChat.module.css";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function NuruChat() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      inputRef.current?.focus();
    }
  }, [open, messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || !token || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setLoading(true);

    const res = await postWithAuth("/api/chat/analyst", { messages: history }, token);
    const reply = res?.reply ?? "Sorry, I couldn't process that.";
    setMessages([...history, { role: "assistant", content: reply }]);
    setLoading(false);
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <>
      {/* FAB button */}
      <button
        className={`${styles.fab} ${open ? styles.fabOpen : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-label="Chat with Gladwell"
      >
        {open ? <span className={styles.fabClose}>✕</span> : <span>✦</span>}
      </button>

      {/* Chat panel */}
      {open && (
        <div className={styles.panel}>
          {/* Header */}
          <div className={styles.header}>
            <div className={styles.headerIcon}>✦</div>
            <div>
              <div className={styles.headerName}>Gladwell</div>
              <div className={styles.headerSub}>
                <span className={styles.dot} />
                AI Retail Analyst
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={`${styles.bubble} ${styles.bot}`}>
                Hey! I'm Gladwell, your retail intelligence analyst. Ask me anything about branches, margins, or products.
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`${styles.bubble} ${m.role === "user" ? styles.user : styles.bot}`}
              >
                {m.content}
              </div>
            ))}
            {loading && (
              <div className={`${styles.bubble} ${styles.bot} ${styles.typing}`}>
                <span /><span /><span />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className={styles.inputRow}>
            <input
              ref={inputRef}
              className={styles.input}
              placeholder="Ask anything…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button
              className={styles.sendBtn}
              onClick={send}
              disabled={loading || !input.trim()}
            >
              ↑
            </button>
          </div>
        </div>
      )}
    </>
  );
}
