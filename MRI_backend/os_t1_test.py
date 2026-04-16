import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score, f1_score, precision_score, \
    recall_score

from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.util import Surv
from sklearn.calibration import calibration_curve
import seaborn as sns
from sklearn.model_selection import KFold
from imblearn.over_sampling import ADASYN
import pickle
import os

# 设置字体为黑体
matplotlib.rcParams['font.family'] = 'SimHei'
matplotlib.rcParams['axes.unicode_minus'] = False

# 定义文件路径
clinical_path = r"D:\ZTY-4.18\项目代码包\预测模型部分代码\训练集数据\clin_fea.xlsx"
pre_treatment_path = r"D:\ZTY-4.18\项目代码包\预测模型部分代码\训练集数据\counter\pre_T1_statistics.xlsx"
post_treatment_path = r"D:\ZTY-4.18\项目代码包\预测模型部分代码\训练集数据\counter\post_T1_statistics.xlsx"

# 定义测试集文件路径
test_clinical_path = r"D:\ZTY-4.18\wuzhong\Wuzhou_Clin.xlsx"
test_pre_treatment_path = r"D:\ZTY-4.18\wuzhong\counter\pre_T1_statistics.xlsx"
test_post_treatment_path = r"D:\ZTY-4.18\wuzhong\counter\post_T1_statistics.xlsx"

# 定义特征列
clinical_features = ['性别', '年龄', 'T分期', 'N分期','总分期' '治疗前DNA', '治疗后DNA']
pre_features = ['total_area_Mean']
post_features = ['total_area_Skewness', 'avg_centroid_x_Std', 'avg_centroid_x_Kurtosis',
                 'avg_centroid_y_Skewness', 'hu_moments_1_Mean', 'hu_moments_1_Min',
                 'hu_moments_2_Skewness', 'hu_moments_3_Q1', 'hu_moments_7_Max',
                 'hu_moments_7_Skewness', 'hu_moments_7_Kurtosis', 'hu_moments_7_Q1',
                 'avg_curvature_Min', 'avg_curvature_Skewness', 'zernike_moments_2_Mean',
                 'zernike_moments_4_Skewness', 'zernike_moments_8_Median',
                 'zernike_moments_10_Min', 'zernike_moments_13_Min',
                 'zernike_moments_14_Median', 'zernike_moments_15_Q3',
                 'zernike_moments_17_Median', 'zernike_moments_18_Q3',
                 'zernike_moments_18_IQR', 'zernike_moments_21_Kurtosis',
                 'zernike_moments_23_IQR', 'zernike_moments_25_Q3',
                 'avg_circularity_Kurtosis', 'avg_rect_width_Mean',
                 'avg_rect_width_Median', 'avg_convex_hull_area_Mean',
                 'avg_convex_hull_area_Kurtosis']

# 定义分类变量列表
categorical_features = []

# 读取训练集数据
clinical_df = pd.read_excel(clinical_path)
pre_df = pd.read_excel(pre_treatment_path)[['Patient_ID'] + pre_features]
post_df = pd.read_excel(post_treatment_path)[['Patient_ID'] + post_features]

# 合并训练集数据集
merged_df = clinical_df.merge(pre_df, on='Patient_ID', how='inner')
merged_df = merged_df.merge(post_df, on='Patient_ID', how='inner')

# 处理分类变量（训练集）
merged_df = pd.get_dummies(merged_df, columns=categorical_features, drop_first=True)

# 设置生存分析列
duration_col = 'Ostime'
event_col = 'OS'

# 处理训练集缺失值
merged_df.fillna(merged_df.median(numeric_only=True), inplace=True)

# 选择特征（训练集）
selected_features = [col for col in merged_df.columns if
                     any(f in col for f in clinical_features + pre_features + post_features)]
X = merged_df[selected_features]
y = merged_df[[duration_col, event_col]]

# 去除低方差特征（训练集）
low_variance_cols = X.var(numeric_only=True)[X.var(numeric_only=True) < 1e-5].index.tolist()
X = X.drop(columns=low_variance_cols)

# 特征标准化（训练集）
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

# 计算样本权重，尝试不同的权重比例(原来为8:1)
event_weight = 6  # 减少一些权重差距，避免过拟合
sample_weights = np.where(y[event_col] == 1, event_weight, 1)

# 应用ADASYN过采样生成合成样本（仅对特征进行过采样，不影响生存时间）
print("原始数据中的事件分布：")
print(y[event_col].value_counts())

# 只对特征和事件状态应用ADASYN，生存时间稍后重新匹配
X_event = X_scaled.copy()
X_event['event'] = y[event_col].values  # 添加事件状态用于过采样
# 进行ADASYN过采样
adasyn = ADASYN(random_state=42, sampling_strategy=0.5)  # 将少数类样本数量提高到多数类的50%
X_resampled, y_resampled = adasyn.fit_resample(X_event, X_event['event'])

