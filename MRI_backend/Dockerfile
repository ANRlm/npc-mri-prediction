# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfontconfig1 \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY predict_backend.py OS_T1_predictor.py ./
COPY requirements.txt ./

# 创建模型和数据目录
RUN mkdir -p models data output

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=models/adasyn_cox_model.pkl
ENV SCALER_PATH=models/scaler.pkl
ENV INFO_PATH=models/adasyn_model_info.pkl
ENV FEATURES_PATH=data/flat_statistics.csv
ENV PORT=5001

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "predict_backend.py"]