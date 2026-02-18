"use client";

import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

const N8N_WEBHOOK_URL = "https://heavily-busy-titmouse.ngrok-free.app/webhook/rag-chat-webhook-001";

function generateSessionId() {
    return "session-" + Math.random().toString(36).substring(2, 12);
}

function getSessionId() {
    if (typeof window === "undefined") return "default-session";
    let id = sessionStorage.getItem("chat_session_id");
    if (!id) {
        id = generateSessionId();
        sessionStorage.setItem("chat_session_id", id);
    }
    return id;
}

export default function ChatBot() {
    const [open, setOpen] = useState(false);
    const location = useLocation();
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            text: "Hi! 👋 Ask me anything about your orders, customers, or products.",
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(getSessionId);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Define paths where the chatbot should be visible
    const qaManagementPaths = ["/projects", "/requirements", "/test-cases", "/defects", "/releases"];
    const isVisible = qaManagementPaths.some(path => location.pathname.startsWith(path));

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    useEffect(() => {
        if (open) setTimeout(() => inputRef.current?.focus(), 100);
    }, [open]);

    if (!isVisible) return null;

    async function sendMessage() {
        const text = input.trim();
        if (!text || loading) return;

        setMessages((prev) => [...prev, { role: "user", text }]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch(N8N_WEBHOOK_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chatInput: text, sessionId }),
            });
            const data = await res.json();
            const reply =
                data?.output ||
                data?.text ||
                data?.message ||
                data?.[0]?.output ||
                "Sorry, I couldn't get a response.";

            setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", text: "⚠️ Connection error. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    }

    function handleKey(e: React.KeyboardEvent) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    return (
        <>
            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

        .cb-root * { box-sizing: border-box; font-family: 'DM Sans', sans-serif; }

        .cb-bubble {
          position: fixed;
          bottom: 28px;
          right: 28px;
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: #0f0f0f;
          border: 1.5px solid #2a2a2a;
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 32px rgba(0,0,0,0.35);
          transition: transform 0.2s ease, box-shadow 0.2s ease;
          z-index: 9999;
        }
        .cb-bubble:hover {
          transform: scale(1.08);
          box-shadow: 0 12px 40px rgba(0,0,0,0.45);
        }
        .cb-bubble svg { transition: transform 0.3s ease; }
        .cb-bubble.open svg { transform: rotate(90deg); }

        .cb-badge {
          position: absolute;
          top: -3px;
          right: -3px;
          width: 14px;
          height: 14px;
          background: #22c55e;
          border-radius: 50%;
          border: 2px solid white;
        }

        .cb-window {
          position: fixed;
          bottom: 96px;
          right: 28px;
          width: 380px;
          height: 560px;
          background: #0a0a0a;
          border: 1px solid #1e1e1e;
          border-radius: 20px;
          display: flex;
          flex-direction: column;
          box-shadow: 0 24px 80px rgba(0,0,0,0.6);
          z-index: 9998;
          overflow: hidden;
          transform-origin: bottom right;
          animation: cb-pop 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        @keyframes cb-pop {
          from { transform: scale(0.85); opacity: 0; }
          to   { transform: scale(1);    opacity: 1; }
        }

        .cb-header {
          padding: 18px 20px 14px;
          border-bottom: 1px solid #1a1a1a;
          display: flex;
          align-items: center;
          gap: 12px;
          background: #0f0f0f;
        }
        .cb-avatar {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
          border: 1px solid #2e2e2e;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
        }
        .cb-header-info { flex: 1; }
        .cb-header-name {
          font-size: 13.5px;
          font-weight: 600;
          color: #f0f0f0;
          letter-spacing: -0.2px;
        }
        .cb-header-status {
          font-size: 11.5px;
          color: #555;
          display: flex;
          align-items: center;
          gap: 5px;
          margin-top: 1px;
        }
        .cb-status-dot {
          width: 6px;
          height: 6px;
          background: #22c55e;
          border-radius: 50%;
        }
        .cb-close {
          background: none;
          border: none;
          color: #444;
          cursor: pointer;
          padding: 4px;
          border-radius: 6px;
          display: flex;
          transition: color 0.15s, background 0.15s;
        }
        .cb-close:hover { color: #aaa; background: #1a1a1a; }

        .cb-messages {
          flex: 1;
          overflow-y: auto;
          padding: 16px 16px 8px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          scrollbar-width: thin;
          scrollbar-color: #222 transparent;
        }
        .cb-messages::-webkit-scrollbar { width: 4px; }
        .cb-messages::-webkit-scrollbar-thumb { background: #222; border-radius: 4px; }

        .cb-msg {
          display: flex;
          flex-direction: column;
          max-width: 86%;
          animation: cb-fade 0.18s ease;
        }
        @keyframes cb-fade {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .cb-msg.user { align-self: flex-end; align-items: flex-end; }
        .cb-msg.assistant { align-self: flex-start; align-items: flex-start; }

        .cb-bubble-text {
          padding: 10px 14px;
          border-radius: 16px;
          font-size: 13.5px;
          line-height: 1.55;
          white-space: pre-wrap;
          word-break: break-word;
        }
        .cb-msg.user .cb-bubble-text {
          background: #f0f0f0;
          color: #0a0a0a;
          border-bottom-right-radius: 4px;
          font-weight: 500;
        }
        .cb-msg.assistant .cb-bubble-text {
          background: #161616;
          color: #d4d4d4;
          border: 1px solid #222;
          border-bottom-left-radius: 4px;
        }

        .cb-typing {
          display: flex;
          gap: 4px;
          align-items: center;
          padding: 12px 14px;
          background: #161616;
          border: 1px solid #222;
          border-radius: 16px;
          border-bottom-left-radius: 4px;
          width: fit-content;
        }
        .cb-typing span {
          width: 6px;
          height: 6px;
          background: #444;
          border-radius: 50%;
          animation: cb-bounce 1.2s infinite;
        }
        .cb-typing span:nth-child(2) { animation-delay: 0.15s; }
        .cb-typing span:nth-child(3) { animation-delay: 0.3s; }
        @keyframes cb-bounce {
          0%, 60%, 100% { transform: translateY(0); background: #444; }
          30% { transform: translateY(-5px); background: #888; }
        }

        .cb-input-area {
          padding: 12px 14px 16px;
          border-top: 1px solid #1a1a1a;
          background: #0f0f0f;
          display: flex;
          gap: 10px;
          align-items: flex-end;
        }
        .cb-input {
          flex: 1;
          background: #161616;
          border: 1px solid #232323;
          border-radius: 12px;
          color: #e8e8e8;
          font-size: 13.5px;
          font-family: 'DM Sans', sans-serif;
          padding: 10px 14px;
          resize: none;
          outline: none;
          min-height: 42px;
          max-height: 100px;
          line-height: 1.5;
          transition: border-color 0.15s;
        }
        .cb-input::placeholder { color: #3a3a3a; }
        .cb-input:focus { border-color: #333; }

        .cb-send {
          width: 38px;
          height: 38px;
          border-radius: 10px;
          background: #f0f0f0;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.15s, transform 0.1s;
          flex-shrink: 0;
        }
        .cb-send:hover:not(:disabled) { background: #fff; transform: scale(1.05); }
        .cb-send:disabled { background: #1e1e1e; cursor: not-allowed; }
        .cb-send:disabled svg path { stroke: #333; }

        .cb-footer {
          text-align: center;
          font-size: 10.5px;
          color: #2e2e2e;
          padding: 0 0 4px;
          font-family: 'DM Mono', monospace;
          letter-spacing: 0.3px;
        }

        @media (max-width: 480px) {
          .cb-window {
            bottom: 0;
            right: 0;
            width: 100vw;
            height: 100dvh;
            border-radius: 0;
          }
          .cb-bubble { bottom: 20px; right: 20px; }
        }
      `}</style>

            <div className="cb-root">
                {/* Chat Window */}
                {open && (
                    <div className="cb-window" role="dialog" aria-label="Chat assistant">
                        {/* Header */}
                        <div className="cb-header">
                            <div className="cb-avatar">🗄️</div>
                            <div className="cb-header-info">
                                <div className="cb-header-name">Data Assistant</div>
                                <div className="cb-header-status">
                                    <div className="cb-status-dot" />
                                    Connected to your database
                                </div>
                            </div>
                            <button className="cb-close" onClick={() => setOpen(false)} aria-label="Close chat">
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="cb-messages">
                            {messages.map((msg, i) => (
                                <div key={i} className={`cb-msg ${msg.role}`}>
                                    <div className="cb-bubble-text">{msg.text}</div>
                                </div>
                            ))}
                            {loading && (
                                <div className="cb-msg assistant">
                                    <div className="cb-typing">
                                        <span /><span /><span />
                                    </div>
                                </div>
                            )}
                            <div ref={bottomRef} />
                        </div>

                        {/* Input */}
                        <div className="cb-input-area">
                            <textarea
                                ref={inputRef}
                                className="cb-input"
                                placeholder="Ask about orders, customers..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKey}
                                rows={1}
                            />
                            <button
                                className="cb-send"
                                onClick={sendMessage}
                                disabled={!input.trim() || loading}
                                aria-label="Send message"
                            >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <path d="M13.5 8H2.5M13.5 8L9 3.5M13.5 8L9 12.5" stroke="#0a0a0a" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        </div>
                        <div className="cb-footer">powered by your postgres db</div>
                    </div>
                )}

                {/* Floating Bubble */}
                <button
                    className={`cb-bubble ${open ? "open" : ""}`}
                    onClick={() => setOpen((v) => !v)}
                    aria-label="Toggle chat"
                >
                    {!open && <div className="cb-badge" />}
                    {open ? (
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                            <path d="M14 4L4 14M4 4l10 10" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
                        </svg>
                    ) : (
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M17 10c0 3.866-3.134 7-7 7a6.973 6.973 0 01-3.5-.937L3 17l.937-3.5A6.973 6.973 0 013 10c0-3.866 3.134-7 7-7s7 3.134 7 7z" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    )}
                </button>
            </div>
        </>
    );
}
