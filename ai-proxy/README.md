# AI Proxy Service

AI Proxy Service 是一个微服务，用于处理材料分类请求。它从S3下载文件，调用OpenAI API进行处理，并将结果保存到另一个S3 bucket中。

## 功能

- 接收加密的材料分类请求
- 从S3下载指定的文件
- 调用OpenAI API处理文件内容
- 将处理结果保存到classify-result bucket
- 返回加密的结果文件位置信息

## API端点

### POST /api/classify-material

处理材料分类请求。

**请求格式:**
```json
{
  "data": "encrypted_request_data"
}
```

加密的请求数据包含:
```json
{
  "object_bucket": "source-bucket-name",
  "object_key": "source-file-key"
}
```

**响应格式:**
```json
{
  "status": "success",
  "data": "encrypted_response_data"
}
```

加密的响应数据包含:
```json
{
  "result_bucket": "classify-result-bucket-name",
  "result_key": "result-file-key.classify_result.txt"
}
```

## 环境变量

- `SERVER_PORT`: 服务端口 (默认: 8091)
- `S3_ENDPOINT`: S3服务端点
- `S3_ACCESS_KEY`: S3访问密钥
- `S3_SECRET_KEY`: S3秘密密钥
- `S3_BUCKET`: 源文件bucket
- `CLASSIFY_RESULT_BUCKET`: 分类结果bucket
- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_MODEL`: OpenAI模型名称
- `OPENAI_URL`: OpenAI API URL
- `LOG_LEVEL`: 日志级别

## 依赖管理

本服务使用uv进行依赖管理：
- `pyproject.toml`: 项目依赖配置
- `uv.lock`: 锁定的依赖版本

## 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8091
