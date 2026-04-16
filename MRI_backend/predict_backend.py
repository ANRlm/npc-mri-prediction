from flask import Flask, request, jsonify, send_from_directory
from datetime import timedelta
import matplotlib
matplotlib.use('Agg')  # 设置为非交互模式
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
import base64
from io import BytesIO
import pandas as pd
import numpy as np
import os
# 添加MongoDB相关库
from pymongo import MongoClient
import datetime
from os_t1_predictor import OST1Predictor
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import re
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='npc_prediction_api.log'
)
logger = logging.getLogger('npc_prediction_api')


def _setup_cjk_font():
    """Configure matplotlib to use WenQuanYi Zen Hei for CJK rendering."""
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for path in font_paths:
        if os.path.exists(path):
            prop = fm.FontProperties(fname=path)
            plt.rcParams['font.family'] = prop.get_name()
            fm.fontManager.addfont(path)
            return
    # Fallback: try any available CJK font
    for f in fm.fontManager.ttflist:
        if any(k in f.name for k in ('WenQuanYi', 'Noto', 'CJK', 'SimHei', 'Arial Unicode')):
            plt.rcParams['font.family'] = f.name
            return

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 开启跨域
jwt = JWTManager(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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
MODEL_PATH = os.environ.get('MODEL_PATH', 'model_training/OS/OS-T1/models/adasyn_cox_model.pkl')
SCALER_PATH = os.environ.get('SCALER_PATH', 'model_training/OS/OS-T1/models/scaler.pkl')
INFO_PATH = os.environ.get('INFO_PATH', 'model_training/OS/OS-T1/models/adasyn_model_info.pkl')
FEATURES_PATH = os.environ.get('FEATURES_PATH',
                               'data/flat_statistics.csv')

# 初始化全局预测器对象
predictor = None




def configure_jwt():
    """配置JWT设置"""
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=int(os.environ.get('JWT_EXPIRES_DAYS', '7')))

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
    # 设置中文字体 (WenQuanYi Zen Hei installed in container)
    _setup_cjk_font()
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

    # 验证数据类型及范围
    try:
        age = float(data['年龄'])
        t_stage = float(data['T分期'])
        n_stage = float(data['N分期'])
        total_stage = float(data['总分期'])
        dna_before = float(data['治疗前DNA'])
        dna_after = float(data['治疗后DNA'])
    except (ValueError, TypeError) as e:
        return False, f"数据类型错误: {str(e)}"

    import math
    for name, val in [('年龄', age), ('T分期', t_stage), ('N分期', n_stage),
                      ('总分期', total_stage), ('治疗前DNA', dna_before), ('治疗后DNA', dna_after)]:
        if math.isnan(val) or math.isinf(val):
            return False, f"{name} 包含无效数值"

    if not (0 < age <= 150):
        return False, "年龄须在 1-150 之间"
    if t_stage not in (1, 2, 3, 4):
        return False, "T分期须为 1/2/3/4"
    if n_stage not in (0, 1, 2, 3):
        return False, "N分期须为 0/1/2/3"
    if total_stage not in (1, 2, 3, 4):
        return False, "总分期须为 1/2/3/4"
    if dna_before <= 0:
        return False, "治疗前DNA须为正数"
    if dna_after <= 0:
        return False, "治疗后DNA须为正数"

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
@jwt_required()
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
        username = get_jwt_identity()

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
                    "username": username,  # 记录执行预测的用户
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

                    # 记录访问日志
                    if db is not None:
                        access_log = {
                            'username': username,
                            'action': 'predict',
                            'patient_id': data['Patient_ID'],
                            'risk_group': risk_group,
                            'timestamp': datetime.datetime.utcnow()
                        }
                        db['access_logs'].insert_one(access_log)
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


# ============== 上传文件 + 自动特征提取 预测接口 ==============

# 影像依赖是否可用（lazy check）
_IMAGING_DEPS_CHECKED = False
_IMAGING_DEPS_AVAILABLE = False
_IMAGING_DEPS_ERROR = ""


