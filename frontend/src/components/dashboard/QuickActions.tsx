import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Send, Loader2 } from 'lucide-react';
import { useSendMessage } from '@/hooks/useApi';
import { useToast } from '@/hooks/useToast';
import { validatePhoneNumber, formatPhoneNumber } from '@/lib/utils';

export const QuickActions: React.FC = () => {
  const [testPhone, setTestPhone] = useState('');
  const [testMessage, setTestMessage] = useState('');
  const { sendMessage, loading: messageLoading } = useSendMessage();
  const { success, error } = useToast();

  const handleSendTestMessage = async () => {
    if (!testPhone || !testMessage) {
      error('Please enter both phone number and message');
      return;
    }

    const formattedPhone = formatPhoneNumber(testPhone);
    if (!validatePhoneNumber(formattedPhone)) {
      error('Please enter a valid phone number with country code (e.g., +1234567890)');
      return;
    }

    try {
      await sendMessage(formattedPhone, testMessage);
      success('Message sent successfully!');
      setTestPhone('');
      setTestMessage('');
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to send message');
    }
  };

  return (
    <div>
      <Card className="card-feelori">
        <CardHeader>
          <CardTitle className="text-white">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <h4 className="text-white font-semibold">Send Test Message</h4>

            <Input
              placeholder="Phone number (e.g., +1234567890)"
              value={testPhone}
              onChange={(e) => setTestPhone(e.target.value)}
              className="input-feelori"
            />

            <Textarea
              placeholder="Test message..."
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              className="input-feelori resize-none"
              rows={3}
            />

            <Button
              onClick={handleSendTestMessage}
              disabled={messageLoading}
              className="w-full btn-feelori"
            >
              {messageLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Send className="w-4 h-4 mr-2" />
              )}
              {messageLoading ? 'Sending...' : 'Send Test Message'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