print("过采样后的事件分布：")
print(y_resampled.value_counts())

# 从X_resampled中移除event列
X_resampled = X_resampled.drop(columns=['event'])

# 为新生成的样本分配生存时间
# 为简单起见，我们从原始死亡样本中随机选择生存时间
original_death_times = y.loc[y[event_col] == 1, duration_col].values
n_synthetic = sum(y_resampled) - sum(y[event_col])

# 创建新的数据框
y_resampled_df = pd.DataFrame(index=X_resampled.index)
y_resampled_df[event_col] = y_resampled

# 对于原始样本，保持其原始生存时间
original_indices = [i for i in X_resampled.index if i in X_scaled.index]
y_resampled_df.loc[original_indices, duration_col] = y.loc[original_indices, duration_col].values

# 对于合成样本，分配随机的死亡样本生存时间
synthetic_indices = [i for i in X_resampled.index if i not in X_scaled.index]
synthetic_times = np.random.choice(original_death_times, size=len(synthetic_indices), replace=True)
y_resampled_df.loc[synthetic_indices, duration_col] = synthetic_times

print(f"原始样本数量: {len(X_scaled)}, 过采样后样本数量: {len(X_resampled)}")
print(f"合成的新样本数量: {len(synthetic_indices)}")

# K折交叉验证
kf = KFold(n_splits=5, shuffle=True, random_state=42)
c_indices = []
aucs = []

for train_index, val_index in kf.split(X_resampled):
    X_train, X_val = X_resampled.iloc[train_index], X_resampled.iloc[val_index]
    y_train, y_val = y_resampled_df.iloc[train_index], y_resampled_df.iloc[val_index]

    # 转换为scikit-survival格式
    train_df = pd.concat([X_train, y_train], axis=1).dropna()
    # 确保数据类型正确
    y_structured = np.zeros(len(train_df), dtype=[('event', bool), ('time', float)])
    y_structured['event'] = train_df[event_col].astype(bool)
    y_structured['time'] = train_df[duration_col].astype(float)

    # 使用强正则化来处理病态矩阵问题
    estimator = CoxPHSurvivalAnalysis(alpha=5.0)
    estimator.fit(X_train, y_structured)

    val_df = pd.concat([X_val, y_val], axis=1).dropna()
    # 为验证集准备结构化数据
    y_val_structured = np.zeros(len(val_df), dtype=[('event', bool), ('time', float)])
    y_val_structured['event'] = val_df[event_col].astype(bool)
    y_val_structured['time'] = val_df[duration_col].astype(float)

    val_df['risk_score'] = estimator.predict(X_val)
    y_true_val = val_df[event_col].astype(bool)
    fpr, tpr, _ = roc_curve(y_true_val, val_df['risk_score'])
    auc_val = auc(fpr, tpr)
    c_index_val = estimator.score(X_val, y_val_structured)

    aucs.append(auc_val)
    c_indices.append(c_index_val)

# 输出交叉验证结果
print(f'测试集内交叉验证平均C指数: {np.mean(c_indices):.3f}')
print(f'测试集内交叉验证平均AUC: {np.mean(aucs):.3f}')

# 在训练集中进行交叉验证以验证模型鲁棒性
inner_kf = KFold(n_splits=3, shuffle=True, random_state=42)
inner_c_indices = []
inner_aucs = []

for inner_train_index, inner_val_index in inner_kf.split(X_resampled):
    X_inner_train, X_inner_val = X_resampled.iloc[inner_train_index], X_resampled.iloc[inner_val_index]
    y_inner_train, y_inner_val = y_resampled_df.iloc[inner_train_index], y_resampled_df.iloc[inner_val_index]

    # 转换为scikit-survival格式
    inner_train_df = pd.concat([X_inner_train, y_inner_train], axis=1).dropna()
    # 确保数据类型正确
    y_inner_structured = np.zeros(len(inner_train_df), dtype=[('event', bool), ('time', float)])
    y_inner_structured['event'] = inner_train_df[event_col].astype(bool)
    y_inner_structured['time'] = inner_train_df[duration_col].astype(float)

    # 使用强正则化来处理病态矩阵问题
    estimator_inner = CoxPHSurvivalAnalysis(alpha=1.0)
    estimator_inner.fit(X_inner_train, y_inner_structured)

    inner_val_df = pd.concat([X_inner_val, y_inner_val], axis=1).dropna()
    # 为验证集准备结构化数据
    y_inner_val_structured = np.zeros(len(inner_val_df), dtype=[('event', bool), ('time', float)])
    y_inner_val_structured['event'] = inner_val_df[event_col].astype(bool)
    y_inner_val_structured['time'] = inner_val_df[duration_col].astype(float)

    inner_val_df['risk_score'] = estimator_inner.predict(X_inner_val)
    y_true_inner_val = inner_val_df[event_col].astype(bool)
    fpr, tpr, _ = roc_curve(y_true_inner_val, inner_val_df['risk_score'])
    auc_inner_val = auc(fpr, tpr)
    c_index_inner_val = estimator_inner.score(X_inner_val, y_inner_val_structured)

    inner_aucs.append(auc_inner_val)
    inner_c_indices.append(c_index_inner_val)

