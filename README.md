# 鼻咽癌 MRI 预后预测平台

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![React](https://img.shields.io/badge/react-18.3-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)

一个综合性的基于 Web 的鼻咽癌（Nasopharyngeal Carcinoma, NPC）预后预测平台，使用 MRI 影像分析和机器学习技术。该系统通过直观的界面提供生存预测、风险分层和临床决策支持。

## 功能特性

- **用户认证**：基于 JWT 的安全注册和登录系统
- **MRI 影像分析**：上传和处理 NIfTI 格式的 MRI 影像（T1、T2、T1C），自动提取特征
- **生存预测**：使用 Cox 比例风险模型进行个性化生存率预测（1年、3年、5年）
- **风险分层**：基于最优阈值自动分类为高风险和低风险组
- **交互式可视化**：动态生存曲线、风险评分分布和对比分析图表
- **临床决策支持**：基于风险评估自动生成随访建议
- **预测历史**：完整的预测审计追踪，支持筛选和搜索功能
- **模型性能指标**：实时显示 C-index、AUC、敏感性和特异性
- **文件管理**：上传、下载和管理临床数据文件
- **响应式设计**：使用 React 和 Tailwind CSS 构建的现代化移动友好界面

## 技术栈

### 后端
- **框架**：Flask 2.3.3
- **数据库**：MongoDB 
- **认证**：Flask-JWT-Extended 配合 bcrypt 密码哈希
- **机器学习**：scikit-survival（Cox 模型）、scikit-learn、lifelines
- **图像处理**：nibabel、OpenCV、mahotas、scikit-image
- **数据处理**：pandas、numpy
- **可视化**：matplotlib
- **API 安全**：Flask-Limiter 用于速率限制、Flask-CORS 用于跨域请求

### 前端
- **框架**：React 18.3 配合 TypeScript
- **构建工具**：Vite 5.4
- **样式**：Tailwind CSS 3.4
- **路由**：React Router DOM 6.27
- **状态管理**：Zustand 5.0
- **图表**：Recharts 2.13
- **动画**：Framer Motion 11.11
- **图标**：Lucide React
- **HTTP 客户端**：Axios 1.7

### 基础设施
- **容器化**：Docker & Docker Compose
- **Web 服务器**：Nginx（前端反向代理）
- **Python 版本**：3.9
- **Node 版本**：兼容 Vite 5.x

## 架构概览

该平台采用现代化的三层架构：

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端层                             │
│  React SPA (端口 80) - 用户界面与可视化                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST API
┌─────────────────────────▼───────────────────────────────────┐
│                        应用层                                │
│  Flask API (端口 5001) - 业务逻辑与机器学习推理                 │
│  - 认证与授权                                                │
│  - MRI 影像特征提取                                           │
│  - Cox 模型预测                                              │
│  - 生存曲线生成                                               │
└─────────────────────────┬───────────────────────────────────┘
                          │ MongoDB 协议
┌─────────────────────────▼───────────────────────────────────┐
│                        数据层                                │
│  MongoDB (端口 27017) - 持久化存储                            │
│  - 用户账户                                                  │
│  - 预测历史                                                  │
│  - 临床数据                                                  │
└─────────────────────────────────────────────────────────────┘
```

## 前置要求

- **Docker**：版本 20.10 或更高
- **Docker Compose**：版本 2.0 或更高
- **系统要求**：
  - 最低 4GB 内存（推荐 8GB）
  - 10GB 可用磁盘空间
  - Linux、macOS 或带 WSL2 的 Windows

## 安装与设置

### 1. 克隆仓库

```bash
git clone <repository-url>
cd MRI
```

### 2. 准备模型文件

将训练好的模型文件放置在 `MRI_backend/models/` 目录中：

```
MRI_backend/models/
├── adasyn_cox_model.pkl      # 训练好的 Cox 模型
├── scaler.pkl                 # 特征缩放器
└── adasyn_model_info.pkl      # 模型元数据
```

### 3. 准备数据文件

将特征数据放置在 `MRI_backend/data/` 目录中：

```
MRI_backend/data/
└── flat_statistics.csv        # 预提取的特征（用于 /api/predict）
```

### 4. 配置环境变量

在项目根目录创建 `.env` 文件（可选，已提供默认值）：

```bash
# JWT 配置
JWT_SECRET_KEY=your-secure-secret-key-here
JWT_EXPIRES_DAYS=7

# 注册码（用于演示模式）
REGISTER_CODE=123456

# 模型路径（相对于容器中的 /app）
MODEL_PATH=models/adasyn_cox_model.pkl
SCALER_PATH=models/scaler.pkl
INFO_PATH=models/adasyn_model_info.pkl
FEATURES_PATH=data/flat_statistics.csv

# MongoDB 配置
MONGO_URI=mongodb://mongodb:27017/
MONGO_DB=MRI
MONGO_COLLECTION=predictions

# 文件存储
FILES_DIRECTORY=/app/data/16after/00C1068568
```

### 5. 构建并启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 6. 验证安装

- **前端**：http://localhost
- **后端 API**：http://localhost:5001
- **MongoDB**：localhost:27017

## 使用指南

### 启动应用

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看实时日志
docker-compose logs -f backend
```

### 访问应用

1. 打开浏览器并访问 `http://localhost`
2. 注册新账户或使用现有凭据登录
3. 上传 MRI 影像或使用预提取的特征进行预测
4. 查看生存曲线、风险评分和临床建议
5. 从仪表板访问预测历史

### 进行预测

#### 方法 1：上传 MRI 影像（推荐）

```bash
# 使用 curl
curl -X POST http://localhost:5001/api/upload-predict \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image_file=@/path/to/image.nii.gz" \
  -F "mask_file=@/path/to/mask.nii.gz" \
  -F "clinical_file=@/path/to/clinical.xlsx" \
  -F "image_type=T1"
```

#### 方法 2：使用预提取的特征

```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "Patient_ID": "P001",
    "性别": 1,
    "年龄": 45,
    "T分期": 3,
    "N分期": 2,
    "总分期": 3,
    "治疗前DNA": 150.5,
    "治疗后DNA": 80.2
  }'
```

## API 端点文档

### 认证端点

#### 注册用户
```http
POST /api/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepass",
  "code": "123456"
}
```

#### 登录
```http
POST /api/login
Content-Type: application/json

{
  "username": "user123",
  "password": "securepass"
}

响应：
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "username": "user123",
  "email": "user@example.com"
}
```

#### 获取当前用户
```http
GET /api/user
Authorization: Bearer <token>
```

#### 登出
```http
POST /api/logout
Authorization: Bearer <token>
```

### 预测端点

#### 使用预提取特征进行预测
```http
POST /api/predict
Content-Type: application/json
Authorization: Bearer <token>

{
  "Patient_ID": "P001",
  "性别": 1,
  "年龄": 45,
  "T分期": 3,
  "N分期": 2,
  "总分期": 3,
  "治疗前DNA": 150.5,
  "治疗后DNA": 80.2
}
```

#### 上传并预测
```http
POST /api/upload-predict
Content-Type: multipart/form-data
Authorization: Bearer <token>

表单数据：
- image_file: NIfTI 影像文件（.nii 或 .nii.gz）
- mask_file: NIfTI 掩码文件
- clinical_file: 临床数据（.xlsx、.xls 或 .csv）
- image_type: "T1" | "T2" | "T1C"
```

#### 获取生存曲线数据
```http
POST /api/survival-curve-data
Content-Type: application/json
Authorization: Bearer <token>

{
  "Patient_ID": "P001",
  "性别": 1,
  "年龄": 45,
  "T分期": 3,
  "N分期": 2,
  "总分期": 3,
  "治疗前DNA": 150.5,
  "治疗后DNA": 80.2
}
```

### 历史记录和管理端点

#### 获取预测历史
```http
GET /api/prediction-history?patient_id=P001&limit=20&skip=0&time_range=month
Authorization: Bearer <token>
```

#### 删除预测
```http
DELETE /api/prediction/<prediction_id>
Authorization: Bearer <token>
```

#### 获取 MRI 影像
```http
GET /api/images
Authorization: Bearer <token>
```

#### 获取文件列表
```http
GET /api/get-file-list
```

#### 下载文件
```http
GET /files/<filename>
```

## 项目结构

```
MRI/
├── MRI_backend/                    # 后端应用
│   ├── Dockerfile                  # 后端容器配置
│   ├── requirements.txt            # Python 依赖
│   ├── predict_backend.py          # 主 Flask 应用
│   ├── OS_T1_predictor.py          # Cox 模型预测器类
│   ├── feature_extractor.py        # MRI 特征提取
│   ├── auth_models.py              # 用户认证模型
│   ├── models/                     # 训练好的机器学习模型
│   │   ├── adasyn_cox_model.pkl
│   │   ├── scaler.pkl
│   │   └── adasyn_model_info.pkl
│   └── data/                       # 数据文件
│       ├── flat_statistics.csv
│       └── 16after/                # 示例 MRI 数据
│
├── frontend/                       # 前端应用
│   ├── Dockerfile                  # 前端容器配置
│   ├── package.json                # Node.js 依赖
│   ├── tsconfig.json               # TypeScript 配置
│   ├── vite.config.ts              # Vite 构建配置
│   ├── tailwind.config.js          # Tailwind CSS 配置
│   ├── src/                        # 源代码
│   │   ├── App.tsx                 # 主应用组件
│   │   ├── main.tsx                # 应用入口点
│   │   ├── components/             # React 组件
│   │   ├── pages/                  # 页面组件
│   │   ├── store/                  # Zustand 状态管理
│   │   └── utils/                  # 工具函数
│   └── public/                     # 静态资源
│
├── docker-compose.yml              # 多容器编排
├── nginx.conf                      # Nginx 配置
└── README.md                       # 本文件
```

## 开发指南

### 后端开发

#### 本地运行后端

```bash
cd MRI_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 上：venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export MONGO_URI=mongodb://localhost:27017/
export JWT_SECRET_KEY=dev-secret-key

# 运行开发服务器
python predict_backend.py
```

#### 添加新的 API 端点

1. 在 `predict_backend.py` 中定义路由
2. 实现验证逻辑
3. 如需要，添加 MongoDB 操作
4. 更新 API 文档
5. 使用 curl 或 Postman 测试

### 前端开发

#### 本地运行前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

#### 项目结构

- `src/components/`：可复用的 UI 组件
- `src/pages/`：页面级组件
- `src/store/`：Zustand 状态管理
- `src/utils/`：辅助函数和 API 客户端

### 代码风格

- **后端**：遵循 PEP 8 规范
- **前端**：使用 ESLint 和 Prettier 配置
- **TypeScript**：启用严格模式
- **提交**：使用约定式提交消息

## 测试说明

### 后端测试

```bash
cd MRI_backend

# 运行单元测试
python -m pytest tests/

# 测试 API 端点
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# 检查模型加载
python -c "from OS_T1_predictor import OST1Predictor; print('Model OK')"
```

### 前端测试

```bash
cd frontend

# 运行类型检查
npm run build

# 测试生产构建
npm run preview
```

### 集成测试

```bash
# 启动所有服务
docker-compose up -d

# 等待服务就绪
sleep 10

# 测试健康检查端点
curl http://localhost:5001/api/prediction-history
curl http://localhost/

# 检查日志中的错误
docker-compose logs backend | grep ERROR
```

### 负载测试

```bash
# 安装 Apache Bench
sudo apt-get install apache2-utils

# 测试预测端点
ab -n 100 -c 10 -T application/json \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5001/api/prediction-history
```

## 部署说明

### 生产环境检查清单

- [ ] 将 `JWT_SECRET_KEY` 更改为强随机值
- [ ] 更新 `REGISTER_CODE` 或实现适当的邀请系统
- [ ] 配置 MongoDB 认证
- [ ] 使用 SSL 证书启用 HTTPS
- [ ] 设置 MongoDB 备份策略
- [ ] 配置日志轮转
- [ ] 设置监控和告警
- [ ] 审查并调整速率限制规则
- [ ] 实现适当的错误跟踪（如 Sentry）
- [ ] 仅为生产域名配置 CORS

### 环境特定配置

#### 开发环境
```bash
docker-compose up
```

#### 生产环境
```bash
# 使用生产 compose 文件
docker-compose -f docker-compose.prod.yml up -d

# 启用自动重启
docker-compose -f docker-compose.prod.yml up -d --restart=always
```

### 扩展考虑

- **后端**：使用 Gunicorn 配合多个 worker
- **数据库**：启用 MongoDB 副本集以实现高可用性
- **前端**：通过 CDN 提供静态资源
- **负载均衡**：使用 Nginx 或云负载均衡器处理多个后端实例

### 安全最佳实践

1. **永远不要提交密钥**：使用环境变量或密钥管理
2. **定期更新**：保持依赖项最新
3. **输入验证**：在后端验证所有用户输入
4. **速率限制**：防止暴力攻击
5. **仅使用 HTTPS**：在生产环境中强制使用 SSL/TLS
6. **数据库安全**：启用认证和加密
7. **审计日志**：记录所有认证和预测事件

### 备份策略

```bash
# 备份 MongoDB
docker exec mri-mongodb mongodump --out /backup

# 备份模型
tar -czf models-backup.tar.gz MRI_backend/models/

# 自动化每日备份
0 2 * * * /path/to/backup-script.sh
```

## 故障排除

### 常见问题

#### 后端无法启动
```bash
# 检查日志
docker-compose logs backend

# 验证模型文件存在
ls -la MRI_backend/models/

# 检查 MongoDB 连接
docker-compose exec backend python -c "from pymongo import MongoClient; print(MongoClient('mongodb://mongodb:27017/').server_info())"
```

#### 前端构建失败
```bash
# 清除 node_modules 并重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### MongoDB 连接被拒绝
```bash
# 确保 MongoDB 正在运行
docker-compose ps mongodb

# 检查网络连接
docker-compose exec backend ping mongodb
```

#### 模型预测错误
```bash
# 验证模型兼容性
docker-compose exec backend python -c "import pickle; pickle.load(open('models/adasyn_cox_model.pkl', 'rb'))"

# 检查特征对齐
docker-compose logs backend | grep "特征对齐"
```

## 性能优化

- **后端**：为静态预测启用响应缓存
- **前端**：实现代码拆分和懒加载
- **数据库**：为频繁查询的字段创建索引
- **图像**：压缩和优化 MRI 可视化
- **API**：对大型结果集使用分页

## 贡献

欢迎贡献！请遵循以下指南：

1. Fork 仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'Add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 开启 Pull Request

## 许可证

本项目采用 Apache-2.0 License 开源协议 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- Cox 比例风险模型实现基于 scikit-survival
- MRI 特征提取使用影像组学原理
- UI 设计灵感来自现代医疗软件界面
- 中文字体支持由文泉驿正黑提供

## 支持

如有问题、疑问或贡献：
- 在 GitHub 上开启 issue
- 联系开发团队
- 查看文档 wiki

## 更新日志

### 版本 1.0.0（当前版本）
- 初始发布
- 用户认证系统
- MRI 影像上传和特征提取
- Cox 模型生存预测
- 交互式生存曲线可视化
- 预测历史管理
- Docker 容器化
- 带完整文档的 RESTful API
