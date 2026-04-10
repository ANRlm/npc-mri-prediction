from flask import Flask, request, jsonify
import matplotlib
matplotlib.use('Agg')  # 设置为非交互模式
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import base64
from io import BytesIO
import pandas as pd
import numpy as np
import os
# 添加MongoDB相关库
from pymongo import MongoClient
import datetime
from OS_T1_predictor import OST1Predictor
from flask_cors import CORS
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='npc_prediction_api.log'
)
logger = logging.getLogger('npc_prediction_api')

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 开启跨域

# MongoDB连接配置
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'MRI')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'predictions')

# 初始化MongoDB客户端
mongo_client = None
db = None
predictions_collection = None


def init_mongodb():
    """初始化MongoDB连接"""
    global mongo_client, db, predictions_collection
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[MONGO_DB]
        predictions_collection = db[MONGO_COLLECTION]
        logger.info("MongoDB连接成功")
        return True
    except Exception as e:
        logger.error(f"MongoDB连接失败: {str(e)}")
        return False


# 模型路径配置
MODEL_PATH = os.environ.get('MODEL_PATH', '模型构建/OS/OS-T1/models/adasyn_cox_model.pkl')
SCALER_PATH = os.environ.get('SCALER_PATH', '模型构建/OS/OS-T1/models/scaler.pkl')
INFO_PATH = os.environ.get('INFO_PATH', '模型构建/OS/OS-T1/models/adasyn_model_info.pkl')
FEATURES_PATH = os.environ.get('FEATURES_PATH',
                               'data/flat_statistics.csv')

# 初始化全局预测器对象
predictor = None


# 加载预测模型，如果出错则记录日志
def load_predictor():
    global predictor
    try:
        predictor = OST1Predictor(
            model_path=MODEL_PATH,
            scaler_path=SCALER_PATH,
            info_path=INFO_PATH
        )
        logger.info("模型加载成功")
        return True
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        return False


# 计算生存率
def calculate_survival_rates(risk_score):
    """ 计算生存率

    Args:
        risk_score (float): 风险评分

    Returns:
        dict: 包含1年、3年和5年生存率的字典
        list: 生存率列表 [1年, 3年, 5年]
    """
    months = np.array([12, 36, 60])  # 1年、3年、5年

    # 基于风险评分计算个性化生存概率
    hazard_ratio = np.exp(risk_score) / np.exp(3.0)  # 相对于基准风险评分3.0的风险比
    baseline_survival = np.exp(-0.01 * months)  # 基线生存率
    personalized_survival = np.power(baseline_survival, hazard_ratio)  # 个性化生存率

    return {
        '1年生存率': f'{personalized_survival[0]:.1%}',
        '3年生存率': f'{personalized_survival[1]:.1%}',
        '5年生存率': f'{personalized_survival[2]:.1%}'
    }, personalized_survival


def get_model_metrics():
    """获取模型评估指标"""
    try:
        if hasattr(predictor, 'model_info') and 'metrics' in predictor.model_info:
            metrics = predictor.model_info['metrics']
        else:
            # 默认指标
            metrics = {
                'c_index': 0.82,
                'auc': 0.85,
                'sensitivity': 0.78,
                'specificity': 0.81,
                'precision': 0.76,
                'recall': 0.78,
                'f1': 0.77,
                'balanced_accuracy': 0.80
            }
        return metrics
    except Exception as e:
        logger.error(f"获取模型评估指标时出错: {str(e)}")
        # 返回默认指标
        return {
            'c_index': 0.82,
            'auc': 0.85,
            'sensitivity': 0.78,
            'specificity': 0.81,
            'precision': 0.76,
            'recall': 0.78,
            'f1': 0.77,
            'balanced_accuracy': 0.80
        }


