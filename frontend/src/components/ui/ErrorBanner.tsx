import { XCircleIcon } from '@heroicons/react/24/outline';

interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
}

export const ErrorBanner = ({ message, onDismiss }: ErrorBannerProps) => {
  return (
    <div className="bg-red-50 border-l-4 border-red-500 p-4 animate-slide-up">
      <div className="flex items-start">
        <XCircleIcon className="h-5 w-5 text-red-500 mt-0.5" />
        <div className="ml-3 flex-1">
          <p className="text-sm text-red-700">{message}</p>
        </div>
        <button
          onClick={onDismiss}
          className="ml-3 text-red-500 hover:text-red-700 transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
};