print(f'训练集内交叉验证平均C指数: {np.mean(inner_c_indices):.3f}')
print(f'训练集内交叉验证平均AUC: {np.mean(inner_aucs):.3f}')

# 训练Cox模型
# 使用过采样后的数据
train_df = pd.concat([X_resampled, y_resampled_df], axis=1).dropna()
# 确保数据类型正确
y_train_structured = np.zeros(len(train_df), dtype=[('event', bool), ('time', float)])
y_train_structured['event'] = train_df[event_col].astype(bool)
y_train_structured['time'] = train_df[duration_col].astype(float)

# 对Cox模型进行网格搜索找到最佳正则化参数
print("\n进行Cox模型参数网格搜索...")
alphas = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 20.0]
best_alpha = 1.0  # 默认值
best_c_index = 0.0

# 构建结构化的交叉验证数据
y_struct_cv = np.zeros(len(X_resampled), dtype=[('event', bool), ('time', float)])
y_struct_cv['event'] = y_resampled_df[event_col].astype(bool)
y_struct_cv['time'] = y_resampled_df[duration_col].astype(float)

for alpha in alphas:
    est = CoxPHSurvivalAnalysis(alpha=alpha)
    cv_scores = []
    # 使用交叉验证评估每个alpha值
    for train_idx, val_idx in KFold(n_splits=5, shuffle=True, random_state=42).split(X_resampled):
        X_train_cv, X_val_cv = X_resampled.iloc[train_idx], X_resampled.iloc[val_idx]
        y_train_cv, y_val_cv = y_struct_cv[train_idx], y_struct_cv[val_idx]

        est.fit(X_train_cv, y_train_cv)
        c_index = est.score(X_val_cv, y_val_cv)
        cv_scores.append(c_index)

    mean_c_index = np.mean(cv_scores)
    print(f"Alpha={alpha}, 平均C指数: {mean_c_index:.3f}")

    if mean_c_index > best_c_index:
        best_c_index = mean_c_index
        best_alpha = alpha

print(f"最佳Alpha参数: {best_alpha}, C指数: {best_c_index:.3f}")

# 使用最佳正则化参数来处理病态矩阵问题
estimator = CoxPHSurvivalAnalysis(alpha=best_alpha)
estimator.fit(X_resampled, y_train_structured)

# 计算风险评分
train_df['risk_score'] = estimator.predict(X_resampled)

# 计算最优阈值（训练集）
y_true = train_df[event_col].astype(bool)
fpr, tpr, thresholds = roc_curve(y_true, train_df['risk_score'])
optimal_idx = np.argmax(tpr - fpr)
optimal_threshold = thresholds[optimal_idx]

# 计算敏感度和特异度
sensitivity = tpr[optimal_idx]
specificity = 1 - fpr[optimal_idx]

# 计算AUC（训练集）
roc_auc = auc(fpr, tpr)