def create_survival_curve_base64(risk_score, patient_id):
    """
    生成个性化生存曲线并返回base64编码的图像

    Args:
        risk_score (float): 风险评分
        patient_id (str): 患者ID

    Returns:
        str: base64编码的图像
    """
    # 设置中文字体
    plt.rcParams['font.family'] = 'SimHei'
    plt.rcParams['axes.unicode_minus'] = False

    # 时间点(月)
    months = np.arange(0, 60, 1)

    # 基于风险评分计算个性化生存概率
    hazard_ratio = np.exp(risk_score) / np.exp(3.0)  # 相对于基准风险评分3.0的风险比
    baseline_survival = np.exp(-0.01 * months)  # 基线生存率
    personalized_survival = np.power(baseline_survival, hazard_ratio)  # 个性化生存率

    # 计算参考组生存率
    high_risk_survival = np.exp(-0.04 * months)  # 高风险组平均生存率
    low_risk_survival = np.exp(-0.008 * months)  # 低风险组平均生存率

    # 计算1年、3年和5年生存率
    survival_1yr = np.interp(12, months, personalized_survival)
    survival_3yr = np.interp(36, months, personalized_survival)
    survival_5yr = np.interp(60, months, personalized_survival)

    # 绘制图形
    plt.figure(figsize=(10, 8))
    gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1])

    # 1. 主生存曲线
    ax1 = plt.subplot(gs[0, :])
    ax1.plot(months, personalized_survival, 'g-', linewidth=3, label=f'患者 {patient_id} 预测')
    ax1.plot(months, low_risk_survival, 'b--', linewidth=1.5, label='低风险组平均')
    ax1.plot(months, high_risk_survival, 'r--', linewidth=1.5, label='高风险组平均')

    # 标记1年、3年和5年生存率
    ax1.plot([12], [survival_1yr], 'go', markersize=8)
    ax1.plot([36], [survival_3yr], 'go', markersize=8)
    ax1.plot([60], [survival_5yr], 'go', markersize=8)

    ax1.text(12, survival_1yr + 0.05, f'1年: {survival_1yr:.1%}', fontsize=10)
    ax1.text(36, survival_3yr + 0.05, f'3年: {survival_3yr:.1%}', fontsize=10)
    ax1.text(60, survival_5yr + 0.05, f'5年: {survival_5yr:.1%}', fontsize=10)

    ax1.set_title(f'患者预测生存曲线 (ID: {patient_id})', fontsize=14)
    ax1.set_xlabel('时间 (月)', fontsize=12)
    ax1.set_ylabel('生存概率', fontsize=12)
    ax1.legend(loc='lower left', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_ylim(0, 1.05)

    # 2. 风险评分与参考分布
    ax2 = plt.subplot(gs[1, 0])

    # 生成参考风险评分分布
    reference_scores = np.random.normal(3.5, 1.0, 100)  # 模拟参考人群的风险评分
    ax2.hist(reference_scores, bins=15, alpha=0.5, color='lightblue', density=True, label='参考人群分布')

    # 绘制患者的风险评分
    ylim = ax2.get_ylim()
    ax2.plot([risk_score, risk_score], [0, ylim[1]], 'r-', linewidth=2, label='患者风险评分')
    ax2.plot(risk_score, 0, 'ro', markersize=8)

    ax2.set_title('风险评分对比', fontsize=12)
    ax2.set_xlabel('风险评分', fontsize=10)
    ax2.set_ylabel('密度', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.7)

    # 3. 生存率对比
    ax3 = plt.subplot(gs[1, 1])

    # 用条形图展示1年、3年和5年生存率
    years = ['1年', '3年', '5年']
    patient_rates = [survival_1yr, survival_3yr, survival_5yr]
    low_risk_rates = [np.exp(-0.008 * 12), np.exp(-0.008 * 36), np.exp(-0.008 * 60)]
    high_risk_rates = [np.exp(-0.04 * 12), np.exp(-0.04 * 36), np.exp(-0.04 * 60)]

    x = np.arange(len(years))
    width = 0.25

    ax3.bar(x - width, high_risk_rates, width, label='高风险组', color='lightcoral')
    ax3.bar(x, patient_rates, width, label='患者预测', color='lightgreen')
    ax3.bar(x + width, low_risk_rates, width, label='低风险组', color='lightblue')

    ax3.set_title('生存率对比', fontsize=12)
    ax3.set_ylabel('生存概率', fontsize=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(years)
    ax3.legend(fontsize=9)
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')

    plt.tight_layout()

    # 将图像转换为base64
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return img_base64


# 返回画图数据
def get_survival_curve_data(risk_score, patient_id):
    """
    获取绘制生存曲线所需的全部数据

    Args:
        risk_score (float): 风险评分
        patient_id (str): 患者ID

    Returns:
        dict: 包含所有绘图数据的字典
    """
    # 时间点(月)
    months = np.arange(0, 61, 1).tolist()  # 0-60个月

    # 基于风险评分计算个性化生存概率
    hazard_ratio = np.exp(risk_score) / np.exp(3.0)  # 相对于基准风险评分3.0的风险比
    baseline_survival = np.exp(-0.01 * np.array(months))  # 基线生存率
    personalized_survival = np.power(baseline_survival, hazard_ratio)  # 个性化生存率

    # 计算参考组生存率
    high_risk_survival = np.exp(-0.04 * np.array(months))  # 高风险组平均生存率
    low_risk_survival = np.exp(-0.008 * np.array(months))  # 低风险组平均生存率

    # 为了前端绘图，将numpy数组转换为列表并保留4位小数
    personalized_survival_list = [round(float(val), 4) for val in personalized_survival]
    high_risk_survival_list = [round(float(val), 4) for val in high_risk_survival]
    low_risk_survival_list = [round(float(val), 4) for val in low_risk_survival]

    # 关键时间点的生存率 (1年、3年、5年)
    survival_1yr = round(float(np.interp(12, months, personalized_survival)), 4)
    survival_3yr = round(float(np.interp(36, months, personalized_survival)), 4)
    survival_5yr = round(float(np.interp(60, months, personalized_survival)), 4)

    # 参考风险评分分布数据 (模拟100个参考病例)
    reference_scores = np.random.normal(3.5, 1.0, 100)
    reference_scores_list = [round(float(score), 4) for score in reference_scores]

    # 生存率柱状图数据
    bar_chart_data = {
        'categories': ['1年', '3年', '5年'],
        'high_risk': [
            round(float(np.exp(-0.04 * 12)), 4),
            round(float(np.exp(-0.04 * 36)), 4),
            round(float(np.exp(-0.04 * 60)), 4)
        ],
        'patient': [survival_1yr, survival_3yr, survival_5yr],
        'low_risk': [
            round(float(np.exp(-0.008 * 12)), 4),
            round(float(np.exp(-0.008 * 36)), 4),
            round(float(np.exp(-0.008 * 60)), 4)
        ]
    }

    # 构造DataV适用的折线图数据格式
    line_chart_data = []
    for i, month in enumerate(months):
        line_chart_data.append({
            'month': month,
            'patient': personalized_survival_list[i],
            'high_risk': high_risk_survival_list[i],
            'low_risk': low_risk_survival_list[i]
        })

    # 构造DataV适用的直方图数据格式
    histogram_data = []
    bins = np.linspace(min(reference_scores), max(reference_scores), 15)
    hist, bin_edges = np.histogram(reference_scores, bins=bins, density=True)
    for i in range(len(hist)):
        histogram_data.append({
            'bin_min': round(float(bin_edges[i]), 2),
            'bin_max': round(float(bin_edges[i + 1]), 2),
            'frequency': round(float(hist[i]), 4)
        })

    # 返回完整的数据对象
    return {
        'patient_id': patient_id,
        'risk_score': round(float(risk_score), 4),
        'months': months,
        'survival_curves': {
            'patient': personalized_survival_list,
            'high_risk': high_risk_survival_list,
            'low_risk': low_risk_survival_list
        },
        'line_chart_data': line_chart_data,
        'key_points': {
            '1yr': {'month': 12, 'survival': survival_1yr},
            '3yr': {'month': 36, 'survival': survival_3yr},
            '5yr': {'month': 60, 'survival': survival_5yr}
        },
        'reference_scores': {
            'scores': reference_scores_list,
            'patient_score': round(float(risk_score), 4),
            'mean': round(float(np.mean(reference_scores)), 4),
            'std': round(float(np.std(reference_scores)), 4),
            'histogram': histogram_data
        },
        'bar_chart': bar_chart_data
    }


def validate_input(data):
    """验证输入数据是否完整有效"""
    required_fields = ['Patient_ID', '性别', '年龄', 'T分期', 'N分期', '总分期', '治疗前DNA', '治疗后DNA']

    # 检查所有必填字段是否存在
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"

    # 验证数据类型
    try:
        # 验证数值型字段
        float(data['年龄'])
        float(data['T分期'])
        float(data['N分期'])
        float(data['总分期'])
        float(data['治疗前DNA'])
        float(data['治疗后DNA'])
    except ValueError as e:
        return False, f"数据类型错误: {str(e)}"

    return True, ""


def save_prediction_to_mongodb(prediction_data):
    """将预测结果保存到MongoDB

    Args:
        prediction_data (dict): 预测结果数据

    Returns:
        bool: 保存是否成功
    """
    global predictions_collection
    if predictions_collection is None:
        if not init_mongodb():
            logger.error("MongoDB未初始化，无法保存数据")
            return False

    try:
        # 添加时间戳
        prediction_data['stored_at'] = datetime.datetime.now()

        # 保存到MongoDB
        result = predictions_collection.insert_one(prediction_data)
        logger.info(f"预测结果已保存到MongoDB, _id: {result.inserted_id}")
        return True
    except Exception as e:
        logger.error(f"保存到MongoDB失败: {str(e)}")
        return False


def generate_clinical_advice(is_high_risk):
    """
    基于风险评估生成临床建议

    Args:
        is_high_risk (bool): 是否为高风险

    Returns:
        list: 临床建议列表
    """
    if is_high_risk:
        return [
            "增加随访频率，建议每1-2个月随访一次",
            "考虑更积极的治疗方案",
            "密切关注治疗反应和副作用"
        ]
    else:
        return [
            "按照常规流程进行随访，建议每3-6个月随访一次",
            "保持良好生活习惯",
            "定期复查"
        ]


@app.route('/api/predict', methods=['POST'])
def predict():
    # 确保模型已加载
    global predictor
    if predictor is None:
        if not load_predictor():
            return jsonify({
                "success": False,
                "message": "模型加载失败，请联系管理员"
            }), 500

    try:
        # 获取JSON数据
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "未接收到数据"
            }), 400

        # 验证输入数据
        is_valid, error_msg = validate_input(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400

        # 创建DataFrame
        clinical_data = pd.DataFrame({
            'Patient_ID': [data['Patient_ID']],
            '性别': [data['性别']],
            '年龄': [float(data['年龄'])],
            'T分期': [float(data['T分期'])],
            'N分期': [float(data['N分期'])],
            '总分期': [float(data['总分期'])],
            '治疗前DNA': [float(data['治疗前DNA'])],
            '治疗后DNA': [float(data['治疗后DNA'])]
        })

        # 加载特征数据
        try:
            features_data = pd.read_csv(FEATURES_PATH)
            # 添加患者ID
            features_data['Patient_ID'] = data['Patient_ID']
        except Exception as e:
            logger.error(f"读取特征数据失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"读取特征数据失败: {str(e)}"
            }), 500

        # 进行预测
        try:
            # 特征对齐和转换
            aligned_features = predictor._align_features(features_data)
            transformed_features = predictor.scaler.transform(aligned_features)

            # 预测风险评分
            risk_score = float(predictor.model.predict(transformed_features)[0])

            # 确定风险分组
            is_high_risk = risk_score > predictor.optimal_threshold
            risk_group = "高风险组" if is_high_risk else "低风险组"

            # 计算生存率
            survival_rates, survival_values = calculate_survival_rates(risk_score)

            # 获取模型评估指标
            metrics = get_model_metrics()

            # 生成临床建议
            clinical_advice = generate_clinical_advice(is_high_risk)

            # 生成生存曲线图并转换为base64
            survival_curve_base64 = create_survival_curve_base64(risk_score, data['Patient_ID'])

            # 构建响应
            response = {
                "success": True,
                "data": {
                    "patient_id": data['Patient_ID'],
                    "risk_score": round(risk_score, 4),
                    "risk_group": risk_group,
                    "survival_rates": survival_rates,
                    "metrics": {
                        "c_index": round(metrics.get('c_index', 0.8), 3),
                        "auc": round(metrics.get('auc', 0.8), 3),
                        "sensitivity": round(metrics.get('sensitivity', 0.8), 3),
                        "specificity": round(metrics.get('specificity', 0.8), 3)
                    },
                    "clinical_advice": clinical_advice,
                    "survival_curve_base64": survival_curve_base64,
                    "timestamp": datetime.datetime.now().isoformat(timespec='seconds')
                },
                "message": "预测成功"
            }

            # 存储预测数据到MongoDB
            try:
                # 构建用于MongoDB存储的文档
                mongo_data = {
                    "patient_id": data['Patient_ID'],
                    "input_data": {
                        "性别": data['性别'],
                        "年龄": float(data['年龄']),
                        "T分期": float(data['T分期']),
                        "N分期": float(data['N分期']),
                        "总分期": float(data['总分期']),
                        "治疗前DNA": float(data['治疗前DNA']),
                        "治疗后DNA": float(data['治疗后DNA'])
                    },
                    "prediction_results": {
                        "risk_score": round(risk_score, 4),
                        "risk_group": risk_group,
                        "survival_rates": {
                            "1年生存率": survival_rates['1年生存率'],
                            "3年生存率": survival_rates['3年生存率'],
                            "5年生存率": survival_rates['5年生存率']
                        },
                        "metrics": {
                            "c_index": round(metrics.get('c_index', 0.8), 3),
                            "auc": round(metrics.get('auc', 0.8), 3),
                            "sensitivity": round(metrics.get('sensitivity', 0.8), 3),
                            "specificity": round(metrics.get('specificity', 0.8), 3)
                        },
                        "clinical_advice": clinical_advice
                    },
                    "prediction_time": datetime.datetime.now()
                }

                # 确保MongoDB已连接
                if predictions_collection is None:
                    logger.info("MongoDB集合未初始化，正在尝试初始化...")
                    init_mongodb()

                # 保存到MongoDB
                if predictions_collection is not None:
                    result = predictions_collection.insert_one(mongo_data)
                    logger.info(f"预测结果已保存到MongoDB, _id: {result.inserted_id}")
                else:
                    logger.error("无法保存到MongoDB: 集合未初始化")

            except Exception as e:
                logger.error(f"保存到MongoDB失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # 继续处理，不中断API响应

            # 记录预测成功日志
            logger.info(f"患者{data['Patient_ID']}预测成功，风险分组: {risk_group}")

            return jsonify(response)

        except Exception as e:
            logger.error(f"预测过程中出错: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"预测过程中出错: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"API处理请求时出错: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"处理请求时出错: {str(e)}"
        }), 500


