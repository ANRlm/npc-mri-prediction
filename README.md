# MRI项目Docker部署指南

## 项目结构

该项目包含两个主要组件：
- 前端：Vue3应用（vue3-font-mri目录）
- 后端：Flask API（MRI_backend目录）

## Docker部署步骤

### 前提条件

- 安装Docker和Docker Compose
- 确保项目文件结构完整

### 部署步骤

1. 构建前端项目
```bash
cd vue3-font-mri
npm install
npm run build
```

2. 启动Docker容器
```bash
docker-compose up -d
```

3. 访问应用
   - 前端界面：http://localhost
   - 后端API：http://localhost:5001

### 注意事项

1. 此Docker配置针对生产环境。前端已通过nginx配置将`/api/`路径的请求代理到后端服务。

2. 如果你需要在开发环境中使用，请注意前端代码中的API请求基地址可能需要修改：
   - 修改`vue3-font-mri/src/utils/http.js`中的baseURL配置
   - 将`http://127.0.0.1:5001`改为`/api`，利用nginx代理

3. 数据卷挂载
   - 后端服务挂载了三个数据卷：`models`、`data`和`output`
   - 确保这些目录包含必要的数据文件和模型文件

4. 环境变量
   - 可以通过修改docker-compose.yml文件中的environment部分来调整后端配置

## 故障排除

1. 如果前端无法连接到后端，检查:
   - nginx配置是否正确
   - 网络连接是否正常
   - API端点是否正确

2. 如果后端无法启动，检查:
   - 所需的模型文件是否存在
   - 数据文件是否完整
   - 环境变量是否配置正确

## 日志查看

查看容器日志：
```bash
# 查看前端日志
docker logs mri-frontend

# 查看后端日志
docker logs mri-backend
``` 