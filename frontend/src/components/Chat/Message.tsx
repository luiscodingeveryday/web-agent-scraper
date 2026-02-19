import { LoadingSpinner } from '../ui/LoadingSpinner';
import type { Message as MessageType } from '../../types';

interface MessageProps {
  message: MessageType;
}

export const Message = ({ message }: MessageProps) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex w-full mb-4 animate-slide-up ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 shadow-md ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
        } ${message.error ? 'border-2 border-red-400' : ''}`}
      >
        {message.isLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            <p className="text-sm md:text-base whitespace-pre-wrap break-words">
              {message.content}
            </p>
            {message.error && (
              <p className="text-xs mt-2 text-red-600 font-medium">
                Error: {message.error}
              </p>
            )}
            <p
              className={`text-xs mt-1 ${
                isUser ? 'text-blue-100' : 'text-gray-400'
              }`}
            >
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </>
        )}
      </div>
    </div>
  );
};