// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import { 
  Home, 
  ShoppingBag, 
  BarChart3, 
  Settings, 
  LogOut,
  User,
  Menu,
  X
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { TabType } from '@/types';
import { cn } from '@/lib/utils';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
}

const navigation = [
  {
    id: 'dashboard' as TabType,
    name: 'Dashboard',
    icon: Home,
    description: 'Overview and metrics'
  },
  {
    id: 'products' as TabType,
    name: 'Products',
    icon: ShoppingBag,
    description: 'Shopify products'
  },
  {
    id: 'analytics' as TabType,
    name: 'Analytics',
    icon: BarChart3,
    description: 'Performance insights'
  },
  {
    id: 'settings' as TabType,
    name: 'Settings',
    icon: Settings,
    description: 'System configuration'
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeTab, 
  onTabChange, 
  collapsed = false,
  onToggleCollapsed 
}) => {
  const { logout } = useAuth();

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to logout?')) {
      await logout();
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {!collapsed && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onToggleCollapsed}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed left-0 top-0 h-full bg-white/10 backdrop-blur-lg border-r border-white/20 transition-all duration-300 z-50",
        collapsed ? "w-20" : "w-72",
        "lg:relative lg:translate-x-0",
        collapsed && "translate-x-0",
        !collapsed && "translate-x-0 lg:translate-x-0"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center justify-between">
              {!collapsed && (
                <div>
                  <h1 className="text-xl font-bold text-white">Feelori</h1>
                  <p className="text-white/60 text-sm">AI Assistant</p>
                </div>
              )}
              
              {onToggleCollapsed && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggleCollapsed}
                  className="text-white/60 hover:text-white lg:hidden"
                >
                  {collapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
                </Button>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;

              return (
                <Button
                  key={item.id}
                  variant="ghost"
                  className={cn(
                    "w-full justify-start h-auto p-4 text-left transition-all duration-200",
                    isActive 
                      ? "bg-white/20 text-white shadow-lg" 
                      : "text-white/70 hover:text-white hover:bg-white/10",
                    collapsed && "px-2"
                  )}
                  onClick={() => onTabChange(item.id)}
                >
                  <Icon className={cn("flex-shrink-0", collapsed ? "w-6 h-6" : "w-5 h-5 mr-3")} />
                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{item.name}</div>
                      <div className="text-xs text-white/50 truncate">
                        {item.description}
                      </div>
                    </div>
                  )}
                  
                  {isActive && !collapsed && (
                    <div className="w-2 h-2 bg-feelori-primary rounded-full flex-shrink-0" />
                  )}
                </Button>
              );
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-white/10">
            <Card className="bg-white/5 border-white/10 p-4">
              <div className={cn("flex items-center", collapsed ? "justify-center" : "gap-3")}>
                <div className="w-8 h-8 bg-feelori-primary rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                
                {!collapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-medium text-sm">Admin</div>
                    <div className="text-white/60 text-xs">System Administrator</div>
                  </div>
                )}
              </div>

              {!collapsed && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-3 text-white/70 hover:text-white"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              )}
            </Card>

            {collapsed && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full mt-2 text-white/70 hover:text-white px-2"
                onClick={handleLogout}
              >
                <LogOut className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};