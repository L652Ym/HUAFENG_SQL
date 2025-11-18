# Phoenix RAG 快速开始

## 5分钟上手指南

### 1️⃣ 安装依赖 (1分钟)

```bash
cd phoenix_rag_demo
pip install -r requirements_phoenix_demo.txt
```

### 2️⃣ 配置API密钥 (1分钟)

```bash
# 复制配置文件
cp .env.example .env

# 编辑.env,填入你的DeepSeek API密钥
# 获取地址: https://platform.deepseek.com/
```

在 `.env` 中设置:
```bash
DEEPSEEK_API_KEY=sk-你的密钥
```

### 3️⃣ 运行演示 (3分钟)

```bash
python demo.py
```

### 4️⃣ 查看Phoenix UI

浏览器打开: http://localhost:6006

---

## 🎯 你会看到什么?

### 终端输出
- ✅ Phoenix启动成功提示
- ✅ RAG索引构建进度
- ✅ 5个测试问题的回答
- ✅ Phoenix评估结果统计

### Phoenix UI
- 📊 所有查询的追踪记录
- ⏱️ 每一步的耗时分析
- 💬 LLM的prompt和response
- 📈 Token使用统计
- ✨ 评估质量指标

---

## 🚀 快速测试 (无Phoenix)

如果只想测试RAG功能:

```bash
python simple_test.py
```

---

## ❓ 遇到问题?

### API密钥错误
```
❌ 未找到DEEPSEEK_API_KEY
```
→ 检查 `.env` 文件是否正确配置

### 端口被占用
```
❌ Port 6006 already in use
```
→ 在 `.env` 中修改: `PHOENIX_PORT=6007`

### 网络连接问题
```
❌ Connection timeout
```
→ 检查网络连接和API服务状态

---

## 📚 详细文档

查看完整文档: [README_PHOENIX_RAG.md](README_PHOENIX_RAG.md)

包含:
- 详细的架构说明
- Phoenix使用指南
- 代码详解
- 常见问题
- 扩展建议

---

## 🎓 学习路径

1. **运行演示** → 了解基本功能
2. **查看Phoenix UI** → 理解追踪机制
3. **阅读代码** → 学习实现细节
4. **修改参数** → 优化性能
5. **添加数据** → 构建自己的RAG

---

**享受你的Phoenix RAG之旅!** 🌟
