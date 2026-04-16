# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 更换为阿里云Debian镜像源（解决国内网络访问deb.debian.org问题）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfontconfig1 \
    libfreetype6-dev \
    fonts-wqy-zenhei \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY predict_backend.py os_t1_predictor.py auth_models.py feature_extractor.py ./
COPY requirements.txt ./

# 创建模型和数据目录
RUN mkdir -p models data output

# 安装Python依赖
# 升级pip并更换为阿里云PyPI镜像（解决国内网络访问pypi.org问题）
RUN python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && python -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && python -m pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=models/adasyn_cox_model.pkl
ENV SCALER_PATH=models/scaler.pkl
ENV INFO_PATH=models/adasyn_model_info.pkl
ENV FEATURES_PATH=data/flat_statistics.csv
ENV PORT=5001
ENV MONGO_URI=mongodb://mongodb:27017/
ENV JWT_SECRET_KEY=your-secret-key-change-in-production

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "predict_backend.py"]
