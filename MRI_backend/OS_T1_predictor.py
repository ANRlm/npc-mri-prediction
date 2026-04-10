import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import os
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score, f1_score, precision_score, \
    recall_score
from lifelines import KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts


class OST1Predictor:
    """
    鼻咽癌患者生存预测模型封装类

    该类封装了预训练的Cox比例风险模型，可以根据输入的临床特征和图像特征预测患者的生存情况，
    并输出相关评估指标和生存曲线。
    """

    def __init__(self, model_path='models/adasyn_cox_model.pkl',
                 scaler_path='models/scaler.pkl',
                 info_path='models/adasyn_model_info.pkl'):
        """
        初始化预测器类

        参数:
            model_path: 模型文件路径
            scaler_path: 标准化器文件路径
            info_path: 模型信息文件路径
        """
        self.model = self._load_pickle(model_path)
        self.scaler = self._load_pickle(scaler_path)
        self.model_info = self._load_pickle(info_path)

        # 设置预测所需的特征和阈值
        self.feature_names = self.model_info['feature_names']
        self.optimal_threshold = self.model_info['optimal_threshold']

        # 定义特征列
        self.clinical_features = ['性别', '年龄', 'T分期', 'N分期', '总分期', '治疗前DNA', '治疗后DNA']
        self.pre_features = ['total_area_Mean']
        self.post_features = ['total_area_Skewness', 'avg_centroid_x_Std', 'avg_centroid_x_Kurtosis',
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
        self.categorical_features = []

        # 生存分析相关列
        self.duration_col = 'Ostime'
        self.event_col = 'OS'

    def _load_pickle(self, file_path):
        """加载pickle文件"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            raise Exception(f"加载文件 {file_path} 失败: {str(e)}")

    def predict_with_features(self, merged_data, return_risk_score=False, plot_curves=True):
        """
        使用预训练模型进行预测（基于已合并的数据）

        参数:
            merged_data: 已合并的临床和特征数据的DataFrame，必须包含Patient_ID列和相关特征
            return_risk_score: 是否返回风险评分
            plot_curves: 是否绘制预测曲线

        返回:
            dict: 包含预测结果和评估指标的字典
        """
        # 检查是否包含Patient_ID列
        if 'Patient_ID' not in merged_data.columns:
            raise ValueError("merged_data 必须包含 'Patient_ID' 列")

        # 检查包含的特征数量
        available_features = [col for col in self.feature_names if col in merged_data.columns]
        if len(available_features) < len(self.feature_names) * 0.5:
            print(f"警告: 数据缺少超过50%的必要特征，可能影响预测性能")

        # 处理分类变量
        data_processed = pd.get_dummies(merged_data, columns=self.categorical_features, drop_first=True)

        # 处理缺失值
        data_processed.fillna(data_processed.median(numeric_only=True), inplace=True)

        # 对齐特征，确保与训练模型使用的特征一致
        X_aligned = self._align_features(data_processed)

        # 应用标准化
        X_scaled = pd.DataFrame(self.scaler.transform(X_aligned), columns=X_aligned.columns)

        # 计算风险评分
        risk_scores = self.model.predict(X_scaled)

        # 构建结果数据框
        result_df = pd.DataFrame({
            'Patient_ID': merged_data['Patient_ID'],
            'risk_score': risk_scores
        })

        # 根据阈值划分高低风险组
        result_df['risk_group'] = np.where(result_df['risk_score'] > self.optimal_threshold, '高风险组', '低风险组')

        # 评估指标（如果有生存数据）
        metrics = {}
        has_survival_data = self.duration_col in merged_data.columns and self.event_col in merged_data.columns

        if has_survival_data:
            metrics = self._calculate_metrics(merged_data, result_df)

            # 绘制曲线
            if plot_curves:
                self._plot_curves(merged_data, result_df)

        # 返回结果
        if return_risk_score:
            return {'result': result_df, 'metrics': metrics}
        else:
            return {'result': result_df[['Patient_ID', 'risk_group']], 'metrics': metrics}

    def predict(self, clinical_data, pre_treatment_data=None, post_treatment_data=None,
                return_risk_score=False, plot_curves=True):
        """
        使用预训练模型进行预测

        参数:
            clinical_data: 临床数据DataFrame，必须包含Patient_ID列和相关临床特征
            pre_treatment_data: 预处理图像特征DataFrame，必须包含Patient_ID列和相关特征
            post_treatment_data: 后处理图像特征DataFrame，必须包含Patient_ID列和相关特征
            return_risk_score: 是否返回风险评分
            plot_curves: 是否绘制预测曲线

        返回:
            dict: 包含预测结果和评估指标的字典
        """
        # 处理输入参数，支持合并数据的情况
        if pre_treatment_data is None and post_treatment_data is None:
            # 如果只提供了一个数据框，假设它已经是合并的数据
            return self.predict_with_features(clinical_data, return_risk_score, plot_curves)

        # 继续原来的预测逻辑
        # 检查输入数据是否包含必要的列
        self._check_input_data(clinical_data, pre_treatment_data, post_treatment_data)

        # 合并数据
        merged_data = self._merge_data(clinical_data, pre_treatment_data, post_treatment_data)

        # 使用合并后的数据进行预测
        return self.predict_with_features(merged_data, return_risk_score, plot_curves)

    def _check_input_data(self, clinical_data, pre_treatment_data, post_treatment_data):
        """检查输入数据是否包含必要的列"""
        # 检查Patient_ID列是否存在
        for data, name in zip([clinical_data, pre_treatment_data, post_treatment_data],
                              ['clinical_data', 'pre_treatment_data', 'post_treatment_data']):
            if 'Patient_ID' not in data.columns:
                raise ValueError(f"{name} 必须包含 'Patient_ID' 列")

        # 检查是否包含必要的特征列
        clinical_available = [col for col in self.clinical_features if col in clinical_data.columns]
        pre_available = [col for col in self.pre_features if col in pre_treatment_data.columns]
        post_available = [col for col in self.post_features if col in post_treatment_data.columns]

        if len(clinical_available) < len(self.clinical_features) * 0.5:
            print(f"警告: 临床数据缺少超过50%的必要特征，可能影响预测性能")

        if len(pre_available) < len(self.pre_features) * 0.5:
            print(f"警告: 预处理图像特征缺少超过50%的必要特征，可能影响预测性能")

        if len(post_available) < len(self.post_features) * 0.5:
            print(f"警告: 后处理图像特征缺少超过50%的必要特征，可能影响预测性能")

    def _merge_data(self, clinical_data, pre_treatment_data, post_treatment_data):
        """合并数据集"""
        # 临床数据需要的列
        required_clinical_cols = ['Patient_ID'] + [col for col in self.clinical_features if
                                                   col in clinical_data.columns]
        if self.duration_col in clinical_data.columns:
            required_clinical_cols.append(self.duration_col)
        if self.event_col in clinical_data.columns:
            required_clinical_cols.append(self.event_col)

        # 预处理特征需要的列
        required_pre_cols = ['Patient_ID'] + [col for col in self.pre_features if col in pre_treatment_data.columns]

        # 后处理特征需要的列
        required_post_cols = ['Patient_ID'] + [col for col in self.post_features if col in post_treatment_data.columns]

        # 选择需要的列
        clinical_subset = clinical_data[required_clinical_cols]
        pre_subset = pre_treatment_data[required_pre_cols]
        post_subset = post_treatment_data[required_post_cols]

        # 合并数据
        merged = clinical_subset.merge(pre_subset, on='Patient_ID', how='inner')
        merged = merged.merge(post_subset, on='Patient_ID', how='inner')

        # 处理分类变量
        merged = pd.get_dummies(merged, columns=self.categorical_features, drop_first=True)

        # 处理缺失值
        merged.fillna(merged.median(numeric_only=True), inplace=True)

        return merged

    def _align_features(self, data):
        """确保特征与训练模型使用的特征一致"""
        # 选择需要的特征列
        selected_cols = [col for col in data.columns if col in self.feature_names]
        X = data[selected_cols]

        # 对齐特征列
        X_aligned = pd.DataFrame(index=X.index)
        for feature in self.feature_names:
            if feature in X.columns:
                X_aligned[feature] = X[feature]
            else:
                # 如果缺少特征，填充0
                X_aligned[feature] = 0

        return X_aligned

    def _calculate_metrics(self, data, result_df):
        """计算评估指标"""
        metrics = {}

        # 合并风险评分和生存数据
        eval_df = data.copy()
        eval_df['risk_score'] = result_df['risk_score']

        # 准备scikit-survival格式的数据
        y_structured = np.zeros(len(eval_df), dtype=[('event', bool), ('time', float)])
        y_structured['event'] = eval_df[self.event_col].astype(bool)
        y_structured['time'] = eval_df[self.duration_col].astype(float)

        # 使用阈值进行分类预测
        predictions = eval_df['risk_score'] > self.optimal_threshold

        # 计算评估指标
        y_true = eval_df[self.event_col].astype(bool)
        fpr, tpr, _ = roc_curve(y_true, eval_df['risk_score'])

        # 确定最佳阈值点
        optimal_idx = np.argmax(tpr - fpr)

        metrics['c_index'] = self.model.score(self._align_features(data), y_structured)
        metrics['auc'] = auc(fpr, tpr)
        metrics['sensitivity'] = tpr[optimal_idx]
        metrics['specificity'] = 1 - fpr[optimal_idx]
        metrics['precision'] = precision_score(y_true, predictions)
        metrics['recall'] = recall_score(y_true, predictions)
        metrics['f1'] = f1_score(y_true, predictions)

        # 计算每类的准确率
        tp = np.sum((predictions == True) & (y_true == True))
        tn = np.sum((predictions == False) & (y_true == False))
        fp = np.sum((predictions == True) & (y_true == False))
        fn = np.sum((predictions == False) & (y_true == True))

        positive_accuracy = tp / (tp + fn) if (tp + fn) > 0 else 0
        negative_accuracy = tn / (tn + fp) if (tn + fp) > 0 else 0
        metrics['balanced_accuracy'] = (positive_accuracy + negative_accuracy) / 2

        return metrics

    def _plot_curves(self, data, result_df):
        """绘制ROC曲线和生存曲线"""
        # 合并风险评分和生存数据
        eval_df = data.copy()
        eval_df['risk_score'] = result_df['risk_score']
        eval_df['risk_group'] = result_df['risk_group']

        # 绘制ROC曲线
        y_true = eval_df[self.event_col].astype(bool)
        fpr, tpr, _ = roc_curve(y_true, eval_df['risk_score'])
        roc_auc = auc(fpr, tpr)

        plt.figure(figsize=(6, 6))
        plt.plot(fpr, tpr, color='b', label=f'AUC = {roc_auc:.3f}')
        plt.plot([0, 1], [0, 1], color='r', linestyle='--')
        plt.xlabel("1 - 特异度")
        plt.ylabel("敏感度")
        plt.title("ROC 曲线")
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.show()

        # 绘制生存曲线
        kmf = KaplanMeierFitter()

        plt.figure(figsize=(10, 6))
        kmf.fit(eval_df[eval_df['risk_group'] == '高风险组'][self.duration_col],
                event_observed=eval_df[eval_df['risk_group'] == '高风险组'][self.event_col], label='高风险组')
        kmf.plot(ci_show=False)
        kmf.fit(eval_df[eval_df['risk_group'] == '低风险组'][self.duration_col],
                event_observed=eval_df[eval_df['risk_group'] == '低风险组'][self.event_col], label='低风险组')
        kmf.plot(ci_show=False)

        plt.title("生存曲线")
        plt.xlabel("时间")
        plt.ylabel("生存率")
        add_at_risk_counts(kmf, ax=plt.gca())
        plt.grid(True)
        plt.show()


# 使用示例
def load_example_data():
    """加载示例数据"""
    clinical_path = r"D:\大创实验\newcost\foshan\data\wuzhong\Wuzhou_Clin.xlsx"
    pre_treatment_path = r"D:\大创实验\newcost\foshan\data\wuzhong\counter\pre_T1_statistics.xlsx"
    post_treatment_path = r"D:\大创实验\newcost\foshan\data\wuzhong\counter\post_T1_statistics.xlsx"

    # 读取数据
    clinical_data = pd.read_excel(clinical_path)
    pre_data = pd.read_excel(pre_treatment_path)
    post_data = pd.read_excel(post_treatment_path)

    return clinical_data, pre_data, post_data


def main():
    """主函数，演示如何使用预测器"""
    # 初始化预测器
    predictor = OST1Predictor()

    # 加载示例数据
    clinical_data, pre_data, post_data = load_example_data()

    # 进行预测
    result = predictor.predict(clinical_data, pre_data, post_data)

    # 输出预测结果
    print("\n预测结果:")
    print(result['result'].head())

    # 输出评估指标
    print("\n评估指标:")
    for metric, value in result['metrics'].items():
        print(f"{metric}: {value:.3f}")


if __name__ == "__main__":
    main() 