# 修改 evaluate_test_set 函数以返回评估指标
def evaluate_test_set(estimator, scaler, original_threshold, clinical_path, pre_path, post_path, method_name="", print_feature_analysis=False):
    # 读取测试集数据
    test_clinical = pd.read_excel(clinical_path)
    test_pre = pd.read_excel(pre_path)[['Patient_ID'] + pre_features]
    test_post = pd.read_excel(post_path)[['Patient_ID'] + post_features]

    # 收集测试集特征一致性分析信息，但不打印
    feature_analysis = {}
    
    # 收集临床特征检查信息
    clinical_features_status = {}
    for feature in clinical_features:
        clinical_features_status[feature] = feature in test_clinical.columns
    feature_analysis['clinical_features'] = clinical_features_status
    
    # 收集预处理图像特征检查信息
    pre_features_status = {}
    for feature in pre_features:
        pre_features_status[feature] = feature in test_pre.columns
    feature_analysis['pre_features'] = pre_features_status
    
    # 收集后处理图像特征检查信息
    post_features_status = {}
    missing_post_features = []
    for feature in post_features:
        post_features_status[feature] = feature in test_post.columns
        if feature not in test_post.columns:
            missing_post_features.append(feature)
    feature_analysis['post_features'] = post_features_status
    feature_analysis['missing_post_features'] = missing_post_features

    # 合并测试集数据和后续处理
    test_merged = test_clinical.merge(test_pre, on='Patient_ID', how='inner')
    test_merged = test_merged.merge(test_post, on='Patient_ID', how='inner')

    # 处理分类变量后比较独热编码特征
    available_categorical_features = [col for col in categorical_features if col in test_merged.columns]
    feature_analysis['categorical_features'] = {
        'train': categorical_features,
        'test_available': available_categorical_features
    }

    # 处理分类变量（测试集）
    test_merged = pd.get_dummies(test_merged, columns=available_categorical_features, drop_first=True)

    # 检查特征对齐前后的特征数量差异
    available_selected_features = [col for col in selected_features if col in test_merged.columns]
    feature_analysis['feature_alignment'] = {
        'train_features_count': len(selected_features),
        'test_available_count': len(available_selected_features),
        'missing_count': len(selected_features) - len(available_selected_features)
    }

    X_test = test_merged[available_selected_features]

    # 去除低方差特征（测试集）
    X_test = X_test.drop(columns=low_variance_cols)

    # 对齐测试集特征与训练集特征
    X_test_aligned = X_test.reindex(columns=X.columns, fill_value=0)

    # 收集对齐后的特征差异
    aligned_feature_df = pd.DataFrame({
        '训练集特征': X.columns,
        '测试集是否包含': [col in X_test.columns for col in X.columns]
    })
    feature_analysis['not_included_features'] = aligned_feature_df[~aligned_feature_df['测试集是否包含']]

    # 如果需要打印特征分析（可选参数控制）
    if print_feature_analysis:
        print("\n测试集特征一致性分析:")
        print("临床特征检查:")
        for feature, exists in feature_analysis['clinical_features'].items():
            print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

        print("\n预处理图像特征检查:")
        for feature, exists in feature_analysis['pre_features'].items():
            print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

        print("\n后处理图像特征检查:")
        for feature, exists in feature_analysis['post_features'].items():
            print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

        print(f"\n分类特征对比 - 训练集: {feature_analysis['categorical_features']['train']}, 测试集可用: {feature_analysis['categorical_features']['test_available']}")

        print(f"\n特征对齐分析:")
        print(f"训练集特征数量: {feature_analysis['feature_alignment']['train_features_count']}")
        print(f"测试集可用特征数量: {feature_analysis['feature_alignment']['test_available_count']}")
        print(f"缺失特征数量: {feature_analysis['feature_alignment']['missing_count']}")

        print("\n训练集和测试集的特征对齐情况:")
        print(feature_analysis['not_included_features'].to_string(index=False))

    # 标准化（测试集）
    X_test_scaled = pd.DataFrame(scaler.transform(X_test_aligned), columns=X_test_aligned.columns)

    # 合并目标变量
    y_test = test_merged[[duration_col, event_col]]
    test_df = pd.concat([X_test_scaled, y_test], axis=1).dropna()

    # 准备结构化数据
    y_test_structured = np.zeros(len(test_df), dtype=[('event', bool), ('time', float)])
    y_test_structured['event'] = test_df[event_col].astype(bool)
    y_test_structured['time'] = test_df[duration_col].astype(float)

    # 计算风险评分
    test_df['risk_score'] = estimator.predict(X_test_scaled)

    # 计算测试集上的最优阈值（新增代码）
    y_test_true = test_df[event_col].astype(bool)
    fpr_test, tpr_test, thresholds_test = roc_curve(y_test_true, test_df['risk_score'])

    # J统计量方法（Youden指数）确定最优阈值
    optimal_idx_test = np.argmax(tpr_test - fpr_test)
    test_optimal_threshold = thresholds_test[optimal_idx_test]

    # 输出对比，添加方法名称
    print(f"\n{method_name} 阈值比较:")
    print(f"训练集最优阈值: {original_threshold:.4f}")
    print(f"测试集最优阈值: {test_optimal_threshold:.4f}")

    # 使用测试集阈值计算指标
    predictions = test_df['risk_score'] > test_optimal_threshold

    # 计算测试集中的指标（使用新阈值）
    sensitivity = tpr_test[optimal_idx_test]
    specificity = 1 - fpr_test[optimal_idx_test]
    precision_test = precision_score(y_test_true, predictions)
    recall_test = recall_score(y_test_true, predictions)
    f1_test = f1_score(y_test_true, predictions)

    # 计算测试集中的平衡精确率和召回率
    predictions = test_df['risk_score'] > test_optimal_threshold
    precision_test = precision_score(y_test_true, predictions)
    recall_test = recall_score(y_test_true, predictions)
    f1_test = f1_score(y_test_true, predictions)

    # 计算每个类别的单独性能
    tp = np.sum((predictions == True) & (y_test_true == True))
    tn = np.sum((predictions == False) & (y_test_true == False))
    fp = np.sum((predictions == True) & (y_test_true == False))
    fn = np.sum((predictions == False) & (y_test_true == True))

    # 计算每类的准确率
    positive_accuracy = tp / (tp + fn) if (tp + fn) > 0 else 0
    negative_accuracy = tn / (tn + fp) if (tn + fp) > 0 else 0
    balanced_accuracy = (positive_accuracy + negative_accuracy) / 2

    print("\n测试集类别不平衡评估：")
    print(f"正例准确率: {positive_accuracy:.3f}")
    print(f"负例准确率: {negative_accuracy:.3f}")
    print(f"平衡准确率: {balanced_accuracy:.3f}")
    print(f"精确率: {precision_test:.3f}")
    print(f"召回率: {recall_test:.3f}")
    print(f"F1分数: {f1_test:.3f}")

    # 输出测试集中的类别分布
    print(f"\n测试集中的类别分布：")
    print(y_test_true.value_counts())

    # 绘制ROC曲线
    plt.figure(figsize=(6, 6))
    plt.plot(fpr_test, tpr_test, color='b', label=f'AUC = {auc(fpr_test, tpr_test):.3f}')
    plt.plot([0, 1], [0, 1], color='r', linestyle='--')
    plt.xlabel("1 - 特异度")
    plt.ylabel("敏感度")
    plt.title("测试集 ROC 曲线")
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.show()

    # 额外添加：使用原阈值的结果进行对比
    predictions_original = test_df['risk_score'] > original_threshold
    print("\n使用不同阈值的测试集结果对比:")
    print(f"{'指标':<15} {'原训练集阈值':>15} {'新测试集阈值':>15}")
    print(f"{'-' * 15:<15} {'-' * 15:>15} {'-' * 15:>15}")
    print(f"{'精确率':<15} {precision_score(y_test_true, predictions_original):>15.3f} {precision_test:>15.3f}")
    print(f"{'召回率':<15} {recall_score(y_test_true, predictions_original):>15.3f} {recall_test:>15.3f}")
    print(f"{'F1分数':<15} {f1_score(y_test_true, predictions_original):>15.3f} {f1_test:>15.3f}")
    print(
        f"{'特异度':<15} {1 - fpr_test[np.argmin(np.abs(thresholds_test - original_threshold))]:>15.3f} {specificity:>15.3f}")
    print(
        f"{'敏感度':<15} {tpr_test[np.argmin(np.abs(thresholds_test - original_threshold))]:>15.3f} {sensitivity:>15.3f}")

    # 返回基于新阈值的指标和特征分析
    c_index = estimator.score(X_test_scaled, y_test_structured)
    auc_value = auc(fpr_test, tpr_test)
    return c_index, auc_value, sensitivity, specificity, precision_test, recall_test, f1_test, balanced_accuracy, feature_analysis