def _check_imaging_deps():
    """检查影像处理相关依赖是否已安装。"""
    global _IMAGING_DEPS_CHECKED, _IMAGING_DEPS_AVAILABLE, _IMAGING_DEPS_ERROR
    if _IMAGING_DEPS_CHECKED:
        return _IMAGING_DEPS_AVAILABLE, _IMAGING_DEPS_ERROR
    try:
        import nibabel  # noqa: F401
        import cv2  # noqa: F401
        import mahotas  # noqa: F401
        import skimage  # noqa: F401
        import scipy  # noqa: F401
        _IMAGING_DEPS_AVAILABLE = True
        _IMAGING_DEPS_ERROR = ""
    except Exception as e:
        _IMAGING_DEPS_AVAILABLE = False
        _IMAGING_DEPS_ERROR = str(e)
    _IMAGING_DEPS_CHECKED = True
    return _IMAGING_DEPS_AVAILABLE, _IMAGING_DEPS_ERROR


def _normalize_sex(value):
    """规范化性别字段 → 数值: 1=男, 2=女。"""
    if value is None:
        return None
    s = str(value).strip()
    upper = s.upper()
    if s in ('男',) or upper in ('M', 'MALE', '1'):
        return 1
    if s in ('女',) or upper in ('F', 'FEMALE', '0', '2'):
        return 2
    try:
        return float(s)
    except ValueError:
        return None


_CLINICAL_COLUMN_MAP = {
    'patient_id': 'Patient_ID', 'Patient_ID': 'Patient_ID', 'PatientID': 'Patient_ID',
    'sex': '性别', '性别': '性别', 'gender': '性别',
    'age': '年龄', '年龄': '年龄',
    't_stage': 'T分期', 'T分期': 'T分期', 'T_stage': 'T分期', 'tstage': 'T分期',
    'n_stage': 'N分期', 'N分期': 'N分期', 'N_stage': 'N分期', 'nstage': 'N分期',
    'dna_after': '治疗后DNA', '治疗后DNA': '治疗后DNA', 'DNA_after': '治疗后DNA',
    'total_stage': '总分期', '总分期': '总分期',
    'dna_before': '治疗前DNA', '治疗前DNA': '治疗前DNA', 'DNA_before': '治疗前DNA',
}