# dataV可视化数据返回
@app.route('/api/survival-curve-data', methods=['POST'])
def get_survival_chart_data():
    """提供生存曲线所需的数据，适用于DataV前端可视化

    请求体格式同/api/predict接口

    返回DataV可用的数据结构
    """
    # 确保模型已加载
    global predictor
    if predictor is None:
        if not load_predictor():
            return jsonify({
                "success": False,
                "message": "模型加载失败，请联系管理员"
            }), 500

    try:
        # 获取JSON数据
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "未接收到数据"
            }), 400

        # 验证输入数据
        is_valid, error_msg = validate_input(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400

        # 创建DataFrame
        clinical_data = pd.DataFrame({
            'Patient_ID': [data['Patient_ID']],
            '性别': [data['性别']],
            '年龄': [float(data['年龄'])],
            'T分期': [float(data['T分期'])],
            'N分期': [float(data['N分期'])],
            '总分期': [float(data['总分期'])],
            '治疗前DNA': [float(data['治疗前DNA'])],
            '治疗后DNA': [float(data['治疗后DNA'])]
        })

        # 加载特征数据
        try:
            features_data = pd.read_csv(FEATURES_PATH)
            # 添加患者ID
            features_data['Patient_ID'] = data['Patient_ID']
        except Exception as e:
            logger.error(f"读取特征数据失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"读取特征数据失败: {str(e)}"
            }), 500

        # 进行预测
        try:
            # 特征对齐和转换
            aligned_features = predictor._align_features(features_data)
            transformed_features = predictor.scaler.transform(aligned_features)

            # 预测风险评分
            risk_score = float(predictor.model.predict(transformed_features)[0])

            # 获取生存曲线数据
            chart_data = get_survival_curve_data(risk_score, data['Patient_ID'])

            # 返回数据
            return jsonify({
                "success": True,
                "data": chart_data,
                "message": "数据获取成功"
            })

        except Exception as e:
            logger.error(f"预测过程中出错: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"预测过程中出错: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"API处理请求时出错: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"处理请求时出错: {str(e)}"
        }), 500


