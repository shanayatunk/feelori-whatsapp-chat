import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  text,
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] space-y-4">
      <Loader2 
        className={cn(
          'animate-spin text-feelori-primary',
          sizeClasses[size],
          className
        )} 
      />
      {text && (
        <p className="text-white/80 text-sm font-medium">{text}</p>
      )}
    </div>
  );
};

// Full screen loading spinner
export const FullScreenSpinner: React.FC<{ text?: string }> = ({ text }) => {
  return (
    <div className="fixed inset-0 bg-gradient-to-br from-feelori-primary via-feelori-primary/80 to-feelori-secondary flex items-center justify-center z-50">
      <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-8">
        <LoadingSpinner size="lg" text={text || 'Loading...'} />
      </div>
    </div>
  );
};