import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { BACKEND_URL, WEBSOCKET_URL } from '../../config/environment';
import './VoiceEngineerPage.css';

interface Message {
  id: string;
  type: 'engineer' | 'user';
  content: string;
  timestamp: Date;
}

interface EngineerContext {
  driverName: string;
  trackName: string;
  currentLap: number;
  position: number;
  gapAhead: number;
  gapBehind: number;
  fuelLevel: number;
  flagStatus: string;
}

const VoiceEngineerPage: React.FC = () => {
  const { token, user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [context, setContext] = useState<EngineerContext | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sessionId = 'live-session'; // In a real app, this would come from the current active session

  const quickCommands = [
    "Gap to leader",
    "Tire status",
    "Weather update",
    "Pit window",
    "Fuel remaining",
    "Best lap",
    "Sector comparison",
    "Strategy update",
  ];

  const recentTopics = [
    { icon: '🛞', text: 'Tire Management' },
    { icon: '⛽', text: 'Fuel Strategy' },
    { icon: '🏁', text: 'Race Position' },
    { icon: '🌡️', text: 'Track Conditions' },
  ];

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Connect WebSocket
  useEffect(() => {
    if (!token) return;

    // Use WS protocol based on config or window location
    const wsUrl = new URL(WEBSOCKET_URL);
    // Ensure we use the voice stream endpoint
    const streamUrl = `${wsUrl.protocol}//${wsUrl.host}/api/voice/stream?sessionId=${sessionId}`;

    console.log('Connecting to Voice WebSocket:', streamUrl);

    // Initialize session first via API to ensure context exists
    const initSession = async () => {
      try {
        await fetch(`${BACKEND_URL}/api/voice/session/init`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            sessionId,
            driverId: user?.id
          })
        });

        // Then connect WS
        connectWebSocket(streamUrl);

        // Load history
        fetchHistory();

      } catch (err) {
        console.error('Failed to init voice session:', err);
      }
    };

    initSession();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, user]);

  const connectWebSocket = (url: string) => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('Voice WebSocket connected');
      setIsConnected(true);

      // Send auth token if needed by your WS implementation, 
      // though typically it's handled via upgrade req cookies or query params
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'engineer_response') {
          const engineerMsg: Message = {
            id: Date.now().toString(),
            type: 'engineer',
            content: data.text,
            timestamp: new Date(data.timestamp || Date.now())
          };
          setMessages(prev => [...prev, engineerMsg]);
          setIsProcessing(false);

          // Play audio if URL provided (not yet in WS message but ready for it)
          if (data.audioUrl) {
            playAudioResponse(data.audioUrl);
          }
        }
        else if (data.type === 'context_update') {
          setContext(data.data);
        }
      } catch (err) {
        console.error('WS Message parse error:', err);
      }
    };

    ws.onclose = () => {
      console.log('Voice WebSocket disconnected');
      setIsConnected(false);
      // Simple reconnect logic could go here
    };

    wsRef.current = ws;
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/history/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.conversationHistory.map((msg: any) => ({
          id: Math.random().toString(),
          type: msg.role === 'user' ? 'user' : 'engineer',
          content: msg.content,
          timestamp: new Date(msg.timestamp)
        })));
        if (data.context) setContext(data.context);
      }
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const playAudioResponse = (url: string) => {
    const audio = new Audio(`${BACKEND_URL}${url}`);
    audio.play().catch(e => console.error('Audio play failed', e));
  };

  const handleSend = useCallback(async () => {
    if (!inputText.trim()) return;

    const textToSend = inputText;
    setInputText('');
    setIsProcessing(true);

    // Optimistic update
    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: textToSend,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      // Send via API (could also send via WS)
      const res = await fetch(`${BACKEND_URL}/api/voice/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          sessionId,
          text: textToSend,
          includeVoice: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        // Response handled via WS or here if we prefer API response
        if (data.engineerResponse) {
          // If WS already handled it, this might duplicate, but usually 
          // WS broadcasts while API returns result. 
          // We can dedupe or just rely on API for the immediate response 
          // and WS for async updates.
          // For now, let's check if we already have it from WS? 
          // Actually, simplest is to NOT add it here if we expect WS. 
          // But let's add it if WS didn't fire yet.

          // Check if last message is this one (rare race condition)
          // Ideally rely on WS for consistency, but for responsiveness:
          const engMsg: Message = {
            id: Date.now().toString(),
            type: 'engineer',
            content: data.engineerResponse,
            timestamp: new Date()
          };

          // Only add if not using WS broadcast for this specific flow
          // or if we want immediate feedback.
          // Let's rely on the API response here as it's the direct result of the POST
          setMessages(prev => [...prev, engMsg]);
          setIsProcessing(false);

          if (data.audioUrl) {
            playAudioResponse(data.audioUrl);
          }
        }
      }
    } catch (err) {
      console.error('Send message failed:', err);
      setIsProcessing(false);
    }
  }, [inputText, token, sessionId]);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioMessage(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Could not access microphone.');
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setIsProcessing(true);
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const sendAudioMessage = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice_command.wav');
    formData.append('sessionId', sessionId);
    formData.append('includeVoice', 'true');

    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (res.ok) {
        const data = await res.json();

        // Add transcribed user message
        if (data.driverMessage) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            type: 'user',
            content: data.driverMessage,
            timestamp: new Date()
          }]);
        }

        // Add engineer response
        if (data.engineerResponse) {
          setMessages(prev => [...prev, {
            id: (Date.now() + 1).toString(),
            type: 'engineer',
            content: data.engineerResponse,
            timestamp: new Date()
          }]);

          if (data.audioUrl) {
            playAudioResponse(data.audioUrl);
          }
        }
      }
    } catch (err) {
      console.error('Failed to send audio:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuickCommand = (cmd: string) => {
    setInputText(cmd);
    // Optional: Auto-send?
    // handleSend(); 
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="voice-engineer-page">
      <div className="voice-header">
        <h1>🎙️ Race Engineer</h1>
        <div className="voice-status">
          <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="indicator"></span>
            {isConnected ? 'Online' : 'Offline'}
          </div>
          <div className={`status-badge ${isListening ? 'listening' : isProcessing ? 'processing' : ''}`} style={{ marginLeft: '10px' }}>
            <span className="indicator"></span>
            {isListening ? 'Listening...' : isProcessing ? 'Processing...' : 'Ready'}
          </div>
        </div>
      </div>

      <div className="voice-content">
        {/* Conversation Panel */}
        <div className="conversation-panel">
          <div className="conversation-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.type}`}>
                <div className="message-avatar">
                  {msg.type === 'engineer' ? '🎧' : '🏎️'}
                </div>
                <div>
                  <div className="message-content">{msg.content}</div>
                  <div className="message-time">{formatTime(msg.timestamp)}</div>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="message engineer">
                <div className="message-avatar">🎧</div>
                <div className="message-content">Analyzing...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="voice-input-area">
            <div className="input-container">
              <input
                type="text"
                className="text-input"
                placeholder="Type a message or use voice..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              />
              <button
                className={`voice-btn mic ${isListening ? 'listening' : ''}`}
                onMouseDown={startListening}
                onMouseUp={stopListening}
              // Also support click toggle for simple usage
              // onClick={handleVoiceToggle} 
              >
                🎤
              </button>
              <button className="send-btn" onClick={handleSend}>
                ➤
              </button>
            </div>
            <div className="mic-hint">Hold to speak</div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="voice-sidebar">
          {/* Engineer Profile */}
          <div className="sidebar-section">
            <div className="engineer-profile">
              <div className="engineer-avatar">🎧</div>
              <div className="engineer-name">Adam</div>
              <div className="engineer-role">Senior Race Engineer</div>
            </div>
          </div>

          {/* Live Context */}
          {context && (
            <div className="sidebar-section">
              <h3>Live Telemetry</h3>
              <div className="session-stats">
                <div className="stat-card">
                  <div className="stat-value">{context.position}</div>
                  <div className="stat-label">Position</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{context.currentLap}</div>
                  <div className="stat-label">Lap</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{context.fuelLevel.toFixed(1)}</div>
                  <div className="stat-label">Fuel (L)</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ color: context.flagStatus === 'green' ? '#4CAF50' : 'orange' }}>
                    {context.flagStatus.toUpperCase()}
                  </div>
                  <div className="stat-label">Flag</div>
                </div>
              </div>
            </div>
          )}

          {/* Quick Commands */}
          <div className="sidebar-section">
            <h3>Quick Commands</h3>
            <div className="quick-commands">
              {quickCommands.map((cmd) => (
                <button
                  key={cmd}
                  className="quick-cmd"
                  onClick={() => handleQuickCommand(cmd)}
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>

          {/* Recent Topics */}
          <div className="sidebar-section">
            <h3>Recent Topics</h3>
            <div className="recent-topics">
              {recentTopics.map((topic, i) => (
                <div key={i} className="topic-item">
                  <span className="topic-icon">{topic.icon}</span>
                  <span>{topic.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceEngineerPage;
