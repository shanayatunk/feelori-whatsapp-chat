// frontend/src/components/dashboard/QuickActions.tsx
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
  import { Textarea } from '@/components/ui/textarea';
  import { Send, Loader2, Zap } from 'lucide-react';
  import { useBroadcastMessage } from '@/hooks/useApi';
  import { useToast } from '@/hooks/useToast';

  export const QuickActions: React.FC = () => {
    const [broadcastMessage, setBroadcastMessage] = useState('');
    const { broadcast, loading } = useBroadcastMessage();
    const { success: showSuccess, error: showError } = useToast();

    const handleBroadcast = async () => {
      if (!broadcastMessage.trim()) {
        showError('Please enter a broadcast message.');
        return;
      }

      try {
        const response = await broadcast(broadcastMessage, 'all');
        if (response.success) {
          showSuccess(`Broadcast sent sent to ${response.data?.sent_count || 0} customers!`);
          setBroadcastMessage('');
        }
      } catch (err: any) {
        showError(err.message || 'Failed to send broadcast.');
      }
    };

    return (
      <div className="lg:col-span-1">
        <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <h4 className="text-white font-semibold">Send Broadcast Message</h4>
            <Textarea
              placeholder="Enter a message to send to all customers..."
              value={broadcastMessage}
              onChange={(e) => setBroadcastMessage(e.target.value)}
              className="bg-white/10 border-white/20 text-white placeholder-white/50 resize-none"
              rows={4}
            />
            <Button
              onClick={handleBroadcast}
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Send className="w-4 h-4 mr-2" />
              )}
              {loading ? 'Sending...' : 'Send Broadcast'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  };