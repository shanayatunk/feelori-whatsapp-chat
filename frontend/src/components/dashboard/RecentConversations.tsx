// frontend/src/components/dashboard/RecentConversations.tsx
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Phone, Clock, TrendingUp } from 'lucide-react';
import { Customer } from '@/types';
import { formatRelativeTime } from '@/lib/utils';

interface RecentConversationsProps {
  customers: Customer[];
}

export const RecentConversations: React.FC<RecentConversationsProps> = ({ customers }) => {
  console.log('RecentConversations customers:', customers);

  // Additional null check
  if (!customers || !Array.isArray(customers)) {
    return <p className="text-center text-white/60 py-8">No recent customer activity.</p>;
  }

  return (
    <div className="lg:col-span-2">
      <Card className="bg-white/5 border-white/10 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {customers.length > 0 ? (
            customers.map((customer) => (
              <div key={customer._id} className="p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-green-400" />
                    <span className="text-white font-medium text-sm">{customer.phone_number}</span>
                  </div>
                  <div className="flex items-center gap-2 text-white/60 text-xs">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(customer.last_interaction)}
                  </div>
                </div>
                <div className="text-white/80 text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                  <span>Total Messages: {customer.total_messages}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-white/60 py-8">No recent customer activity.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};