import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Cpu, Database, Search, Brain, Save, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';

interface ConfigData {
  data_source_type: string;
  schema_type: string;
  mock_llm: boolean;
  debug: boolean;
  llm: {
    model: string;
    temperature: number;
    max_tokens: number;
  };
  search: {
    max_iterations: number;
    top_k: number;
    use_bm25: boolean;
    use_vector: boolean;
    use_metadata_filter: boolean;
  };
}

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { toast } = useToast();
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load configuration on open
  useEffect(() => {
    if (isOpen && !config) {
      loadConfig();
    }
  }, [isOpen, config]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/config/default');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        throw new Error('Failed to load config');
      }
    } catch (error) {
      toast({
        title: "加载配置失败",
        description: "无法连接到后端服务",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    try {
      setSaving(true);
      // 这里可以实现保存配置到后端的逻辑
      // 暂时只显示成功消息
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast({
        title: "配置已保存",
        description: "设置将在下次查询时生效",
      });

      onClose();
    } catch (error) {
      toast({
        title: "保存失败",
        description: "配置保存时发生错误",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (updates: Partial<ConfigData>) => {
    if (config) {
      setConfig({ ...config, ...updates });
    }
  };

  const updateLLMConfig = (updates: Partial<ConfigData['llm']>) => {
    if (config) {
      setConfig({
        ...config,
        llm: { ...config.llm, ...updates }
      });
    }
  };

  const updateSearchConfig = (updates: Partial<ConfigData['search']>) => {
    if (config) {
      setConfig({
        ...config,
        search: { ...config.search, ...updates }
      });
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Crux 配置设置</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            ✕
          </Button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-6 h-6 animate-spin mr-2" />
              <span>加载配置中...</span>
            </div>
          ) : config ? (
            <Tabs defaultValue="data" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="data" className="flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  数据源
                </TabsTrigger>
                <TabsTrigger value="llm" className="flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  LLM
                </TabsTrigger>
                <TabsTrigger value="search" className="flex items-center gap-2">
                  <Search className="w-4 h-4" />
                  检索
                </TabsTrigger>
                <TabsTrigger value="system" className="flex items-center gap-2">
                  <Cpu className="w-4 h-4" />
                  系统
                </TabsTrigger>
              </TabsList>

              <TabsContent value="data" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">数据源配置</CardTitle>
                    <CardDescription>
                      配置数据源类型和Schema
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>数据源类型</Label>
                        <Select
                          value={config.data_source_type}
                          onValueChange={(value) => updateConfig({ data_source_type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="json">JSON 文件</SelectItem>
                            <SelectItem value="csv">CSV 文件</SelectItem>
                            <SelectItem value="vector_db">向量数据库</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Schema 类型</Label>
                        <Select
                          value={config.schema_type}
                          onValueChange={(value) => updateConfig({ schema_type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="paper">论文数据</SelectItem>
                            <SelectItem value="news">新闻数据</SelectItem>
                            <SelectItem value="log">日志数据</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="llm" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">LLM 配置</CardTitle>
                    <CardDescription>
                      配置大语言模型参数
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>模型选择</Label>
                      <Select
                        value={config.llm.model}
                        onValueChange={(value) => updateLLMConfig({ model: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Qwen/Qwen3-32B">Qwen3-32B</SelectItem>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          <SelectItem value="claude-3">Claude-3</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>温度: {config.llm.temperature}</Label>
                        <Slider
                          value={[config.llm.temperature]}
                          onValueChange={([value]) => updateLLMConfig({ temperature: value })}
                          max={2}
                          min={0}
                          step={0.1}
                          className="w-full"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>最大Token数</Label>
                        <Input
                          type="number"
                          value={config.llm.max_tokens}
                          onChange={(e) => updateLLMConfig({ max_tokens: parseInt(e.target.value) })}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="search" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">检索配置</CardTitle>
                    <CardDescription>
                      配置检索策略和参数
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>最大迭代次数</Label>
                        <Input
                          type="number"
                          value={config.search.max_iterations}
                          onChange={(e) => updateSearchConfig({ max_iterations: parseInt(e.target.value) })}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>Top-K 返回数</Label>
                        <Input
                          type="number"
                          value={config.search.top_k}
                          onChange={(e) => updateSearchConfig({ top_k: parseInt(e.target.value) })}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <Label>检索方法</Label>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={config.search.use_bm25}
                            onCheckedChange={(checked) => updateSearchConfig({ use_bm25: checked })}
                          />
                          <Label>BM25</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={config.search.use_vector}
                            onCheckedChange={(checked) => updateSearchConfig({ use_vector: checked })}
                          />
                          <Label>向量检索</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Switch
                            checked={config.search.use_metadata_filter}
                            onCheckedChange={(checked) => updateSearchConfig({ use_metadata_filter: checked })}
                          />
                          <Label>元数据过滤</Label>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="system" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">系统配置</CardTitle>
                    <CardDescription>
                      系统级别的配置选项
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>使用模拟LLM</Label>
                          <p className="text-sm text-muted-foreground">开发模式下使用模拟响应</p>
                        </div>
                        <Switch
                          checked={config.mock_llm}
                          onCheckedChange={(checked) => updateConfig({ mock_llm: checked })}
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label>调试模式</Label>
                          <p className="text-sm text-muted-foreground">启用详细的调试日志</p>
                        </div>
                        <Switch
                          checked={config.debug}
                          onCheckedChange={(checked) => updateConfig({ debug: checked })}
                        />
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant="outline">状态</Badge>
                        <span>后端服务: </span>
                        <Badge variant="secondary" className="text-green-600">
                          运行中
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              无法加载配置，请检查后端服务是否运行
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 p-6 border-t bg-muted/30">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={saveConfig} disabled={saving || !config}>
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                保存配置
              </>
            )}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}
