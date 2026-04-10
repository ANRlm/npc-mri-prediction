import cv2
import numpy as np
import os
import nibabel as nib
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import warnings
from skimage.measure import shannon_entropy
import mahotas
from skimage.transform import rotate
import pandas as pd

warnings.simplefilter(action='ignore', category=FutureWarning)

image_path = 'C:/Users/25049/Desktop/MRI/data/16after/00C1068568/T1.nii.gz'
mask_path = 'C:/Users/25049/Desktop/MRI/data/16after/00C1068568/mask_all.nii.gz'
output_dir = u'C:/Users/25049/Desktop/MRI/data/16after/00C1068568/outline_original'  # 输出目录，用于保存轮廓图像

# 创建输出目录（如果不存在的话）
try:
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录创建成功: {output_dir}")
except Exception as e:
    print(f"创建输出目录时出错: {e}")

# 加载图像和掩膜数据
image_nifti = nib.load(image_path)
mask_nifti = nib.load(mask_path)

# 获取图像和掩膜的 numpy 数组
image_data = image_nifti.get_fdata()
mask_data = mask_nifti.get_fdata()

# 确保掩膜数据为二进制（0 和 1）
binary_mask_data = np.where(mask_data > 0, 1, 0)

# 获取图像的维度
num_slices = image_data.shape[2]

# 存储提取的有效信息层
extracted_slices = []
slice_indices = []

# 提取有效信息的图层
for slice_index in range(num_slices):
    extracted_slice = image_data[:, :, slice_index] * binary_mask_data[:, :, slice_index]
    if np.sum(extracted_slice) > 0:  # 存在有效信息
        extracted_slices.append(extracted_slice)
        slice_indices.append(slice_index)
    else:
        print(f"Slice {slice_index} has no valid information.")

print(f"Extracted {len(extracted_slices)} slices with valid information.")


# 聚类和轮廓提取
def cluster_image(image_slice, n_clusters=4):
    """
    对单层图像进行灰度聚类并返回聚类结果图像
    """
    flattened_data = image_slice.flatten()
    nonzero_indices = np.where(flattened_data > 0)[0]
    nonzero_values = flattened_data[nonzero_indices]

    # 检查非零值是否有效，并 reshape 为二维数组
    if nonzero_values.size == 0:
        raise ValueError("No valid pixels found in the slice for clustering.")
    nonzero_values = nonzero_values.reshape(-1, 1)  # 确保数据形状正确

    # 使用 KMeans 聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(nonzero_values)
    clustered_values = kmeans.labels_

    # 构造聚类结果图像
    clustered_image = np.zeros_like(flattened_data)
    clustered_image[nonzero_indices] = clustered_values + 1
    return clustered_image.reshape(image_slice.shape)


# 计算 Zernike 矩
def calculate_zernike_moments(image, radius=21, degree=8):
    """
    计算图像的 Zernike 矩（使用 mahotas 库）
    :param image: 输入的二值化图像
    :param radius: 半径
    :param degree: 计算的阶数
    :return: Zernike 矩
    """
    return mahotas.features.zernike_moments(image, radius, degree)


# 计算主方向（即主轴）
def calculate_orientation(contour):
    """
    计算给定轮廓的主方向（方向是相对于水平方向的角度）
    """
    moments = cv2.moments(contour)
    if moments["m00"] != 0:
        hu_moments = cv2.HuMoments(moments)
        angle = 0.5 * np.arctan2(2 * moments["m10"], moments["m00"] - moments["m11"])
        angle = np.degrees(angle)
        return angle
    return 0


# 计算信息熵
def calculate_entropy(image):
    """
    计算图像的熵值
    """
    return shannon_entropy(image)


