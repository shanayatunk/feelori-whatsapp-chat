import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Phone, Clock, CheckCircle } from 'lucide-react';
import { RecentMessage } from '@/types';
import { formatRelativeTime } from '@/lib/utils';

interface RecentConversationsProps {
  messages: RecentMessage[];
}

export const RecentConversations: React.FC<RecentConversationsProps> = ({ messages }) => {
  return (
    <div className="lg:col-span-2">
      <Card className="card-feelori">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Recent Conversations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <Phone className="w-4 h-4 text-feelori-primary" />
                  <span className="text-white font-medium text-sm">{message.phone}</span>
                </div>
                <div className="flex items-center gap-2 text-white/60 text-xs">
                  <Clock className="w-3 h-3" />
                  {formatRelativeTime(message.timestamp)}
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-white/90 text-sm">
                  <strong className="text-feelori-accent">Customer:</strong> {message.message}
                </div>
                <div className="text-white/80 text-sm">
                  <strong className="text-green-400">AI:</strong> {message.response}
                </div>
              </div>

              <div className="flex justify-end mt-3">
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  {message.status}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};