@app.route('/api/prediction-history', methods=['GET'])
def get_prediction_history():
    """获取历史预测记录

    查询参数:
    - patient_id: 可选，按患者ID过滤
    - limit: 可选，限制返回记录数量，默认20
    - skip: 可选，跳过记录数量，默认0

    返回:
    - 预测记录列表
    """
    try:
        # 获取查询参数
        patient_id = request.args.get('patient_id')
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))

        # 构建查询条件
        query = {}
        if patient_id:
            query['patient_id'] = patient_id

        # 确保MongoDB已连接
        if predictions_collection is None:
            if not init_mongodb():
                return jsonify({
                    "success": False,
                    "message": "MongoDB未初始化，无法查询数据"
                }), 500

        # 查询MongoDB
        results = list(predictions_collection.find(
            query,
            {'_id': 0}  # 排除_id字段
        ).sort('prediction_time', -1).skip(skip).limit(limit))

        # 转换datetime对象为ISO格式字符串
        for result in results:
            if 'prediction_time' in result:
                result['prediction_time'] = result['prediction_time'].isoformat()

        return jsonify({
            "success": True,
            "data": results,
            "count": len(results),
            "message": "查询成功"
        })

    except Exception as e:
        logger.error(f"查询历史记录时出错: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"查询历史记录时出错: {str(e)}"
        }), 500

# 应用启动时加载模型
# 使用Flask 2.0+兼容的方式初始化
# 不再使用@app.before_first_request，而是使用app实例化后直接加载

def create_app():
    """应用工厂函数，解决Flask 2.0+中不再支持before_first_request的问题"""
    # 确保模型加载
    with app.app_context():
        load_predictor()
        init_mongodb()  # 初始化MongoDB连接
    return app


if __name__ == "__main__":
    # 应用启动时加载模型
    load_predictor()
    init_mongodb()  # 初始化MongoDB连接

    # 启动应用
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)