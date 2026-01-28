# Crux AgenticRAG Backend

基于FastAPI的Crux AgenticRAG框架后端服务，提供流式API支持前端实时显示处理进度。

## 功能特性

- 🚀 **FastAPI框架**: 现代化的异步Web框架
- 📡 **流式响应**: 支持Server-Sent Events (SSE)，实时返回处理状态
- 🔧 **配置管理**: 支持动态配置数据源、Schema和LLM参数
- 📊 **健康检查**: 提供系统健康状态监控
- 🔄 **CORS支持**: 配置跨域访问支持前端开发

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 运行服务

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 3. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 获取默认配置
curl http://localhost:8000/api/config/default
```

## API 接口

### GET `/`
根路径，返回API信息

### GET `/health`
健康检查接口

### GET `/api/config/default`
获取默认配置参数

### POST `/api/query`
普通查询接口（同步返回结果）

**请求体:**
```json
{
  "query": "找关于RAG的论文",
  "data_source_type": "json",
  "data_source_path": "data/ir_papers.json",
  "schema_type": "paper",
  "mock_llm": true,
  "debug": false
}
```

### POST `/api/query/stream`
流式查询接口（SSE）

返回Server-Sent Events格式的实时处理状态：

```javascript
// 连接SSE
const eventSource = new EventSource('/api/query/stream');

// 监听不同类型的事件
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'start':
      console.log('开始处理:', data.message);
      break;
    case 'stage_complete':
      console.log(`阶段 ${data.stage} 完成:`, data.output);
      break;
    case 'complete':
      console.log('处理完成');
      eventSource.close();
      break;
    case 'error':
      console.error('错误:', data.message);
      eventSource.close();
      break;
  }
};
```

## 配置说明

### 数据源配置
- `data_source_type`: 数据源类型 (`"json"`, `"csv"`, `"vector_db"`)
- `data_source_path`: 数据文件路径
- `schema_type`: Schema类型 (`"paper"`, `"news"`, `"log"`)

### LLM配置
- `mock_llm`: 是否使用模拟LLM（开发时设为true）
- `model`: LLM模型名称
- `temperature`: 生成温度
- `max_tokens`: 最大token数

### 检索配置
- `max_iterations`: 最大迭代次数
- `top_k`: 检索返回Top-K结果
- `use_bm25`: 是否启用BM25检索
- `use_vector`: 是否启用向量检索
- `use_metadata_filter`: 是否启用元数据过滤

## 开发说明

### 项目结构
```
backend/
├── main.py           # 主应用入口
├── requirements.txt  # 依赖包列表
└── README.md         # 文档说明
```

### 扩展接口

如需添加新的数据源类型或Schema：

1. 在`src/crux/data/loaders/`中实现新的数据加载器
2. 在`src/crux/schemas/`中定义新的Schema
3. 更新`CruxConfig`类支持新配置项

### 错误处理

API遵循标准的HTTP状态码：
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 与前端集成

后端已配置CORS支持前端开发服务器（`http://localhost:5173`）。

前端可通过以下方式调用：

```typescript
// 流式查询
const response = await fetch('http://localhost:8000/api/query/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: '用户查询' })
});
```
