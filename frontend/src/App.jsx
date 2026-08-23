import { useState } from "react";
import {
  Bot,
  ChevronDown,
  CircleHelp,
  FileText,
  Package,
  Send,
  ShieldCheck,
  Ticket,
  UserRound,
  Zap,
} from "lucide-react";
import "./App.css";

const quickActions = [
  {
    icon: Package,
    title: "Order Status",
    description: "Check shipment information",
    prompt: "What is the status of order ORD-2002?",
  },
  {
    icon: ShieldCheck,
    title: "Service Credits",
    description: "Check credit eligibility",
    prompt:
      "Is LumenWorks eligible for a service credit for ORD-2002?",
  },
  {
    icon: Ticket,
    title: "Support Tickets",
    description: "Review support issues",
    prompt: "Show me the support ticket for ORD-2002.",
  },
  {
    icon: FileText,
    title: "Policies",
    description: "Search ParcelPilot policies",
    prompt: "What is the service credit policy?",
  },
];

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text = message) => {
    const trimmed = text.trim();

    if (!trimmed || loading) return;

    // Add user message immediately
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: trimmed,
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(
        "https://parcelpilot-ai-agent-0u4s.onrender.com/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: trimmed,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      // Add real agent response
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            data.answer || "The agent did not return an answer.",
          activity: data.activity || [],
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't connect to the ParcelPilot backend. Please try again in a moment.",
          activity: [],
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const useQuickAction = (prompt) => {
    sendMessage(prompt);
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-icon">
              <Zap size={19} />
            </div>

            <div>
              <h1>ParcelPilot</h1>
              <span>AI Support Agent</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="navigation">
            <button className="nav-item active">
              <Bot size={18} />
              Support Chat
            </button>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="agent-status">
            <div className="status-dot" />

            <div>
              <strong>Agent Online</strong>
              <span>Ready to assist</span>
            </div>
          </div>

          <div className="profile">
            <div className="profile-avatar">
              <UserRound size={17} />
            </div>

            <div className="profile-info">
              <strong>Support Agent</strong>
              <span>AI Assistant</span>
            </div>

            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        {/* Header */}
        <header className="topbar">
          <div>
            <h2>ParcelPilot Support</h2>
            <p>
              AI-powered customer support and operations assistant
            </p>
          </div>

          <div className="model-badge">
            <span className="online-dot" />
            Gemini · Agent Online
          </div>
        </header>

        {/* Chat */}
        <section className="chat-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="hero-icon">
                <Bot size={30} />
              </div>

              <h3>How can I help?</h3>

              <p>
                Ask ParcelPilot about orders, customers, policies,
                service credits, or support tickets.
              </p>

              <div className="quick-actions">
                {quickActions.map((action) => {
                  const Icon = action.icon;

                  return (
                    <button
                      key={action.title}
                      className="quick-card"
                      onClick={() =>
                        useQuickAction(action.prompt)
                      }
                      disabled={loading}
                    >
                      <div className="quick-icon">
                        <Icon size={18} />
                      </div>

                      <div>
                        <strong>{action.title}</strong>
                        <span>{action.description}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="conversation">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message-row ${
                    msg.role === "user"
                      ? "user-row"
                      : "assistant-row"
                  }`}
                >
                  {msg.role === "assistant" && (
                    <div className="message-avatar">
                      <Bot size={17} />
                    </div>
                  )}

                  <div
                    className={`message ${
                      msg.role === "user"
                        ? "user-message"
                        : "assistant-message"
                    }`}
                  >
                    <p>{msg.content}</p>

                    {msg.role === "assistant" &&
                      msg.activity &&
                      msg.activity.length > 0 && (
                        <div className="agent-activity">
                          <div className="activity-header">
                            <Zap size={14} />
                            <strong>Agent Activity</strong>
                          </div>

                          {msg.activity.map(
                            (activity, activityIndex) => (
                              <div
                                className="activity-item"
                                key={activityIndex}
                              >
                                <span>✓</span>
                                Used {activity.tool}
                              </div>
                            )
                          )}
                        </div>
                      )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row assistant-row">
                  <div className="message-avatar">
                    <Bot size={17} />
                  </div>

                  <div className="message assistant-message">
                    <p className="thinking">
                      ParcelPilot is investigating...
                    </p>

                    <div className="agent-activity">
                      <div className="activity-header">
                        <Zap size={14} />
                        <strong>Agent Activity</strong>
                      </div>

                      <div className="activity-item">
                        <span>•</span>
                        Querying support agent
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Input */}
        <div className="composer-wrapper">
          <div className="composer">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Ask about an order, customer, policy, or ticket..."
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={() => sendMessage()}
              disabled={!message.trim() || loading}
            >
              <Send size={18} />
            </button>
          </div>

          <div className="composer-footer">
            <span>
              <CircleHelp size={13} />
              AI responses may require verification
            </span>

            <span>ParcelPilot AI</span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;