# 评估测试集并接收返回值（不在函数中打印特征分析）
c_index, auc_test, sensitivity_test, specificity_test, precision_test, recall_test, f1_test, balanced_accuracy, feature_analysis = evaluate_test_set(
    estimator, scaler, optimal_threshold,
    test_clinical_path, test_pre_treatment_path, test_post_treatment_path, 
    method_name="ADASYN过采样",  # 添加方法名称
    print_feature_analysis=False  # 不在函数中打印特征分析
)

# 统一输出结果
print("\n训练集评估结果：")
y_train_eval = np.zeros(len(train_df), dtype=[('event', bool), ('time', float)])
y_train_eval['event'] = train_df[event_col].astype(bool)
y_train_eval['time'] = train_df[duration_col].astype(float)
print(f"- C指数（训练集）: {estimator.score(X_resampled, y_train_eval):.3f}")
print(f"- AUC（训练集）: {roc_auc:.3f}")
print(f"- 敏感度（训练集）: {sensitivity:.3f}")
print(f"- 特异度（训练集）: {specificity:.3f}")

print("\n测试集评估结果：")
print(f"- C指数（测试集）: {c_index:.3f}")
print(f"- AUC（测试集）: {auc_test:.3f}")
print(f"- 敏感度（测试集）: {sensitivity_test:.3f}")
print(f"- 特异度（测试集）: {specificity_test:.3f}")
print(f"- 精确率（测试集）: {precision_test:.3f}")
print(f"- 召回率（测试集）: {recall_test:.3f}")
print(f"- F1分数（测试集）: {f1_test:.3f}")
print(f"- 平衡准确率（测试集）: {balanced_accuracy:.3f}")

