import React, { useState, useRef, useEffect } from 'react';
import { Send, Plane, User, Bot, Settings, MessageCircle, Users, HelpCircle } from 'lucide-react';

const ReadyFlightChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Welcome to ReadyFlight! ✈️ I'm here to help you with flight bookings, check-ins, and any questions you might have. How can I assist you today?",
      sender: 'bot',
      agent: 'Sky Assistant',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userType, setUserType] = useState('customer');
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          user_type: userType
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      setSessionId(data.session_id);
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        agent: data.agent_type,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment. ✈️",
        sender: 'bot',
        agent: 'System',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    // Convert markdown-style formatting to JSX
    return text.split('\n').map((line, index) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return <div key={index} className="font-bold text-blue-800 mb-1">{line.slice(2, -2)}</div>;
      }
      if (line.startsWith('✅') || line.startsWith('❌') || line.startsWith('🎉')) {
        return <div key={index} className="font-semibold mb-1">{line}</div>;
      }
      return <div key={index} className="mb-1">{line}</div>;
    });
  };

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'Sky Assistant':
        return <User className="w-4 h-4" />;
      case 'FAQ Agent':
        return <HelpCircle className="w-4 h-4" />;
      case 'Staff Control':
        return <Settings className="w-4 h-4" />;
      default:
        return <Bot className="w-4 h-4" />;
    }
  };

  const getAgentColor = (agent) => {
    switch (agent) {
      case 'Sky Assistant':
        return 'bg-blue-100 border-blue-300';
      case 'FAQ Agent':
        return 'bg-green-100 border-green-300';
      case 'Staff Control':
        return 'bg-purple-100 border-purple-300';
      default:
        return 'bg-gray-100 border-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-full">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">ReadyFlight Assistant</h1>
                <p className="text-sm text-gray-600">Your AI-powered travel companion</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-gray-500" />
                <select 
                  value={userType} 
                  onChange={(e) => setUserType(e.target.value)}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="customer">Customer</option>
                  <option value="staff">Staff</option>
                </select>
              </div>
              {sessionId && (
                <div className="text-xs text-gray-500">
                  Session: {sessionId.slice(0, 8)}...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto p-4 h-[calc(100vh-120px)] flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 bg-white rounded-lg shadow-sm p-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-lg p-4 shadow-sm ${
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white ml-8'
                    : `${getAgentColor(message.agent)} mr-8 border`
                }`}
              >
                {message.sender === 'bot' && (
                  <div className="flex items-center space-x-2 mb-2">
                    {getAgentIcon(message.agent)}
                    <span className="text-xs font-semibold text-gray-700">
                      {message.agent}
                    </span>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                )}
                
                <div className={`${message.sender === 'user' ? 'text-white' : 'text-gray-800'}`}>
                  {message.sender === 'bot' ? formatMessage(message.text) : message.text}
                </div>
                
                {message.sender === 'user' && (
                  <div className="text-xs text-blue-100 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 border border-gray-300 rounded-lg p-4 mr-8">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-gray-600">Assistant is typing...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex space-x-3">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask about ${userType === 'staff' ? 'flight management, bookings, or system operations' : 'flights, bookings, policies, or travel help'}...`}
              className="flex-1 resize-none border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="2"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md px-4 py-2 transition-colors duration-200 flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </div>
          
          {/* Quick Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            {userType === 'customer' ? (
              <>
                <button
                  onClick={() => setInputMessage("I'd like to search for flights")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Search Flights
                </button>
                <button
                  onClick={() => setInputMessage("Check my booking status")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Check Booking
                </button>
                <button
                  onClick={() => setInputMessage("What's your baggage policy?")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Baggage Policy
                </button>
                <button
                  onClick={() => setInputMessage("Do you have WiFi on flights?")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  WiFi Info
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setInputMessage("Show all current bookings")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  View Bookings
                </button>
                <button
                  onClick={() => setInputMessage("Flight status overview")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Flight Status
                </button>
                <button
                  onClick={() => setInputMessage("Add a new flight")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Add Flight
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReadyFlightChat;