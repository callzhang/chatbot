# 🤖 星尘小助手 (Stardust AI Assistant)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.21+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**一个功能丰富的AI聊天助手，集成了多种AI模型和实用工具**

[🚀 快速开始](#-快速开始) • [✨ 功能特性](#-功能特性) • [📖 使用指南](#-使用指南) • [🛠️ 技术栈](#️-技术栈)

</div>

---

## 📋 项目简介

星尘小助手是一个基于Streamlit构建的多功能AI聊天应用，集成了OpenAI GPT系列模型、图像生成、语音处理、网页检索等多种AI能力。通过直观的Web界面，用户可以轻松体验各种AI功能，包括智能对话、文档处理、图像创作等。

## ✨ 功能特性

### 🧠 智能对话
- **GPT-3.5/GPT-4对话** - 支持最新的OpenAI模型
- **GPT-4V多模态** - 图像理解和分析
- **Assistant API** - 自定义AI助手
- **实时流式响应** - 流畅的对话体验

### 🔍 信息检索
- **网页搜索** - 实时获取最新信息
- **智能摘要** - 自动提取关键信息
- **多源整合** - 结合多个数据源

### 🎨 创意工具
- **文字生成图片** - AI图像创作
- **语音识别** - 语音转文字
- **文本朗读** - 文字转语音
- **多语言支持** - 中英文切换

### 📄 文档处理
- **PDF对话** - 智能文档问答
- **Excel处理** - 表格数据分析
- **Markdown转换** - 格式转换工具

### 🔧 实用功能
- **聊天历史** - 对话记录管理
- **密钥管理** - 安全的API密钥配置
- **精选应用** - 集成优质AI工具
- **错误监控** - Sentry集成

## 🚀 快速开始

### 环境要求
- Python 3.8+
- OpenAI API Key
- 其他可选API密钥（Bing、Google等）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/chatbot.git
cd chatbot
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置密钥**
创建 `.streamlit/secrets.toml` 文件：
```toml
openai-key = "your-openai-api-key"
debug = false
streaming = true
```

4. **启动应用**
```bash
streamlit run home.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:8501`

## 📖 使用指南

### 主要页面

#### 🤗 助理页面
- 选择不同的AI模型进行对话
- 支持GPT-3.5、GPT-4、GPT-4V等模型
- 实时流式响应，体验流畅对话

#### 🔍 信息检索
- 输入问题，AI会搜索最新信息
- 自动整合多个来源的信息
- 提供准确的答案和引用

#### 🎨 创意工具
- **文字做图**: 输入描述，生成AI图像
- **语音识别**: 上传音频文件，转换为文字
- **文本朗读**: 输入文字，生成语音文件

#### 📒 聊天历史
- 查看和管理历史对话
- 支持搜索和筛选
- 导出对话记录

#### ㊙️ 秘钥管理
- 安全配置各种API密钥
- 支持OpenAI、Bing、Google等
- 密钥加密存储

#### ⭐️ 精选应用
- 集成优质AI工具推荐
- 包括ChatPDF、文心一言等
- 一键访问外部AI服务

### 使用技巧

1. **模型选择**: 根据需求选择合适的AI模型
   - GPT-3.5: 日常对话，响应快速
   - GPT-4: 复杂推理，质量更高
   - GPT-4V: 图像理解，多模态交互

2. **任务类型**: 选择正确的任务类型获得最佳效果
   - 对话: 一般性聊天和问答
   - 信息检索: 需要最新信息的查询
   - 文字做图: 图像生成需求

3. **提示词优化**: 使用清晰、具体的提示词
   - 明确描述你的需求
   - 提供必要的上下文信息
   - 使用中文或英文都可以

## 🛠️ 技术栈

### 核心框架
- **Streamlit** - Web应用框架
- **Gradio** - 备选UI框架
- **OpenAI API** - AI模型接口

### 主要依赖
- **streamlit** - 主Web框架
- **openai** - OpenAI API客户端
- **EdgeGPT** - Bing AI集成
- **transformers** - 本地模型支持
- **beautifulsoup4** - 网页解析
- **gspread-pandas** - Google Sheets集成

### 工具模块
```
tools/
├── openai.py      # OpenAI API集成
├── bing.py        # Bing搜索集成
├── speech.py      # 语音处理
├── imagegen.py    # 图像生成
├── document.py    # 文档处理
├── google_sheet.py # Google Sheets
├── apify.py       # 网页抓取
└── utils.py       # 工具函数
```

## 📁 项目结构

```
chatbot/
├── home.py                 # 主应用入口
├── chatbot_v2.py          # Gradio版本
├── requirements.txt       # 依赖列表
├── pages/                 # Streamlit页面
│   ├── 🤗助理.py         # AI助手页面
│   ├── 📒聊天历史.py     # 历史记录
│   ├── ㊙️秘钥管理.py     # 密钥管理
│   └── ⭐️精选应用.py     # 应用推荐
├── tools/                 # 工具模块
│   ├── openai.py         # OpenAI集成
│   ├── bing.py           # 搜索功能
│   ├── speech.py         # 语音处理
│   ├── imagegen.py       # 图像生成
│   └── ...
└── images/               # 静态资源
    ├── chatpdf.png
    └── icon.ico
```

## 🔧 配置说明

### 环境变量
```bash
# 必需
OPENAI_API_KEY=your-openai-key

# 可选
BING_COOKIE=your-bing-cookie
GOOGLE_API_KEY=your-google-key
```

### Streamlit配置
创建 `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## 🚀 部署指南

### 本地部署
```bash
# 开发模式
streamlit run home.py --server.port 8501

# 生产模式
streamlit run home.py --server.port 8501 --server.headless true
```

### 云端部署
支持部署到：
- **Streamlit Cloud** - 官方云平台
- **Heroku** - 简单部署
- **Docker** - 容器化部署
- **VPS** - 自建服务器

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v2.0.0 (2023-11-28)
- ✨ 新增文本朗读功能
- 🎨 优化UI界面设计
- 🔧 改进错误处理机制

### v1.5.0 (2023-11-10)
- ✨ 新增网页信息检索功能
- 🔍 集成Bing搜索API
- 📊 添加数据可视化

### v1.3.0 (2023-11-5)
- ✨ 新增GPT-4V多模态对话
- 🖼️ 支持图像理解和分析
- 🎯 优化模型选择逻辑

### v1.0.0 (2023-11-3)
- 🎉 首次发布
- ✨ 基础GPT-4对话功能
- 🎨 Streamlit界面

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的AI模型
- [Streamlit](https://streamlit.io/) - 优秀的Web框架
- [Gradio](https://gradio.app/) - 备选UI框架
- 所有贡献者和用户的支持

## 📞 联系我们

- **项目主页**: [GitHub Repository](https://github.com/your-username/chatbot)
- **问题反馈**: [Issues](https://github.com/your-username/chatbot/issues)
- **功能建议**: [Discussions](https://github.com/your-username/chatbot/discussions)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**

Made with ❤️ by [Derek](https://github.com/your-username)

</div>