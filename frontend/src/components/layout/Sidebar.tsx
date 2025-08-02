import React from 'react';
import { BarChart3, ShoppingBag, TrendingUp, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TabType } from '@/types';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const navigationItems = [
  {
    id: 'dashboard' as TabType,
    label: 'Dashboard',
    icon: BarChart3,
  },
  {
    id: 'products' as TabType,
    label: 'Products',
    icon: ShoppingBag,
  },
  {
    id: 'analytics' as TabType,
    label: 'Analytics',
    icon: TrendingUp,
  },
  {
    id: 'settings' as TabType,
    label: 'Settings',
    icon: Settings,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="w-80 bg-white/10 backdrop-blur-lg border-r border-white/20">
      <div className="p-6">
        {/* Logo */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white">
              Feelori AI
            </h2>
            <span className="text-sm text-white/60 bg-white/10 px-2 py-1 rounded-md">
              v2.0
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200',
                  'hover:bg-white/10 hover:transform hover:translate-x-1',
                  isActive
                    ? 'bg-feelori-primary text-white shadow-lg'
                    : 'text-white/80 hover:text-white'
                )}
              >
                <Icon size={20} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};