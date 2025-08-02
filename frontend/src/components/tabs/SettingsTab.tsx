import React, { useState, useEffect } from 'react';
import { Settings, Bot, Database, MessageSquare, Shield, Zap, Save, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useHealthCheck } from '@/hooks/useApi';
import { useToast } from '@/hooks/useToast';
import { HealthStatus } from '@/types';

const SettingsTab: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [settings, setSettings] = useState({
    primaryModel: 'gemini',
    fallbackModel: 'openai',
    responseTimeout: '30',
    autoFallback: true,
    logLevel: 'info',
    rateLimitEnabled: true,
    maintenanceMode: false,
  });

  const { checkHealth, loading: healthLoading } = useHealthCheck();
  const { success, error } = useToast();

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await checkHealth();
        if (response.success && response.data) {
          setHealthStatus(response.data);
        }
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };

    fetchHealth();
  }, [checkHealth]);

  const handleSaveSettings = () => {
    // In a real application, this would send settings to the backend
    success('Settings saved successfully!');
  };

  const handleRefreshHealth = async () => {
    try {
      const response = await checkHealth();
      if (response.success && response.data) {
        setHealthStatus(response.data);
        success('Health status refreshed');
      }
    } catch (err) {
      error('Failed to refresh health status');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap = {
      connected: { color: 'bg-green-500/20 text-green-400 border-green-500/30', text: 'Connected' },
      configured: { color: 'bg-green-500/20 text-green-400 border-green-500/30', text: 'Configured' },
      available: { color: 'bg-green-500/20 text-green-400 border-green-500/30', text: 'Available' },
      not_configured: { color: 'bg-red-500/20 text-red-400 border-red-500/30', text: 'Not Configured' },
      not_available: { color: 'bg-red-500/20 text-red-400 border-red-500/30', text: 'Not Available' },
      error: { color: 'bg-red-500/20 text-red-400 border-red-500/30', text: 'Error' },
    };

    const config = statusMap[status as keyof typeof statusMap] || statusMap.error;
    return <Badge className={config.color}>{config.text}</Badge>;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">Settings</h2>
          <p className="text-white/70">Configure your AI assistant settings</p>
        </div>
        
        <Button
          onClick={handleRefreshHealth}
          disabled={healthLoading}
          variant="outline"
          className="border-white/20 text-white hover:bg-white/10"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${healthLoading ? 'animate-spin' : ''}`} />
          Refresh Status
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WhatsApp Configuration */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              WhatsApp Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white/80">Phone Number ID</Label>
              <Input
                value="658673550670053"
                disabled
                className="input-feelori opacity-60"
              />
            </div>
            
            <div className="flex justify-between items-center">
              <Label className="text-white/80">Webhook Status</Label>
              {healthStatus?.services?.whatsapp && getStatusBadge(healthStatus.services.whatsapp)}
            </div>
            
            <div className="space-y-2">
              <Label className="text-white/80">Verify Token</Label>
              <Input
                value="feelori-verify-token"
                disabled
                className="input-feelori opacity-60"
              />
            </div>
          </CardContent>
        </Card>

        {/* AI Model Settings */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bot className="w-5 h-5" />
              AI Model Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white/80">Primary Model</Label>
              <Select value={settings.primaryModel} onValueChange={(value) => setSettings(prev => ({ ...prev, primaryModel: value }))}>
                <SelectTrigger className="input-feelori">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gemini">Google Gemini</SelectItem>
                  <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white/80">Fallback Model</Label>
              <Select value={settings.fallbackModel} onValueChange={(value) => setSettings(prev => ({ ...prev, fallbackModel: value }))}>
                <SelectTrigger className="input-feelori">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI GPT-4</SelectItem>
                  <SelectItem value="gemini">Google Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label className="text-white/80">AI Models Status</Label>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-white/70 text-sm">Gemini</span>
                  {healthStatus?.services?.ai_models?.gemini && getStatusBadge(healthStatus.services.ai_models.gemini)}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70 text-sm">OpenAI</span>
                  {healthStatus?.services?.ai_models?.openai && getStatusBadge(healthStatus.services.ai_models.openai)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Configuration */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Settings className="w-5 h-5" />
              System Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white/80">Response Timeout (seconds)</Label>
              <Input
                value={settings.responseTimeout}
                onChange={(e) => setSettings(prev => ({ ...prev, responseTimeout: e.target.value }))}
                className="input-feelori"
                type="number"
                min="5"
                max="60"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white/80">Log Level</Label>
              <Select value={settings.logLevel} onValueChange={(value) => setSettings(prev => ({ ...prev, logLevel: value }))}>
                <SelectTrigger className="input-feelori">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="debug">Debug</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-white/80">Auto-Fallback</Label>
                <p className="text-white/60 text-xs">Automatically use fallback model if primary fails</p>
              </div>
              <Switch
                checked={settings.autoFallback}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, autoFallback: checked }))}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-white/80">Rate Limiting</Label>
                <p className="text-white/60 text-xs">Enable API rate limiting protection</p>
              </div>
              <Switch
                checked={settings.rateLimitEnabled}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, rateLimitEnabled: checked }))}
              />
            </div>
          </CardContent>
        </Card>

        {/* Database & Storage */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Database className="w-5 h-5" />
              Database & Storage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <Label className="text-white/80">MongoDB Status</Label>
              {healthStatus?.services?.database && getStatusBadge(healthStatus.services.database)}
            </div>
            
            <div className="space-y-2">
              <Label className="text-white/80">Database URL</Label>
              <Input
                value="mongodb://localhost:27017/feelori_assistant"
                disabled
                className="input-feelori opacity-60"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">Connection Pool</span>
                <span className="text-green-400 text-sm">Active</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">Query Performance</span>
                <span className="text-white text-sm">12ms avg</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Shopify Integration */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Shopify Integration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white/80">Store Domain</Label>
              <Input
                value="feelori.myshopify.com"
                disabled
                className="input-feelori opacity-60"
              />
            </div>
            
            <div className="flex justify-between items-center">
              <Label className="text-white/80">API Status</Label>
              {healthStatus?.services?.shopify && getStatusBadge(healthStatus.services.shopify)}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">API Rate Limit</span>
                <span className="text-yellow-400 text-sm">85% used</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">Last Sync</span>
                <span className="text-white text-sm">5 min ago</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card className="card-feelori">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Security Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-white/80">Admin API Key</Label>
              <Input
                value="feelori-admin-****-****-****"
                disabled
                className="input-feelori opacity-60"
                type="password"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-white/80">Maintenance Mode</Label>
                <p className="text-white/60 text-xs">Temporarily disable the assistant</p>
              </div>
              <Switch
                checked={settings.maintenanceMode}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, maintenanceMode: checked }))}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">SSL Certificate</span>
                <span className="text-green-400 text-sm">Valid</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/80 text-sm">Rate Limiting</span>
                <span className="text-green-400 text-sm">Active</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Save Settings */}
      <div className="flex justify-end">
        <Button onClick={handleSaveSettings} className="btn-feelori">
          <Save className="w-4 h-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  );
};

export default SettingsTab;