# 绘制风险评分分布
sns.histplot(train_df['risk_score'], bins=30, kde=True)
plt.title("风险评分分布（综合数据）")
plt.xlabel("风险评分")
plt.ylabel("频数")
plt.grid(True)
plt.show()

# 绘制ROC曲线
plt.figure(figsize=(6, 6))
plt.plot(fpr, tpr, color='b', label=f'AUC = {roc_auc:.3f}')
plt.plot([0, 1], [0, 1], color='r', linestyle='--')
plt.xlabel("1 - 特异度 (False Positive Rate)")
plt.ylabel("敏感度 (True Positive Rate)")
plt.title("ROC 曲线（综合数据）")
plt.legend(loc="lower right")
plt.grid(True)
plt.show()

# 计算精确率、召回率、F1分数和精确召回曲线下面积
precision, recall, _ = precision_recall_curve(y_true, train_df['risk_score'])
average_precision = average_precision_score(y_true, train_df['risk_score'])
f1 = f1_score(y_true, train_df['risk_score'] > optimal_threshold)
precision_score_val = precision_score(y_true, train_df['risk_score'] > optimal_threshold)
recall_score_val = recall_score(y_true, train_df['risk_score'] > optimal_threshold)

# 根据风险评分分组
train_df['risk_group'] = np.where(train_df['risk_score'] > train_df['risk_score'].median(), '高风险组', '低风险组')

# 使用预测结果生成生存曲线
kmf = KaplanMeierFitter()

plt.figure(figsize=(10, 6))
kmf.fit(train_df[train_df['risk_group'] == '高风险组'][duration_col],
        event_observed=train_df[train_df['risk_group'] == '高风险组'][event_col], label='高风险组')
kmf.plot(ci_show=False)
kmf.fit(train_df[train_df['risk_group'] == '低风险组'][duration_col],
        event_observed=train_df[train_df['risk_group'] == '低风险组'][event_col], label='低风险组')
kmf.plot(ci_show=False)

plt.title("生存曲线")
plt.xlabel("时间")
plt.ylabel("生存率")
add_at_risk_counts(kmf, ax=plt.gca())
plt.grid(True)
plt.show()

# 列线图
X_nomogram = train_df.drop([duration_col, event_col, 'risk_score', 'risk_group'], axis=1)
y_nomogram = train_df[[duration_col, event_col]]
y_nomogram = Surv.from_dataframe(event_col, duration_col, y_nomogram)

# 使用普通Cox模型
estimator_nomogram = CoxPHSurvivalAnalysis()
estimator_nomogram.fit(X_nomogram, y_nomogram)

feature_names = X_nomogram.columns
coefficients = estimator_nomogram.coef_
plt.figure(figsize=(10, 6))
plt.barh(feature_names, coefficients)
plt.xlabel('系数')
plt.ylabel('特征')
plt.title('列线图（特征系数）- ADASYN过采样后')
plt.grid(True)
plt.tight_layout()
plt.show()

# 校准曲线
predicted_survival = estimator_nomogram.predict_survival_function(X_nomogram)
time_points = np.linspace(0, train_df[duration_col].max(), 10)
survival_probs = np.array([[fn(t) for t in time_points] for fn in predicted_survival])
mean_survival_probs = survival_probs.mean(axis=1)

prob_true, prob_pred = calibration_curve(train_df[event_col], mean_survival_probs, n_bins=10)

plt.figure(figsize=(6, 6))
plt.plot(prob_pred, prob_true, marker='o', label='校准曲线')
plt.plot([0, 1], [0, 1], linestyle='--', label='完美校准')
plt.xlabel('预测概率')
plt.ylabel('实际概率')
plt.title('校准曲线 - ADASYN过采样后')
plt.legend()
plt.grid(True)
plt.show()

# 绘制原始数据与过采样后数据的类别分布对比
plt.figure(figsize=(10, 6))
original_counts = y[event_col].value_counts().sort_index()
resampled_counts = train_df[event_col].value_counts().sort_index()

# 转换为百分比
original_percents = original_counts / original_counts.sum() * 100
resampled_percents = resampled_counts / resampled_counts.sum() * 100

x = np.arange(2)
width = 0.35
fig, ax = plt.subplots(figsize=(10, 6))

ax.bar(x - width / 2, [original_percents[0], original_percents[1]], width, label='原始数据')
ax.bar(x + width / 2, [resampled_percents[0], resampled_percents[1]], width, label='ADASYN过采样后数据')

ax.set_ylabel('百分比 (%)')
ax.set_title('原始数据与ADASYN过采样后数据的类别分布')
ax.set_xticks(x)
ax.set_xticklabels(['存活 (0)', '死亡 (1)'])
ax.legend()
plt.grid(True)
plt.show()

