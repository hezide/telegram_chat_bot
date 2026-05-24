import { useState, useEffect, useRef } from "react";
import "./index.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [participantConnected, setParticipantConnected] = useState(false);
  const [noChat, setNoChat] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const eventSource = new EventSource("/api/stream");

    eventSource.onerror = () => setParticipantConnected(false);

    eventSource.addEventListener("message", (e) => {
      const data = JSON.parse(e.data);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          text: data.text,
          timestamp: new Date().toISOString(),
          direction: data.sender === "user" ? "outgoing" : "incoming",
        },
      ]);
    });

    eventSource.addEventListener("system", (e) => {
      const data = JSON.parse(e.data);
      setNoChat(false);
      if (data.text.includes("connected")) setParticipantConnected(true);
      if (data.text.includes("disconnected")) setParticipantConnected(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          text: data.text,
          timestamp: new Date().toISOString(),
          direction: "system",
        },
      ]);
    });

    return () => eventSource.close();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const text = input;
    setInput("");

    try {
      const res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (res.status === 409) {
        setNoChat(true);
      } else {
        setNoChat(false);
      }
    } catch {
      setNoChat(true);
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        <header className="chat-header">
          <h2>Telegram Chat</h2>
          <span className={`status-dot ${participantConnected ? "connected" : ""}`} />
        </header>

        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.direction}`}>
              {msg.direction === "system" ? (
                <div className="chat-system-text">{msg.text}</div>
              ) : (
                <div className="chat-bubble">
                  <div className="chat-text">{msg.text}</div>
                  <div className="chat-timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {noChat && (
          <div className="chat-banner">
            No active chat — ask the participant to send /start
          </div>
        )}

        <div className="chat-input">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