# 计算分形维数
def calculate_fractal_dimension(image):
    """
    使用盒子计数法计算图像的分形维数
    """
    # 将图像转换为二值图像
    binary_image = np.where(image > 0, 1, 0)
    size = binary_image.shape[0]

    # 计算不同盒子大小的计数
    box_sizes = []
    box_counts = []

    for box_size in range(2, size // 2):
        count = 0
        for i in range(0, size, box_size):
            for j in range(0, size, box_size):
                if np.sum(binary_image[i:i + box_size, j:j + box_size]) > 0:
                    count += 1
        box_sizes.append(box_size)
        box_counts.append(count)

    # 计算分形维数
    if not box_sizes or not box_counts:
        return 0

    log_sizes = np.log(box_sizes)
    log_counts = np.log(box_counts)

    # 使用线性回归拟合 log(count) ~ log(size) 来估计分形维数
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    return -coeffs[0]


# 计算轮廓特征（包括面积、周长、圆形度、质心、Hu 矩、斜率、曲率等）
def calculate_contour_features(all_contours_image):
    """
    计算图像 all_contours_image 的轮廓特征：总面积，总周长，总圆形度，总质心，总 Hu 矩、斜率、曲率等
    """
    contours, _ = cv2.findContours(all_contours_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 初始化特征变量
    total_area = 0
    total_perimeter = 0
    total_circularity = 0
    total_centroid_x = 0
    total_centroid_y = 0
    hu_moments_list = []
    slope_list = []
    curvature_list = []
    zernike_moments_list = []
    orientations = []
    entropies = []
    fractal_dimensions = []
    circularity_list = []  # 存储圆形度的列表
    rect_lengths = []  # 存储最小外接矩形长度的列表
    rect_widths = []  # 存储最小外接矩形宽度的列表
    convex_hull_areas = []  # 存储凸包面积的列表
    convex_hull_perimeters = []  # 存储凸包周长的列表
    concavities = []  # 存储凹陷度的列表

    # 遍历所有轮廓并计算特征
    for contour in contours:
        area = cv2.contourArea(contour)
        total_area += area

        perimeter = cv2.arcLength(contour, True)
        total_perimeter += perimeter

        # 计算质心
        moments = cv2.moments(contour)
        if moments["m00"] != 0:
            centroid_x = moments["m10"] / moments["m00"]
            centroid_y = moments["m01"] / moments["m00"]
            total_centroid_x += centroid_x
            total_centroid_y += centroid_y

        # 计算 Hu 矩
        hu_moments = cv2.HuMoments(moments).flatten()
        hu_moments_list.append(hu_moments)

        # 计算斜率和曲率
        if len(contour) > 2:  # 确保至少有3个点才能计算曲率
            for i in range(1, len(contour) - 1):  # 从第二个点开始到倒数第二个点
                # 计算斜率
                dx = contour[i][0][0] - contour[i - 1][0][0]
                dy = contour[i][0][1] - contour[i - 1][0][1]
                slope = np.abs(dy / dx) if dx != 0 else 0  # 避免除以 0，斜率取绝对值
                slope_list.append(slope)

                # 计算曲率
                dx2 = contour[i + 1][0][0] - 2 * contour[i][0][0] + contour[i - 1][0][0]
                dy2 = contour[i + 1][0][1] - 2 * contour[i][0][1] + contour[i - 1][0][1]
                curvature = np.abs(dx2 + dy2)  # 曲率的绝对值
                curvature_list.append(curvature)

        # 计算 Zernike 矩
        zernike_moments = calculate_zernike_moments(all_contours_image)
        zernike_moments_list.append(zernike_moments)

        # 计算主方向
        orientation = calculate_orientation(contour)
        orientations.append(orientation)

        # 计算信息熵
        entropy = calculate_entropy(all_contours_image)
        entropies.append(entropy)

        # 计算分形维数
        fractal_dimension = calculate_fractal_dimension(all_contours_image)
        fractal_dimensions.append(fractal_dimension)

        # 计算圆形度
        if perimeter != 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            circularity_list.append(circularity)

        # 计算最小外接矩形
        rect = cv2.minAreaRect(contour)
        rect_lengths.append(rect[1][0])
        rect_widths.append(rect[1][1])

        # 计算凸包
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        convex_hull_areas.append(hull_area)
        hull_perimeter = cv2.arcLength(hull, True)
        convex_hull_perimeters.append(hull_perimeter)

        # 计算凹陷度
        if hull_area != 0:
            concavity = (hull_area - area) / hull_area
            concavities.append(concavity)

    # 计算平均质心
    num_contours = len(contours)
    if num_contours > 0:
        avg_centroid_x = total_centroid_x / num_contours
        avg_centroid_y = total_centroid_y / num_contours
    else:
        avg_centroid_x = avg_centroid_y = 0

    # 计算 Hu 矩的平均值
    avg_hu_moments = np.mean(hu_moments_list, axis=0) if hu_moments_list else np.zeros(7)

    # 计算斜率和曲率的平均值
    avg_slope = np.mean(slope_list) if slope_list else 0
    avg_curvature = np.mean(curvature_list) if curvature_list else 0

    # 计算 Zernike 矩的平均值
    avg_zernike_moments = np.mean(zernike_moments_list, axis=0) if zernike_moments_list else np.zeros(25)

    # 计算圆形度的平均值
    avg_circularity = np.mean(circularity_list) if circularity_list else 0

    # 计算最小外接矩形的平均长度和宽度
    avg_rect_length = np.mean(rect_lengths) if rect_lengths else 0
    avg_rect_width = np.mean(rect_widths) if rect_widths else 0

    # 计算凸包的平均面积和周长
    avg_convex_hull_area = np.mean(convex_hull_areas) if convex_hull_areas else 0
    avg_convex_hull_perimeter = np.mean(convex_hull_perimeters) if convex_hull_perimeters else 0

    # 计算凹陷度的平均值
    avg_concavity = np.mean(concavities) if concavities else 0

    # 计算主方向的平均值
    avg_orientation = np.mean(orientations) if orientations else 0

    # 计算信息熵的平均值
    avg_entropy = np.mean(entropies) if entropies else 0

    # 计算分形维数的平均值
    avg_fractal_dimension = np.mean(fractal_dimensions) if fractal_dimensions else 0

    return {
        "total_area": total_area,
        "total_perimeter": total_perimeter,
        "avg_centroid": (avg_centroid_x, avg_centroid_y),
        "avg_hu_moments": avg_hu_moments,
        "avg_slope": avg_slope,
        "avg_curvature": avg_curvature,
        "avg_zernike_moments": avg_zernike_moments,
        "avg_orientation": avg_orientation,
        "avg_entropy": avg_entropy,
        "avg_fractal_dimension": avg_fractal_dimension,
        "avg_circularity": avg_circularity,  # 平均圆形度
        "avg_rect_length": avg_rect_length,  # 平均外接矩形长度
        "avg_rect_width": avg_rect_width,  # 平均外接矩形宽度
        "avg_convex_hull_area": avg_convex_hull_area,  # 平均凸包面积
        "avg_convex_hull_perimeter": avg_convex_hull_perimeter,  # 平均凸包周长
        "avg_concavity": avg_concavity  # 平均凹陷度
    }


# 创建一个数据表来保存所有切片的特征
all_features = []
all_slice_indices = []

# 对提取的层逐一聚类并提取轮廓
for i, extracted_slice in enumerate(extracted_slices):
    # 聚类
    clustered_slice = cluster_image(extracted_slice, n_clusters=4)

    # 初始化一个空白图像，用于保存所有聚类的轮廓
    all_contours_image = np.zeros_like(extracted_slice, dtype=np.uint8)

    # 对每个聚类进行轮廓提取
    for cluster_label in range(1, 5):
        # 提取当前聚类的二值化掩膜
        cluster_mask = np.where(clustered_slice == cluster_label, 255, 0).astype(np.uint8)

        # Canny 边缘检测来提取轮廓
        edges = cv2.Canny(cluster_mask, 50, 100)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 绘制轮廓
        if contours:
            all_contours_image = cv2.drawContours(all_contours_image.copy(), contours, -1, 255, 1)

    # 提高轮廓图像的清晰度（对比度拉伸）
    all_contours_image = cv2.equalizeHist(all_contours_image)  # 直方图均衡化

    # 将聚类图像和轮廓图像放在一起
    # 首先将聚类图像转换为合适的数据类型
    clustered_slice = (clustered_slice * 255).astype(np.uint8)
    # 确保两者尺寸相同
    if clustered_slice.shape != all_contours_image.shape:
        min_height = min(clustered_slice.shape[0], all_contours_image.shape[0])
        min_width = min(clustered_slice.shape[1], all_contours_image.shape[1])
        clustered_slice = cv2.resize(clustered_slice, (min_width, min_height))
        all_contours_image = cv2.resize(all_contours_image, (min_width, min_height))

    # 将聚类图像和轮廓图像拼接在一起，这里使用水平拼接
    combined_image = np.hstack((clustered_slice, all_contours_image))

    # 保存轮廓图像
    contour_output_path = os.path.join(output_dir, f'contour_slice_{slice_indices[i] + 1}.jpg')
    print(
        f"正在保存切片 {slice_indices[i] + 1} 的图像，图像形状 {all_contours_image.shape}，数据类型 {all_contours_image.dtype}")

    try:
        # 确保图像数据范围在0-255之间
        if np.max(all_contours_image) > 0:  # 避免保存全黑图像
            normalized_image = all_contours_image.copy()
            # 保存图像
            success = cv2.imwrite(contour_output_path, normalized_image)

            if not success:
                print(f"图像保存失败，尝试使用plt保存")
                plt.imsave(contour_output_path, normalized_image, cmap='gray')
                print(f"使用plt.imsave保存图像到 {contour_output_path}")
        else:
            print(f"切片 {slice_indices[i] + 1} 图像为全黑，跳过保存")
    except Exception as e:
        print(f"保存图像时出错: {e}")

    if np.sum(all_contours_image) == 0:
        print(f"未找到切片 {slice_indices[i] + 1} 的轮廓")
    else:
        print(f"找到切片 {slice_indices[i] + 1} 的轮廓")

    # 计算轮廓特征
    features = calculate_contour_features(all_contours_image)

    # 将特征和切片索引添加到列表中
    feature_row = {
        'Slice_Index': slice_indices[i] + 1,
        'Total_Area': features['total_area'],
        'Total_Perimeter': features['total_perimeter'],
        'Avg_Centroid_X': features['avg_centroid'][0],
        'Avg_Centroid_Y': features['avg_centroid'][1],
        'Avg_Slope': features['avg_slope'],
        'Avg_Curvature': features['avg_curvature'],
        'Avg_Orientation': features['avg_orientation'],
        'Avg_Entropy': features['avg_entropy'],
        'Avg_Fractal_Dimension': features['avg_fractal_dimension'],
        'Avg_Circularity': features['avg_circularity'],
        'Avg_Rect_Length': features['avg_rect_length'],
        'Avg_Rect_Width': features['avg_rect_width'],
        'Avg_Convex_Hull_Area': features['avg_convex_hull_area'],
        'Avg_Convex_Hull_Perimeter': features['avg_convex_hull_perimeter'],
    }

    # Hu矩特征
    for j, moment in enumerate(features['avg_hu_moments']):
        feature_row[f'Hu_Moment_{j + 1}'] = moment

    # Zernike矩特征 (前10个)
    for j, moment in enumerate(features['avg_zernike_moments'][:10]):
        feature_row[f'Zernike_Moment_{j + 1}'] = moment

    all_features.append(feature_row)

    # 打印提取的特征
    print(f"轮廓 {slice_indices[i] + 1} 特征：")
    print(f"  总面积: {features['total_area']}")
    print(f"  总周长: {features['total_perimeter']}")
    print(f"  平均质心: {features['avg_centroid']}")
    print(f"  平均 Hu 矩: {features['avg_hu_moments']}")
    print(f"  平均斜率: {features['avg_slope']}")
    print(f"  平均曲率: {features['avg_curvature']}")
    print(f"  平均 Zernike 矩: {features['avg_zernike_moments']}")
    print(f"  平均主方向: {features['avg_orientation']}")
    print(f"  平均信息熵: {features['avg_entropy']}")
    print(f"  平均分形维数: {features['avg_fractal_dimension']}")
    print(f"  平均圆形度: {features['avg_circularity']}")
    print(f"  平均外接矩形长度: {features['avg_rect_length']}")
    print(f"  平均外接矩形宽度: {features['avg_rect_width']}")
    print(f"  平均凸包面积: {features['avg_convex_hull_area']}")
    print(f"  平均凸包周长: {features['avg_convex_hull_perimeter']}")

    # 显示图像用于调试（可选）
    # cv2.imshow('Contour Image', all_contours_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

# 将所有特征保存为CSV文件
features_df = pd.DataFrame(all_features)
features_output_path = os.path.join(output_dir, 'all_features.csv')
try:
    features_df.to_csv(features_output_path, index=False)
    print(f"特征数据已保存到 {features_output_path}")
except Exception as e:
    print(f"保存特征数据时出错: {e}")

# 直接使用提取的特征计算统计数据
print("开始计算当前数据的统计特征...")
try:
    # 计算基本统计量
    stats_df = features_df.describe().T
    # 添加额外的统计量
    stats_df['Range'] = stats_df['max'] - stats_df['min']
    stats_df['CV'] = stats_df['std'] / stats_df['mean']  # 变异系数
    stats_df['Skewness'] = features_df.skew()  # 偏度
    stats_df['Kurtosis'] = features_df.kurtosis()  # 峰度
    stats_df['IQR'] = stats_df['75%'] - stats_df['25%']  # 四分位距

    # 保存统计数据
    stats_output_path = os.path.join(output_dir, 'features_statistics.xlsx')
    stats_df.to_excel(stats_output_path)
    print(f"统计数据已保存到 {stats_output_path}")
except Exception as e:
    print(f"计算或保存统计数据时出错: {e}")


def calculate_simple_statistics(input_path, output_path):
    """
    为单个病人的特征数据计算简单统计结果，以键值对形式输出
    """
    # 检查all_features.csv是否存在
    features_file = os.path.join(input_path, 'all_features.csv')
    if not os.path.exists(features_file):
        print(f"特征文件不存在: {features_file}")
        return
        
    try:
        # 读取特征数据
        features_df = pd.read_csv(features_file)
        print(f"成功读取特征文件，包含 {len(features_df)} 行数据")
        
        # 移除Slice_Index列（如果存在）
        if 'Slice_Index' in features_df.columns:
            slice_indices = features_df['Slice_Index'].tolist()
            features_df = features_df.drop(columns=['Slice_Index'])
        
        # 计算每个特征的基本统计量（以扁平化形式存储）
        flat_results = {}
        
        for column in features_df.columns:
            # 获取非NaN值
            values = features_df[column].dropna().values
            if len(values) == 0:
                continue
                
            # 计算基本统计量并以扁平化方式存储
            flat_results[f"{column}_Mean"] = np.mean(values)
            flat_results[f"{column}_Median"] = np.median(values)
            flat_results[f"{column}_Min"] = np.min(values)
            flat_results[f"{column}_Max"] = np.max(values)
            flat_results[f"{column}_Range"] = np.max(values) - np.min(values)
            flat_results[f"{column}_Std"] = np.std(values)
            flat_results[f"{column}_Variance"] = np.var(values)
        
        # 将结果保存为JSON格式（扁平化键值对）
        import json
        json_output_path = os.path.join(output_path, 'flat_statistics.json')
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(flat_results, f, indent=4, ensure_ascii=False)
        print(f"扁平化统计数据已保存到 {json_output_path}")
        
        # 同时保存为CSV格式便于查看
        # 将扁平化键值对转换为DataFrame
        flat_df = pd.DataFrame([flat_results])
        csv_output_path = os.path.join(output_path, 'flat_statistics.csv')
        flat_df.to_csv(csv_output_path, index=False)
        print(f"扁平化统计数据CSV版本已保存到 {csv_output_path}")
        
    except Exception as e:
        print(f"计算扁平化统计数据时出错: {e}")


# 使用当前的all_features.csv作为输入
modified_input_path = output_dir
modified_output_path = output_dir
print(f"开始计算简化统计数据，输入路径: {modified_input_path}，输出路径: {modified_output_path}")
calculate_simple_statistics(modified_input_path, modified_output_path)