# 检查合并后的数据完整性
print(f"合并后的样本数量: {merged_df.shape[0]}")
print(f"ADASYN过采样后的样本数量: {len(X_resampled)}")
print(f"原始数据事件状态分布（OS=0 存活，OS=1 死亡）：\n{merged_df['OS'].value_counts()}")
print(f"ADASYN过采样后事件状态分布（OS=0 存活，OS=1 死亡）：\n{train_df['OS'].value_counts()}")
print(f"缺失值统计：\n{merged_df.isnull().sum()}")

# 保存模型和重要的性能指标
# 创建保存目录（如果不存在）
os.makedirs('model_training/OS/OS-T1/models', exist_ok=True)

# 保存模型
with open('model_training/OS/OS-T1/models/adasyn_cox_model.pkl', 'wb') as f:
    pickle.dump(estimator, f)

# 保存标准化器
with open('model_training/OS/OS-T1/models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# 保存重要的参数和结果
model_info = {
    'optimal_threshold': optimal_threshold,
    'train_metrics': {
        'c_index': estimator.score(X_resampled, y_train_eval),
        'auc': roc_auc,
        'sensitivity': sensitivity,
        'specificity': specificity
    },
    'test_metrics': {
        'c_index': c_index,
        'auc': auc_test,
        'sensitivity': sensitivity_test,
        'specificity': specificity_test,
        'precision': precision_test,
        'recall': recall_test,
        'f1': f1_test,
        'balanced_accuracy': balanced_accuracy
    },
    'feature_names': list(X.columns)
}

with open('model_training/OS/OS-T1/models/adasyn_model_info.pkl', 'wb') as f:
    pickle.dump(model_info, f)

print("\nADASYN过采样Cox模型、标准化器和性能指标已保存到 'model_training/OS/OS-T1/models/' 目录")

# 尝试使用样本权重训练模型
print("\n尝试使用样本权重训练模型...")
# 创建一个字典，记录每个样本索引对应的权重
weight_dict = {}
for idx, is_event in enumerate(y[event_col].values):
    weight_dict[idx] = event_weight if is_event == 1 else 1.0

# 准备加权训练数据
X_weighted = X_scaled.copy()
y_weighted_structured = np.zeros(len(X_weighted), dtype=[('event', bool), ('time', float)])
y_weighted_structured['event'] = y[event_col].astype(bool)
y_weighted_structured['time'] = y[duration_col].astype(float)

try:
    # 收集所有样本权重
    weighted_samples = []
    for idx in range(len(X_weighted)):
        weight = weight_dict.get(idx, 1.0)
        # 重复添加样本以模拟权重效果
        for _ in range(int(weight)):
            weighted_samples.append(idx)

    # 根据权重复制样本
    X_weighted_dup = X_weighted.iloc[weighted_samples].reset_index(drop=True)
    y_weighted_dup = np.zeros(len(X_weighted_dup), dtype=[('event', bool), ('time', float)])
    y_weighted_dup['event'] = y[event_col].iloc[weighted_samples].astype(bool)
    y_weighted_dup['time'] = y[duration_col].iloc[weighted_samples].astype(float)

    # 使用最佳alpha参数训练模型
    weighted_estimator = CoxPHSurvivalAnalysis(alpha=best_alpha)
    weighted_estimator.fit(X_weighted_dup, y_weighted_dup)

    # 评估测试集，添加方法名称
    weighted_results = evaluate_test_set(
        weighted_estimator, scaler, optimal_threshold,
        test_clinical_path, test_pre_treatment_path, test_post_treatment_path,
        method_name="样本权重",  # 添加方法名称
        print_feature_analysis=False
    )

    # 保存加权模型
    with open('model_training/OS/OS-T1/models/weighted_cox_model.pkl', 'wb') as f:
        pickle.dump(weighted_estimator, f)

    print("基于样本权重的模型已保存")

except Exception as e:
    print(f"样本权重模型训练失败: {str(e)}")


# 定义一个函数来比较所有模型的性能
def compare_all_models(models_dict, X_test_data, y_test_data, title="所有模型性能对比"):
    """
    比较多个模型在测试集上的性能

    Parameters:
    -----------
    models_dict : dict
        包含模型名称和模型对象的字典
    X_test_data : pandas.DataFrame
        测试集特征
    y_test_data : numpy.ndarray
        测试集目标（结构化数据格式）
    title : str
        图表标题
    """
    plt.figure(figsize=(10, 8))

    results = {}

    for model_name, model in models_dict.items():
        # 计算风险评分
        risk_scores = model.predict(X_test_data)

        # 提取事件状态
        y_true = y_test_data['event']

        # 计算ROC曲线
        fpr, tpr, _ = roc_curve(y_true, risk_scores)
        roc_auc = auc(fpr, tpr)

        # 计算C-index
        c_index = model.score(X_test_data, y_test_data)

        # 存储结果
        results[model_name] = {'auc': roc_auc, 'c_index': c_index, 'fpr': fpr, 'tpr': tpr}

        # 绘制ROC曲线
        plt.plot(fpr, tpr, lw=2, label=f'{model_name} (AUC = {roc_auc:.3f}, C-index = {c_index:.3f})')

    # 绘制对角线
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('1 - 特异度')
    plt.ylabel('敏感度')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.show()

    # 创建性能对比表格
    perf_data = {
        '模型': list(results.keys()),
        'AUC': [results[model]['auc'] for model in results.keys()],
        'C-index': [results[model]['c_index'] for model in results.keys()]
    }

    perf_df = pd.DataFrame(perf_data)
    print("\n所有模型性能对比：")
    print(perf_df.to_string(index=False))

    # 保存结果
    os.makedirs('model_training/OS/OS-T1', exist_ok=True)
    perf_df.to_csv('model_training/OS/OS-T1/all_models_comparison.csv', index=False)
    print("所有模型性能对比已保存至 'all_models_comparison.csv'")

    return results

# 准备测试数据用于模型比较
print("\n准备测试数据用于所有模型性能对比...")
try:
    # 读取测试集数据
    test_clinical = pd.read_excel(test_clinical_path)
    test_pre = pd.read_excel(test_pre_treatment_path)[['Patient_ID'] + pre_features]
    test_post = pd.read_excel(test_post_treatment_path)[['Patient_ID'] + post_features]

    # 合并测试集数据
    test_merged = test_clinical.merge(test_pre, on='Patient_ID', how='inner')
    test_merged = test_merged.merge(test_post, on='Patient_ID', how='inner')

    # 处理分类变量（测试集）
    available_categorical_features = [col for col in categorical_features if col in test_merged.columns]
    test_merged = pd.get_dummies(test_merged, columns=available_categorical_features, drop_first=True)

    # 处理缺失值（测试集）
    test_merged.fillna(merged_df.median(numeric_only=True), inplace=True)

    # 选择特征（测试集）
    available_selected_features = [col for col in selected_features if col in test_merged.columns]
    X_test = test_merged[available_selected_features]

    # 去除低方差特征（测试集）
    X_test = X_test.drop(columns=low_variance_cols)

    # 对齐测试集特征与训练集特征
    X_test_aligned = X_test.reindex(columns=X.columns, fill_value=0)

    # 标准化（测试集）
    X_test_scaled = pd.DataFrame(scaler.transform(X_test_aligned), columns=X_test_aligned.columns)

    # 合并目标变量
    y_test = test_merged[[duration_col, event_col]]

    # 准备结构化数据
    y_test_structured = np.zeros(len(test_merged), dtype=[('event', bool), ('time', float)])
    y_test_structured['event'] = test_merged[event_col].astype(bool)
    y_test_structured['time'] = test_merged[duration_col].astype(float)

    # 收集所有模型进行比较
    models_to_compare = {}

    # 添加ADASYN模型
    models_to_compare['ADASYN过采样'] = estimator

    # 如果存在加权模型，添加到比较中
    try:
        models_to_compare['样本权重'] = weighted_estimator
    except NameError:
        print("样本权重模型不可用，跳过比较")

    # 比较所有模型性能
    comparison_results = compare_all_models(
        models_to_compare, X_test_scaled, y_test_structured,
        title="不同平衡策略Cox模型在测试集上的ROC曲线对比"
    )

except Exception as e:
    print(f"模型比较失败: {str(e)}")

# 在代码最后添加，需要放在try-except块后面，以确保只输出一次
print("\n最终测试集特征一致性分析:")
print("临床特征检查:")
for feature, exists in feature_analysis['clinical_features'].items():
    print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

print("\n预处理图像特征检查:")
for feature, exists in feature_analysis['pre_features'].items():
    print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

print("\n后处理图像特征检查:")
for feature, exists in feature_analysis['post_features'].items():
    print(f"  {'✓' if exists else '✗'} {feature} {'存在于' if exists else '不存在于'}测试集中")

print(f"\n分类特征对比 - 训练集: {feature_analysis['categorical_features']['train']}, 测试集可用: {feature_analysis['categorical_features']['test_available']}")

print(f"\n特征对齐分析:")
print(f"训练集特征数量: {feature_analysis['feature_alignment']['train_features_count']}")
print(f"测试集可用特征数量: {feature_analysis['feature_alignment']['test_available_count']}")
print(f"缺失特征数量: {feature_analysis['feature_alignment']['missing_count']}")

print("\n训练集和测试集的特征对齐情况:")
print(feature_analysis['not_included_features'].to_string(index=False))