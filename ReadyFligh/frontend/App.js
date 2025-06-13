import React, { useState, useRef, useEffect } from 'react';
import { Send, Plane, Users, HelpCircle, Settings, MessageCircle, Loader2 } from 'lucide-react';

const ReadyFlightApp = () => {
  const [activeTab, setActiveTab] = useState('customer');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState('');
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
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Simulate API call to your FastAPI backend
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          user_type: activeTab
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.response,
        agent: data.agent_type,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
      setCurrentAgent(data.agent_type);
    } catch (error) {
      // Fallback demo response
      const demoResponses = {
        customer: {
          'Sky Assistant': "✈️ Hello! I'm Sky Assistant, your friendly customer service representative! I can help you with flight bookings, check your reservations, or make changes to your travel plans. What can I do for you today? 😊",
          'FAQ Agent': "📋 Hi there! I'm your FAQ specialist and I'm here to help with questions about ReadyFlight policies, services, and general information. Whether you need to know about baggage policies, Wi-Fi, meals, or check-in procedures, I've got you covered! 🛫"
        },
        staff: {
          'Staff Control': "👨‍💼 Welcome to Staff Control! I'm your operations manager with access to flight management and booking systems. I can help you add flights, update information, view bookings, and provide operational insights. How can I assist you today?",
          'FAQ Agent': "📋 Hello staff member! I can help you with airline policy information, flight schedules, and general service details. What information do you need? 🛫"
        }
      };

      const agents = Object.keys(demoResponses[activeTab]);
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: demoResponses[activeTab][randomAgent],
        agent: randomAgent,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
      setCurrentAgent(randomAgent);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setCurrentAgent('');
  };

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'Sky Assistant':
        return <Users className="w-4 h-4" />;
      case 'FAQ Agent':
        return <HelpCircle className="w-4 h-4" />;
      case 'Staff Control':
        return <Settings className="w-4 h-4" />;
      default:
        return <MessageCircle className="w-4 h-4" />;
    }
  };

  const getTabContent = () => {
    if (activeTab === 'customer') {
      return {
        title: 'Customer Support',
        subtitle: 'Book flights, check reservations, get travel assistance',
        agents: ['Sky Assistant', 'FAQ Agent'],
        color: 'from-blue-500 to-cyan-500',
        examples: [
          'I want to book a flight from New York to Los Angeles',
          'Check my booking RF12345',
          'What is your baggage policy?',
          'Show me flight schedules'
        ]
      };
    } else {
      return {
        title: 'Staff Operations',
        subtitle: 'Manage flights, view bookings, operational controls',
        agents: ['Staff Control', 'FAQ Agent'],
        color: 'from-purple-500 to-indigo-500',
        examples: [
          'Add a new flight RF001 from Chicago to Miami',
          'View all current bookings',
          'Update flight RF002 departure time',
          'Show flight status overview'
        ]
      };
    }
  };

  const tabContent = getTabContent();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-lg border-b">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-2 rounded-xl">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">ReadyFlight</h1>
                <p className="text-sm text-gray-600">AI Assistant</p>
              </div>
            </div>
            
            {/* Tab Switcher */}
            <div className="flex bg-gray-100 rounded-xl p-1">
              <button
                onClick={() => {
                  setActiveTab('customer');
                  clearChat();
                }}
                className={`px-6 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'customer'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-blue-600'
                }`}
              >
                <Users className="w-4 h-4 inline mr-2" />
                Customer
              </button>
              <button
                onClick={() => {
                  setActiveTab('staff');
                  clearChat();
                }}
                className={`px-6 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'staff'
                    ? 'bg-white text-purple-600 shadow-sm'
                    : 'text-gray-600 hover:text-purple-600'
                }`}
              >
                <Settings className="w-4 h-4 inline mr-2" />
                Staff
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Tab Content Header */}
        <div className={`bg-gradient-to-r ${tabContent.color} rounded-2xl p-6 mb-6 text-white`}>
          <h2 className="text-2xl font-bold mb-2">{tabContent.title}</h2>
          <p className="text-white/90 mb-4">{tabContent.subtitle}</p>
          <div className="flex flex-wrap gap-2">
            {tabContent.agents.map((agent) => (
              <div key={agent} className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full flex items-center space-x-1">
                {getAgentIcon(agent)}
                <span className="text-sm font-medium">{agent}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl overflow-hidden">
            {/* Chat Header */}
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 border-b">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MessageCircle className="w-5 h-5 text-gray-600" />
                  <span className="font-semibold text-gray-700">
                    {currentAgent || 'Chat Assistant'}
                  </span>
                </div>
                <button
                  onClick={clearChat}
                  className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Clear Chat
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="h-96 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <div className={`bg-gradient-to-r ${tabContent.color} w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4`}>
                    <Plane className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    Welcome to {tabContent.title}!
                  </h3>
                  <p className="text-gray-500 mb-4">
                    Start a conversation with our AI assistants
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                      message.type === 'user'
                        ? `bg-gradient-to-r ${tabContent.color} text-white`
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {message.type === 'bot' && message.agent && (
                      <div className="flex items-center space-x-1 mb-2 text-xs opacity-75">
                        {getAgentIcon(message.agent)}
                        <span>{message.agent}</span>
                      </div>
                    )}
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className={`text-xs mt-2 ${
                      message.type === 'user' ? 'text-white/70' : 'text-gray-500'
                    }`}>
                      {message.timestamp}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 px-4 py-3 rounded-2xl flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Assistant is typing...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t bg-gray-50">
              <div className="flex space-x-2">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="1"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isLoading}
                  className={`bg-gradient-to-r ${tabContent.color} text-white p-3 rounded-xl hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none`}
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
                <HelpCircle className="w-5 h-5 mr-2" />
                Quick Examples
              </h3>
              <div className="space-y-2">
                {tabContent.examples.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(example)}
                    className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors text-sm text-gray-700 hover:text-gray-900"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            {/* Agent Info */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-semibold text-gray-800 mb-4">Available Agents</h3>
              <div className="space-y-3">
                {tabContent.agents.map((agent) => (
                  <div key={agent} className="flex items-center space-x-3 p-3 rounded-lg bg-gray-50">
                    <div className={`bg-gradient-to-r ${tabContent.color} p-2 rounded-lg`}>
                      {getAgentIcon(agent)}
                    </div>
                    <div>
                      <div className="font-medium text-gray-800">{agent}</div>
                      <div className="text-xs text-gray-500">
                        {agent === 'Sky Assistant' && 'Bookings & Travel Help'}
                        {agent === 'FAQ Agent' && 'Policies & Information'}
                        {agent === 'Staff Control' && 'Flight Management'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-semibold text-gray-800 mb-4">System Status</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API Status</span>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-green-600">Online</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AI Agents</span>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-green-600">Active</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Database</span>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-green-600">Connected</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReadyFlightApp;