import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { ErrorBanner } from '../ui/ErrorBanner';
import { useChat } from '../../hooks/useChat';

export const ChatContainer = () => {
  const { messages, isLoading, error, sendMessage, clearError, messagesEndRef } =
    useChat();

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">🤖</span>
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold text-gray-800">
                Web Agent Scraper
              </h1>
              <p className="text-xs text-gray-500">
                {isLoading ? 'Agent is thinking...' : 'Online'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'
              }`}
            ></div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && <ErrorBanner message={error} onDismiss={clearError} />}

      {/* Messages */}
      <MessageList messages={messages} messagesEndRef={messagesEndRef} />

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};