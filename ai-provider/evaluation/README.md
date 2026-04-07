# 精度测试框架

这是一个用于测试各种模型准确率和召回率的框架。

## 功能特性

- 支持从CSV文件加载测试数据
- 自动计算准确率、召回率、精确率和F1分数
- 显示混淆矩阵
- 支持多种模型函数
- 详细的日志输出

## 安装依赖

### 使用uv安装（推荐）

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e .

# 或者安装完整版本（包含所有可选依赖）
uv pip install -e ".[full]"

# 或者安装开发版本（包含测试工具）
uv pip install -e ".[dev]"
```

### 运行程序

```bash
# 使用uv运行
uv run python eva.py --list-models

# 或者激活虚拟环境后直接运行
source .venv/bin/activate
python eva.py --ground-truth example_input.csv --model "bedrock.classify_video_is_funny"
```

### 安装llm-proxy项目依赖

确保已安装llm-proxy项目的依赖：

```bash
cd llm-proxy
uv pip install -r requirements.txt
```

### 传统pip安装（备选）

如果不想使用uv，也可以使用传统的pip：

```bash
# 安装基本依赖
pip install -r requirements-minimal.txt

# 安装完整依赖
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python eva.py --ground-truth input.csv --model "bedrock.classify_video_is_funny"
```

### 参数说明

- `--ground-truth`: 包含真实标签的CSV文件路径（必需）
- `--model`: 模型函数名称，格式为 "package.function_name"（必需）
- `--list-models`: 列出所有可用的模型
- `--verbose`: 显示详细日志

### 查看可用模型

```bash
python eva.py --list-models
```

### 详细日志模式

```bash
python eva.py --ground-truth input.csv --model "bedrock.classify_video_is_funny" --verbose
```

## CSV文件格式

框架支持动态字段，会根据CSV文件的第一行header自动识别字段。**只要求包含 `expect_result` 字段**，其余字段全部自动传递给模型函数。

- `expect_result`: 期望结果（0或1，唯一必需字段）
- 其他字段：全部自动传递给模型函数，模型函数可自由使用

### 示例CSV文件

**最简格式：**
```csv
expect_result
1
0
```

**扩展格式（包含任意自定义字段）：**
```csv
expect_result,content_id,video_url,slice_duration,description,category
1,id1,https://example.com/video1.mp4,120,搞笑视频1,娱乐
1,id2,https://example.com/video2.mp4,90,搞笑视频2,搞笑
0,id3,https://example.com/video3.mp4,120,严肃视频1,新闻
0,id4,https://example.com/video4.mp4,60,严肃视频2,教育
```

框架会自动识别所有字段并将其传递给模型函数，模型函数可以根据需要处理这些额外参数。

## 输出结果

框架会输出以下指标：

- **准确率 (Accuracy)**: 正确预测的样本占总样本的比例
- **精确率 (Precision)**: 预测为正例中实际为正例的比例
- **召回率 (Recall)**: 实际正例中被正确预测的比例
- **F1分数 (F1-Score)**: 精确率和召回率的调和平均数
- **混淆矩阵**: 显示预测结果的详细分布

### 示例输出

```
=== 评估结果 ===
总样本数: 4
准确率 (Accuracy): 0.7500 (75.00%)
精确率 (Precision): 1.0000 (100.00%)
召回率 (Recall): 0.5000 (50.00%)
F1分数 (F1-Score): 0.6667 (66.67%)

详细统计:
真阳性 (TP): 1
假阳性 (FP): 0
真阴性 (TN): 2
假阴性 (FN): 1

混淆矩阵:
          预测
           0    1
实际  0    2    0
      1    1    1
```

## 添加新模型

要添加新的模型函数，请在 `models.py` 文件中：

1. 定义新的模型函数
2. 在 `MODEL_REGISTRY` 中注册模型

### 示例

```python
def my_new_model(**kwargs) -> int:
    """我的新模型函数"""
    # 实现模型逻辑
    return 0  # 或 1

# 注册模型
MODEL_REGISTRY = {
    "bedrock.classify_video_is_funny": classify_video_is_funny,
    "my.new_model": my_new_model,  # 添加新模型
}
```

## 错误处理

框架包含完善的错误处理机制：

- CSV文件格式验证
- 数据完整性检查
- 模型执行异常处理
- 详细的错误日志

## 注意事项

1. 确保llm-proxy服务正常运行
2. 视频URL必须可访问
3. 模型函数必须返回0或1
4. CSV文件编码建议使用UTF-8

## 故障排除

### 常见问题

1. **模块导入错误**: 确保llm-proxy项目路径正确
2. **CSV文件格式错误**: 检查列名和数据格式
3. **模型执行失败**: 检查网络连接和API配置
4. **视频URL不可访问**: 确保视频URL有效且可访问

### 调试模式

使用 `--verbose` 参数获取详细的调试信息：

```bash
python eva.py --ground-truth input.csv --model "bedrock.classify_video_is_funny" --verbose
```