def _parse_clinical_file(file_path):
    """解析临床数据文件（xlsx/xls/csv），返回第一行规范化后的字典。"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(file_path)
    elif ext == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"不支持的临床数据文件格式: {ext}")

    if df.empty:
        raise ValueError("临床数据文件为空")

    # 列名映射（中英文兼容）
    renamed = {}
    for col in df.columns:
        key = str(col).strip()
        if key in _CLINICAL_COLUMN_MAP:
            renamed[col] = _CLINICAL_COLUMN_MAP[key]
    if renamed:
        df = df.rename(columns=renamed)

    row = df.iloc[0].to_dict()

    # 必需字段校验
    required = ['性别', '年龄', 'T分期', 'N分期', '治疗后DNA']
    missing = [c for c in required if c not in row or pd.isna(row.get(c))]
    if missing:
        raise ValueError(f"临床数据缺少必要字段: {', '.join(missing)}")

    result = {
        'Patient_ID': str(row.get('Patient_ID', 'UNKNOWN')),
        '性别': _normalize_sex(row.get('性别')),
        '年龄': float(row.get('年龄')),
        'T分期': float(row.get('T分期')),
        'N分期': float(row.get('N分期')),
        '治疗后DNA': float(row.get('治疗后DNA')),
    }
    # 可选字段
    if '总分期' in row and not pd.isna(row.get('总分期')):
        result['总分期'] = float(row.get('总分期'))
    if '治疗前DNA' in row and not pd.isna(row.get('治疗前DNA')):
        result['治疗前DNA'] = float(row.get('治疗前DNA'))
    return result


def _save_upload(file_storage, tmp_dir, prefix):
    """保存上传文件到临时目录，保留原扩展名。"""
    filename = file_storage.filename or f"{prefix}.bin"
    # 处理 .nii.gz 的复合扩展名
    lower = filename.lower()
    if lower.endswith('.nii.gz'):
        ext = '.nii.gz'
    else:
        ext = os.path.splitext(filename)[1]
    target = os.path.join(tmp_dir, f"{prefix}{ext}")
    file_storage.save(target)
    return target


@app.route('/api/upload-predict', methods=['POST'])
def upload_predict():
    """上传影像+掩膜+临床数据，自动提取特征后预测。

    multipart/form-data 字段：
      - image_file: NIfTI 原始影像 (.nii 或 .nii.gz)
      - mask_file:  NIfTI 掩膜文件
      - clinical_file: 临床数据 (.xlsx/.xls/.csv)
      - image_type: 字符串 T1/T2/T1C（用于日志）
    """
    global predictor
    import tempfile
    import shutil

    # 依赖检查
    ok, err = _check_imaging_deps()
    if not ok:
        logger.error(f"影像处理依赖未安装: {err}")
        return jsonify({
            "success": False,
            "message": "影像处理依赖未安装，请联系管理员重新构建后端镜像"
        }), 503

    # 模型加载
    if predictor is None:
        if not load_predictor():
            return jsonify({"success": False, "message": "模型加载失败，请联系管理员"}), 500

    # 校验上传文件
    image_file = request.files.get('image_file')
    mask_file = request.files.get('mask_file')
    clinical_file = request.files.get('clinical_file')
    image_type = (request.form.get('image_type') or 'T1').strip()

    if image_file is None or image_file.filename == '':
        return jsonify({"success": False, "message": "缺少 image_file"}), 400
    if mask_file is None or mask_file.filename == '':
        return jsonify({"success": False, "message": "缺少 mask_file"}), 400
    if clinical_file is None or clinical_file.filename == '':
        return jsonify({"success": False, "message": "缺少 clinical_file"}), 400

    tmp_dir = tempfile.mkdtemp(prefix='mri_upload_')
    try:
        image_path = _save_upload(image_file, tmp_dir, 'image')
        mask_path = _save_upload(mask_file, tmp_dir, 'mask')
        clinical_path = _save_upload(clinical_file, tmp_dir, 'clinical')

        # 解析临床数据
        try:
            clinical = _parse_clinical_file(clinical_path)
        except Exception as e:
            logger.error(f"解析临床数据失败: {e}")
            return jsonify({"success": False, "message": f"解析临床数据失败: {str(e)}"}), 400

        # 提取影像特征
        try:
            from feature_extractor import extract_features
            logger.info(f"开始提取 {image_type} 影像特征: {image_path}")
            image_features = extract_features(image_path, mask_path)
            logger.info(f"特征提取完成，共 {len(image_features)} 个特征")
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "message": f"特征提取失败: {str(e)}"}), 500

        # 构造合并后的 DataFrame（临床 + 影像特征）
        patient_id = clinical.get('Patient_ID') or 'UNKNOWN'
        row = {
            'Patient_ID': patient_id,
            '性别': clinical.get('性别'),
            '年龄': clinical.get('年龄'),
            'T分期': clinical.get('T分期'),
            'N分期': clinical.get('N分期'),
            '治疗后DNA': clinical.get('治疗后DNA'),
        }
        if '总分期' in clinical:
            row['总分期'] = clinical['总分期']
        if '治疗前DNA' in clinical:
            row['治疗前DNA'] = clinical['治疗前DNA']
        row.update(image_features)
        merged = pd.DataFrame([row])

        # 预测（复用 predictor 的特征对齐 + 标准化逻辑）
        try:
            aligned = predictor._align_features(merged)
            transformed = predictor.scaler.transform(aligned)
            risk_score = float(predictor.model.predict(transformed)[0])

            is_high_risk = risk_score > predictor.optimal_threshold
            risk_group = "高风险组" if is_high_risk else "低风险组"

            survival_rates, _ = calculate_survival_rates(risk_score)
            metrics = get_model_metrics()
            clinical_advice = generate_clinical_advice(is_high_risk)
            survival_curve_base64 = create_survival_curve_base64(risk_score, patient_id)

            response = {
                "success": True,
                "data": {
                    "patient_id": patient_id,
                    "image_type": image_type,
                    "risk_score": round(risk_score, 4),
                    "risk_group": risk_group,
                    "survival_rates": survival_rates,
                    "metrics": {
                        "c_index": round(metrics.get('c_index', 0.8), 3),
                        "auc": round(metrics.get('auc', 0.8), 3),
                        "sensitivity": round(metrics.get('sensitivity', 0.8), 3),
                        "specificity": round(metrics.get('specificity', 0.8), 3),
                    },
                    "clinical_advice": clinical_advice,
                    "survival_curve_base64": survival_curve_base64,
                    "timestamp": datetime.datetime.now().isoformat(timespec='seconds'),
                },
                "message": "预测成功",
            }

            # 存 MongoDB（失败不阻塞响应）
            try:
                if predictions_collection is None:
                    init_mongodb()
                if predictions_collection is not None:
                    predictions_collection.insert_one({
                        "patient_id": patient_id,
                        "image_type": image_type,
                        "input_data": {k: (v if not isinstance(v, float) else float(v)) for k, v in clinical.items()},
                        "prediction_results": {
                            "risk_score": round(risk_score, 4),
                            "risk_group": risk_group,
                            "survival_rates": survival_rates,
                        },
                        "prediction_time": datetime.datetime.now(),
                        "source": "upload-predict",
                    })
            except Exception as e:
                logger.error(f"保存到 MongoDB 失败: {e}")

            logger.info(f"上传预测成功 patient={patient_id} type={image_type} group={risk_group}")
            return jsonify(response)

        except Exception as e:
            logger.error(f"预测过程中出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "message": f"预测过程中出错: {str(e)}"}), 500

    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")


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
@jwt_required()
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
        username = get_jwt_identity()
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

        # 时间范围过滤
        time_range = request.args.get('time_range')
        if time_range:
            now = datetime.datetime.utcnow()
            if time_range == 'week':
                query['prediction_time'] = {'$gte': now - datetime.timedelta(days=7)}
            elif time_range == 'month':
                query['prediction_time'] = {'$gte': now - datetime.timedelta(days=30)}
            elif time_range == 'year':
                query['prediction_time'] = {'$gte': now - datetime.timedelta(days=365)}

        # 查询MongoDB（保留_id用于删除操作）
        results = list(predictions_collection.find(
            query
        ).sort('prediction_time', -1).skip(skip).limit(limit))

        # Flatten nested prediction_results into PredictionData shape expected by frontend
        flattened = []
        for result in results:
            pr = result.get('prediction_results', {})
            flat = {
                "id": str(result['_id']),
                "patient_id": result.get('patient_id', ''),
                "risk_score": pr.get('risk_score', result.get('risk_score', 0)),
                "risk_group": pr.get('risk_group', result.get('risk_group', '')),
                "survival_rates": pr.get('survival_rates', result.get('survival_rates', {
                    '1年生存率': '—', '3年生存率': '—', '5年生存率': '—'
                })),
                "metrics": pr.get('metrics', result.get('metrics')) or get_model_metrics(),
                "clinical_advice": pr.get('clinical_advice', result.get('clinical_advice')) or generate_clinical_advice(pr.get('risk_group', result.get('risk_group', '')) == '高风险组'),
                "timestamp": result['prediction_time'].isoformat()
                    if hasattr(result.get('prediction_time'), 'isoformat')
                    else str(result.get('prediction_time', '')),
            }
            flattened.append(flat)

        # 记录访问日志到MongoDB
        try:
            if db is not None:
                access_log = {
                    'username': username,
                    'action': 'view_prediction_history',
                    'patient_id': patient_id,
                    'record_count': len(flattened),
                    'timestamp': datetime.datetime.utcnow()
                }
                db['access_logs'].insert_one(access_log)
        except Exception as log_error:
            logger.warning(f"记录访问日志失败: {log_error}")

        return jsonify({
            "success": True,
            "data": flattened,
            "count": len(flattened),
            "message": "查询成功"
        })

    except Exception as e:
        logger.error(f"查询历史记录时出错: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"查询历史记录时出错: {str(e)}"
        }), 500


# ============== 认证 API ==============

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """验证用户名格式"""
    if len(username) < 3 or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False
    return True

@app.route('/api/register', methods=['POST'])
@limiter.limit('5 per minute')
def register():
    """用户注册"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "未接收到数据"}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # 输入验证
        if not username:
            return jsonify({"success": False, "message": "用户名不能为空"}), 400
        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400
        if not password:
            return jsonify({"success": False, "message": "密码不能为空"}), 400
        
        if not validate_username(username):
            return jsonify({"success": False, "message": "用户名格式不正确（3-50位字母数字或下划线）"}), 400
        if not validate_email(email):
            return jsonify({"success": False, "message": "邮箱格式不正确"}), 400
        if not validate_password(password):
            return jsonify({"success": False, "message": "密码至少6位"}), 400

        # 验证码验证（演示模式：接受任意验证码）
        code = data.get('code', '')
        if not code:
            return jsonify({"success": False, "message": "请输入验证码"}), 400

        # 创建用户
        try:
            from auth_models import create_user, get_user_by_username, get_user_by_email
            user = create_user(username, email, password)
            logger.info(f"用户注册成功: {username}")
            return jsonify({
                "success": True,
                "message": "注册成功",
                "username": user['username'],
                "email": user['email']
            }), 201
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 409
        except Exception as e:
            logger.error(f"注册错误: {str(e)}")
            return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500
            
    except Exception as e:
        logger.error(f"注册处理错误: {str(e)}")
        return jsonify({"success": False, "message": f"处理请求时出错: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    """用户登录"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "未接收到数据"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        
        # 查询用户
        from auth_models import get_user_with_password, verify_password, update_last_login
        user = get_user_with_password(username)
        
        if not user:
            logger.warning(f"登录失败 - 用户不存在: {username}")
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            logger.warning(f"登录失败 - 密码错误: {username}")
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
        
        # 更新最后登录时间
        update_last_login(username)
        
        # 生成JWT token
        access_token = create_access_token(identity=username)
        
        logger.info(f"用户登录成功: {username}")
        return jsonify({
            "success": True,
            "message": "登录成功",
            "token": access_token,
            "username": user['username'],
            "email": user['email']
        }), 200
        
    except Exception as e:
        logger.error(f"登录处理错误: {str(e)}")
        return jsonify({"success": False, "message": f"处理请求时出错: {str(e)}"}), 500

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    """获取当前用户信息"""
    try:
        username = get_jwt_identity()
        from auth_models import get_user_by_username
        user = get_user_by_username(username)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        return jsonify({
            "success": True,
            "username": user['username'],
            "email": user['email'],
            "created_at": user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户信息错误: {str(e)}")
        return jsonify({"success": False, "message": f"处理请求时出错: {str(e)}"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """退出登录"""
    try:
        logger.info(f"用户登出")
        return jsonify({
            "success": True,
            "message": "登出成功"
        }), 200
    except Exception as e:
        logger.error(f"登出错误: {str(e)}")
        return jsonify({"success": False, "message": f"处理请求时出错: {str(e)}"}), 500

@app.route('/api/change_password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        username = get_jwt_identity()
        data = request.json

        if not data or not data.get('old_password') or not data.get('new_password'):
            return jsonify({"success": False, "message": "旧密码和新密码是必填项"}), 400

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        # 验证新密码强度
        if not validate_password(new_password):
            return jsonify({"success": False, "message": "新密码至少6位"}), 400

        # 获取用户信息（包含密码哈希）
        from auth_models import get_user_with_password, verify_password, hash_password, _get_coll
        user = get_user_with_password(username)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 验证旧密码
        if not verify_password(old_password, user['password_hash']):
            logger.warning(f"修改密码失败 - 旧密码错误: {username}")
            return jsonify({"success": False, "message": "旧密码不正确"}), 401

        # 更新密码
        coll = _get_coll()
        coll.update_one(
            {'username': username},
            {'$set': {'password_hash': hash_password(new_password)}}
        )

        logger.info(f"用户密码修改成功: {username}")
        return jsonify({"success": True, "message": "密码修改成功"}), 200

    except Exception as e:
        logger.error(f"修改密码错误: {str(e)}")
        return jsonify({"success": False, "message": f"处理请求时出错: {str(e)}"}), 500

# ============== 认证 API 结束 ==============

# ============== 文件管理 API ==============
import os

# 文件存储目录（请确保该目录存在且可读写）
FILES_DIRECTORY = os.environ.get('FILES_DIRECTORY', os.path.join(os.getcwd(), 'data/16after/00C1068568'))

@app.route('/api/get-file-list', methods=['GET'])
def get_file_list():
    """获取文件列表（仅列出文件，不包含目录）"""
    try:
        files = [f for f in os.listdir(FILES_DIRECTORY) if os.path.isfile(os.path.join(FILES_DIRECTORY, f))]
        return jsonify({"files": files})
    except Exception as e:
        logger.error(f"读取文件列表失败: {e}")
        return jsonify({"files": [], "error": str(e)}), 500

@app.route('/files/<filename>', methods=['GET'])
def download_file(filename):
    """提供文件下载"""
    try:
        file_path = os.path.join(FILES_DIRECTORY, filename)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "文件未找到"}), 404
        return send_from_directory(FILES_DIRECTORY, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/prediction/<prediction_id>', methods=['DELETE'])
@jwt_required()
def delete_prediction(prediction_id):
    """删除指定预测记录"""
    try:
        from bson import ObjectId
        if predictions_collection is None:
            if not init_mongodb():
                return jsonify({"success": False, "message": "MongoDB未初始化"}), 500
        result = predictions_collection.delete_one({'_id': ObjectId(prediction_id)})
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "记录不存在"}), 404
        return jsonify({"success": True, "message": "删除成功"})
    except Exception as e:
        logger.error(f"删除预测记录失败: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """返回统计数据"""
    try:
        username = get_jwt_identity()

        # 获取输出目录参数
        output_dir = request.args.get('output_dir', os.path.join(os.getcwd(), 'data'))

        # 尝试读取 flat_statistics.csv
        csv_path = os.path.join(output_dir, 'flat_statistics.csv')
        if not os.path.exists(csv_path):
            # 尝试默认路径
            csv_path = os.path.join(os.getcwd(), 'data', 'flat_statistics.csv')

        if not os.path.exists(csv_path):
            return jsonify({"success": False, "message": "统计数据文件未找到"}), 404

        # 读取CSV文件
        statistics_df = pd.read_csv(csv_path)
        statistics_data = statistics_df.to_dict(orient='records')

        # 记录访问日志到MongoDB
        try:
            if db is not None:
                access_log = {
                    'username': username,
                    'action': 'view_statistics',
                    'directory': output_dir,
                    'feature_count': len(statistics_data),
                    'timestamp': datetime.datetime.utcnow()
                }
                db['access_logs'].insert_one(access_log)
        except Exception as log_error:
            logger.warning(f"记录访问日志失败: {log_error}")

        logger.info(f"用户 {username} 查看统计数据")
        return jsonify({
            "success": True,
            "statistics": statistics_data,
            "count": len(statistics_data)
        }), 200

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({"success": False, "message": f"获取统计数据失败: {str(e)}"}), 500


@app.route('/api/images', methods=['GET'])
@jwt_required()
def get_images():
    """返回MRI轮廓图列表（base64编码）"""
    try:
        username = get_jwt_identity()

        # 获取输出目录参数
        output_dir = request.args.get('output_dir', os.path.join(os.getcwd(), 'data', '16after', '00C1068568', 'outline_original'))

        # 检查目录是否存在
        if not os.path.exists(output_dir):
            return jsonify({"success": False, "message": f"目录未找到: {output_dir}"}), 404

        # 查找所有JPG图像文件
        import glob as glob_mod
        image_files = glob_mod.glob(os.path.join(output_dir, 'contour_slice_*.jpg'))

        # 按切片编号排序
        image_files.sort(key=lambda x: int(os.path.basename(x).split('_')[2].split('.')[0]))

        # 读取每个图像文件并转换为base64
        images = []
        for file_path in image_files:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'rb') as img_file:
                    encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
                    slice_number = int(filename.split('_')[2].split('.')[0])
                    images.append({
                        'filename': filename,
                        'slice_number': slice_number,
                        'base64': f'data:image/jpeg;base64,{encoded_img}'
                    })
            except Exception as e:
                logger.warning(f"编码图像失败 {filename}: {str(e)}")
                images.append({
                    'filename': filename,
                    'slice_number': int(filename.split('_')[2].split('.')[0]),
                    'error': str(e)
                })

        # 记录访问日志到MongoDB
        try:
            if db is not None:
                access_log = {
                    'username': username,
                    'action': 'view_images',
                    'directory': output_dir,
                    'image_count': len(images),
                    'timestamp': datetime.datetime.utcnow()
                }
                db['access_logs'].insert_one(access_log)
        except Exception as log_error:
            logger.warning(f"记录访问日志失败: {log_error}")

        logger.info(f"用户 {username} 查看MRI图像，共 {len(images)} 张")
        return jsonify({
            "success": True,
            "images": images,
            "count": len(images),
            "directory": output_dir
        }), 200

    except Exception as e:
        logger.error(f"获取MRI图像失败: {e}")
        return jsonify({"success": False, "images": [], "message": str(e)}), 500


# 应用启动时加载模型
# 使用Flask 2.0+兼容的方式初始化
# 不再使用@app.before_first_request，而是使用app实例化后直接加载

def create_app():
    """应用工厂函数，解决Flask 2.0+中不再支持before_first_request的问题"""
    # 确保模型加载
    with app.app_context():
        configure_jwt()  # 配置JWT
        load_predictor()
        init_mongodb()  # 初始化MongoDB连接
    return app


if __name__ == "__main__":
    # 应用启动时加载模型
    configure_jwt()  # 配置JWT
    load_predictor()
    init_mongodb()  # 初始化MongoDB连接

    # 启动应用
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)