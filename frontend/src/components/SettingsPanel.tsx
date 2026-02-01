import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  Cpu,
  Database,
  Search,
  Brain,
  Save,
  RefreshCw,
  Gavel,
  FileJson,
  Info,
  CheckCircle2
} from 'lucide-react';
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ConfigData {
  data_source_type: string;
  data_source_path: string;  // 数据文件路径
  schema_path: string;       // YAML schema 配置文件路径（兼容旧模式）
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
  judge?: {
    use_parallel: boolean;
    max_retry: number;
    max_workers: number;
    batch_size: number;
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
        // 确保 judge 配置存在
        if (!data.judge) {
          data.judge = {
            use_parallel: true,
            max_retry: 5,
            max_workers: 4,
            batch_size: 4,
          };
        }
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
      // TODO: 实现保存配置到后端的逻辑
      await new Promise(resolve => setTimeout(resolve, 800));

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

  const updateJudgeConfig = (updates: Partial<NonNullable<ConfigData['judge']>>) => {
    if (config) {
      setConfig({
        ...config,
        judge: { ...(config.judge || { use_parallel: true, max_retry: 5, max_workers: 4, batch_size: 4 }), ...updates }
      });
    }
  };

  if (!isOpen) return null;

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="bg-background rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden border"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-primary/5 to-transparent">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Settings className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Crux 配置设置</h2>
                <p className="text-sm text-muted-foreground">配置来自 config.yaml</p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full">
              ✕
            </Button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <RefreshCw className="w-8 h-8 animate-spin text-primary" />
                <span className="text-muted-foreground">加载配置中...</span>
              </div>
            ) : config ? (
              <Tabs defaultValue="data" className="space-y-6">
                <TabsList className="grid w-full grid-cols-5 h-12">
                  <TabsTrigger value="data" className="flex items-center gap-2 text-sm">
                    <Database className="w-4 h-4" />
                    <span className="hidden sm:inline">数据源</span>
                  </TabsTrigger>
                  <TabsTrigger value="llm" className="flex items-center gap-2 text-sm">
                    <Brain className="w-4 h-4" />
                    <span className="hidden sm:inline">LLM</span>
                  </TabsTrigger>
                  <TabsTrigger value="search" className="flex items-center gap-2 text-sm">
                    <Search className="w-4 h-4" />
                    <span className="hidden sm:inline">检索</span>
                  </TabsTrigger>
                  <TabsTrigger value="judge" className="flex items-center gap-2 text-sm">
                    <Gavel className="w-4 h-4" />
                    <span className="hidden sm:inline">研判</span>
                  </TabsTrigger>
                  <TabsTrigger value="system" className="flex items-center gap-2 text-sm">
                    <Cpu className="w-4 h-4" />
                    <span className="hidden sm:inline">系统</span>
                  </TabsTrigger>
                </TabsList>

                {/* 数据源配置 */}
                <TabsContent value="data" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-4">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Database className="w-5 h-5 text-primary" />
                        数据源配置
                      </CardTitle>
                      <CardDescription>
                        配置数据源类型、文件路径和Schema结构
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label className="flex items-center gap-2">
                            数据源类型
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="w-3.5 h-3.5 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>选择数据来源的格式类型</p>
                              </TooltipContent>
                            </Tooltip>
                          </Label>
                          <Select
                            value={config.data_source_type}
                            onValueChange={(value) => updateConfig({ data_source_type: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="json">
                                <span className="flex items-center gap-2">
                                  <FileJson className="w-4 h-4" />
                                  JSON 文件
                                </span>
                              </SelectItem>
                              <SelectItem value="csv">CSV 文件</SelectItem>
                              <SelectItem value="milvus">Milvus 向量库</SelectItem>
                              <SelectItem value="qdrant">Qdrant 向量库</SelectItem>
                              <SelectItem value="es">Elasticsearch</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label className="flex items-center gap-2">
                            数据文件路径
                            <Tooltip>
                              <TooltipTrigger>
                                <Info className="w-3.5 h-3.5 text-muted-foreground" />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>支持相对路径（相对于项目根目录）或绝对路径</p>
                              </TooltipContent>
                            </Tooltip>
                          </Label>
                          <Input
                            placeholder="data/ir_papers.json"
                            value={config.data_source_path || ''}
                            onChange={(e) => updateConfig({ data_source_path: e.target.value })}
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                          Schema 配置路径
                          <Badge variant="secondary" className="text-xs">可选</Badge>
                        </Label>
                        <Input
                          placeholder="留空将使用 config.yaml 中内嵌的 schema"
                          value={config.schema_path || ''}
                          onChange={(e) => updateConfig({ schema_path: e.target.value })}
                        />
                        <p className="text-xs text-muted-foreground">
                          独立的 YAML Schema 文件路径，留空则使用 config.yaml 内的 schema 配置
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* LLM 配置 */}
                <TabsContent value="llm" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-4">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Brain className="w-5 h-5 text-primary" />
                        LLM 配置
                      </CardTitle>
                      <CardDescription>
                        配置大语言模型参数，API密钥在 config.yaml 或环境变量中设置
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
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
                            <SelectItem value="Qwen/Qwen3-32B">
                              <span className="flex items-center gap-2">
                                Qwen3-32B
                                <Badge variant="secondary" className="text-xs">推荐</Badge>
                              </span>
                            </SelectItem>
                            <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                            <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                            <SelectItem value="deepseek-chat">DeepSeek Chat</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label>生成温度</Label>
                            <Badge variant="outline">{config.llm.temperature.toFixed(1)}</Badge>
                          </div>
                          <Slider
                            value={[config.llm.temperature]}
                            onValueChange={([value]) => updateLLMConfig({ temperature: value })}
                            max={2}
                            min={0}
                            step={0.1}
                            className="w-full"
                          />
                          <p className="text-xs text-muted-foreground">
                            较低值更精确，较高值更有创意
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>最大 Token 数</Label>
                          <Input
                            type="number"
                            value={config.llm.max_tokens}
                            onChange={(e) => updateLLMConfig({ max_tokens: parseInt(e.target.value) || 4096 })}
                          />
                          <p className="text-xs text-muted-foreground">
                            单次生成的最大 Token 限制
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 检索配置 */}
                <TabsContent value="search" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-4">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Search className="w-5 h-5 text-primary" />
                        检索配置
                      </CardTitle>
                      <CardDescription>
                        配置检索策略和参数
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label>最大迭代次数</Label>
                            <Badge variant="outline">{config.search.max_iterations}</Badge>
                          </div>
                          <Slider
                            value={[config.search.max_iterations]}
                            onValueChange={([value]) => updateSearchConfig({ max_iterations: value })}
                            max={10}
                            min={1}
                            step={1}
                            className="w-full"
                          />
                          <p className="text-xs text-muted-foreground">
                            检索→研判→分析的最大循环次数
                          </p>
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label>Top-K 返回数</Label>
                            <Badge variant="outline">{config.search.top_k}</Badge>
                          </div>
                          <Slider
                            value={[config.search.top_k]}
                            onValueChange={([value]) => updateSearchConfig({ top_k: value })}
                            max={20}
                            min={1}
                            step={1}
                            className="w-full"
                          />
                          <p className="text-xs text-muted-foreground">
                            每次检索返回的文档数量
                          </p>
                        </div>
                      </div>

                      <div className="space-y-4 pt-2">
                        <Label>检索方法</Label>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                            <div className="space-y-0.5">
                              <Label className="cursor-pointer">BM25 稀疏检索</Label>
                              <p className="text-xs text-muted-foreground">关键词匹配</p>
                            </div>
                            <Switch
                              checked={config.search.use_bm25}
                              onCheckedChange={(checked) => updateSearchConfig({ use_bm25: checked })}
                            />
                          </div>
                          <div className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                            <div className="space-y-0.5">
                              <Label className="cursor-pointer">向量检索</Label>
                              <p className="text-xs text-muted-foreground">语义相似度</p>
                            </div>
                            <Switch
                              checked={config.search.use_vector}
                              onCheckedChange={(checked) => updateSearchConfig({ use_vector: checked })}
                            />
                          </div>
                          <div className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
                            <div className="space-y-0.5">
                              <Label className="cursor-pointer">元数据过滤</Label>
                              <p className="text-xs text-muted-foreground">时间/作者等</p>
                            </div>
                            <Switch
                              checked={config.search.use_metadata_filter}
                              onCheckedChange={(checked) => updateSearchConfig({ use_metadata_filter: checked })}
                            />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 研判配置 */}
                <TabsContent value="judge" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-4">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Gavel className="w-5 h-5 text-primary" />
                        研判配置
                      </CardTitle>
                      <CardDescription>
                        配置深度研判模块的执行参数
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                        <div className="space-y-0.5">
                          <Label className="text-base">并行研判</Label>
                          <p className="text-sm text-muted-foreground">
                            启用后将并发处理多个文档，提高研判速度
                          </p>
                        </div>
                        <Switch
                          checked={config.judge?.use_parallel ?? true}
                          onCheckedChange={(checked) => updateJudgeConfig({ use_parallel: checked })}
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                          <Label>最大重试次数</Label>
                          <Input
                            type="number"
                            value={config.judge?.max_retry ?? 5}
                            onChange={(e) => updateJudgeConfig({ max_retry: parseInt(e.target.value) || 5 })}
                          />
                          <p className="text-xs text-muted-foreground">
                            LLM 调用失败时的重试次数
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>并行工作线程</Label>
                          <Input
                            type="number"
                            value={config.judge?.max_workers ?? 4}
                            onChange={(e) => updateJudgeConfig({ max_workers: parseInt(e.target.value) || 4 })}
                          />
                          <p className="text-xs text-muted-foreground">
                            并行处理的最大线程数
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>批处理大小</Label>
                          <Input
                            type="number"
                            value={config.judge?.batch_size ?? 4}
                            onChange={(e) => updateJudgeConfig({ batch_size: parseInt(e.target.value) || 4 })}
                          />
                          <p className="text-xs text-muted-foreground">
                            每批处理的文档数量
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 系统配置 */}
                <TabsContent value="system" className="space-y-4">
                  <Card>
                    <CardHeader className="pb-4">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Cpu className="w-5 h-5 text-primary" />
                        系统配置
                      </CardTitle>
                      <CardDescription>
                        系统级别的配置选项和状态
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                          <div className="space-y-0.5">
                            <Label className="text-base">Mock LLM 模式</Label>
                            <p className="text-sm text-muted-foreground">
                              开发测试时使用模拟响应，不消耗 API 配额
                            </p>
                          </div>
                          <Switch
                            checked={config.mock_llm}
                            onCheckedChange={(checked) => updateConfig({ mock_llm: checked })}
                          />
                        </div>

                        <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                          <div className="space-y-0.5">
                            <Label className="text-base">调试模式</Label>
                            <p className="text-sm text-muted-foreground">
                              启用详细的调试日志输出
                            </p>
                          </div>
                          <Switch
                            checked={config.debug}
                            onCheckedChange={(checked) => updateConfig({ debug: checked })}
                          />
                        </div>
                      </div>

                      <div className="pt-4 border-t space-y-3">
                        <Label className="text-base">系统状态</Label>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                            <span className="text-sm">后端服务运行中</span>
                          </div>
                          <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
                            <FileJson className="w-4 h-4 text-blue-500" />
                            <span className="text-sm">配置文件已加载</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground">
                <Database className="w-12 h-12 opacity-50" />
                <p>无法加载配置，请检查后端服务是否运行</p>
                <Button variant="outline" size="sm" onClick={loadConfig}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  重试
                </Button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between gap-3 p-6 border-t bg-muted/30">
            <p className="text-xs text-muted-foreground">
              提示：API 密钥等敏感配置请在 config.yaml 中设置
            </p>
            <div className="flex items-center gap-3">
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
          </div>
        </motion.div>
      </motion.div>
    </TooltipProvider>
  );
}
