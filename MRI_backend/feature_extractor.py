# -*- coding: utf-8 -*-
"""Radiomics feature extraction for NPC MRI prediction pipeline.

Reusable module that extracts per-slice shape/texture features from a NIfTI
image + mask pair and aggregates them into a flat dict whose keys match the
model's feature names exactly (e.g. ``total_area_Mean``, ``hu_moments_1_Q1``,
``zernike_moments_10_Min``).

The extraction logic mirrors ``combined_features3.py`` but is packaged as a
reusable function with no hardcoded paths or side effects.
"""
from __future__ import annotations

import warnings
from typing import Dict, List

import numpy as np

warnings.simplefilter(action="ignore", category=FutureWarning)

# Heavy imaging deps are imported lazily inside extract_features() so that the
# module can be imported even when they are missing (the Flask endpoint uses
# this to return a clear 503 error).

# Base per-slice scalar feature names (no index suffix).
_SCALAR_FEATURES: List[str] = [
    "total_area",
    "total_perimeter",
    "avg_centroid_x",
    "avg_centroid_y",
    "avg_slope",
    "avg_curvature",
    "avg_orientation",
    "avg_entropy",
    "avg_fractal_dimension",
    "avg_circularity",
    "avg_rect_length",
    "avg_rect_width",
    "avg_convex_hull_area",
    "avg_convex_hull_perimeter",
]

# Statistic names used as suffixes (must match model feature names).
_STAT_NAMES: List[str] = [
    "Mean",
    "Median",
    "Min",
    "Max",
    "Range",
    "Std",
    "Variance",
    "Skewness",
    "Kurtosis",
    "Q1",
    "Q3",
    "IQR",
]

# Number of indexed moment features.
_NUM_HU = 7
_NUM_ZERNIKE = 25


def _compute_stats(values: np.ndarray) -> Dict[str, float]:
    """Compute the 12 statistics for a 1D array of per-slice values."""
    from scipy import stats as _scipy_stats

    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]

    if values.size == 0:
        return {name: 0.0 for name in _STAT_NAMES}

    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))

    if values.size >= 2:
        skew = float(_scipy_stats.skew(values, bias=False))
        kurt = float(_scipy_stats.kurtosis(values, fisher=True, bias=False))
    else:
        skew = 0.0
        kurt = 0.0

    mean = float(np.mean(values))
    median = float(np.median(values))
    vmin = float(np.min(values))
    vmax = float(np.max(values))

    return {
        "Mean": mean,
        "Median": median,
        "Min": vmin,
        "Max": vmax,
        "Range": vmax - vmin,
        "Std": float(np.std(values)),
        "Variance": float(np.var(values)),
        "Skewness": skew if np.isfinite(skew) else 0.0,
        "Kurtosis": kurt if np.isfinite(kurt) else 0.0,
        "Q1": q1,
        "Q3": q3,
        "IQR": q3 - q1,
    }


def _empty_feature_dict() -> Dict[str, float]:
    """Return a feature dict with all model feature names set to 0.0."""
    out: Dict[str, float] = {}
    for name in _SCALAR_FEATURES:
        for stat in _STAT_NAMES:
            out[f"{name}_{stat}"] = 0.0
    for i in range(1, _NUM_HU + 1):
        for stat in _STAT_NAMES:
            out[f"hu_moments_{i}_{stat}"] = 0.0
    for i in range(1, _NUM_ZERNIKE + 1):
        for stat in _STAT_NAMES:
            out[f"zernike_moments_{i}_{stat}"] = 0.0
    return out


def _cluster_image(image_slice: np.ndarray, n_clusters: int = 4) -> np.ndarray:
    """KMeans cluster non-zero pixels of a 2D slice."""
    from sklearn.cluster import KMeans

    flat = image_slice.flatten()
    nz_idx = np.where(flat > 0)[0]
    if nz_idx.size == 0:
        return np.zeros_like(image_slice, dtype=np.int32)

    nz_vals = flat[nz_idx].reshape(-1, 1)
    k = min(n_clusters, max(1, nz_vals.shape[0]))
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(nz_vals)

    labels = np.zeros_like(flat, dtype=np.int32)
    labels[nz_idx] = kmeans.labels_ + 1
    return labels.reshape(image_slice.shape)


def _calculate_zernike_moments(image: np.ndarray, radius: int = 21, degree: int = 8) -> np.ndarray:
    import mahotas

    moments = mahotas.features.zernike_moments(image, radius, degree)
    if moments.shape[0] < _NUM_ZERNIKE:
        padded = np.zeros(_NUM_ZERNIKE, dtype=float)
        padded[: moments.shape[0]] = moments
        return padded
    return moments[:_NUM_ZERNIKE]


def _calculate_orientation(contour) -> float:
    import cv2

    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return 0.0
    angle = 0.5 * np.arctan2(2 * moments["m10"], moments["m00"] - moments["m11"])
    return float(np.degrees(angle))


def _calculate_entropy(image: np.ndarray) -> float:
    from skimage.measure import shannon_entropy

    return float(shannon_entropy(image))


def _calculate_fractal_dimension(image: np.ndarray) -> float:
    binary = np.where(image > 0, 1, 0)
    size = binary.shape[0]
    if size < 4:
        return 0.0

    box_sizes = []
    box_counts = []
    for box_size in range(2, size // 2):
        count = 0
        for i in range(0, size, box_size):
            for j in range(0, size, box_size):
                if np.sum(binary[i : i + box_size, j : j + box_size]) > 0:
                    count += 1
        box_sizes.append(box_size)
        box_counts.append(count)

    if not box_sizes or not box_counts:
        return 0.0

    box_counts_arr = np.array(box_counts, dtype=float)
    box_sizes_arr = np.array(box_sizes, dtype=float)
    # Guard against log(0)
    if np.any(box_counts_arr <= 0):
        mask = box_counts_arr > 0
        if mask.sum() < 2:
            return 0.0
        box_counts_arr = box_counts_arr[mask]
        box_sizes_arr = box_sizes_arr[mask]

    log_sizes = np.log(box_sizes_arr)
    log_counts = np.log(box_counts_arr)
    coeffs = np.polyfit(log_sizes, log_counts, 1)
    return float(-coeffs[0])


def _slice_features(all_contours_image: np.ndarray) -> Dict[str, float]:
    """Compute per-slice feature dict for a single contour image.

    Returns a dict with scalar keys (``total_area`` etc.), plus
    ``hu_moments_{i}`` (i=1..7) and ``zernike_moments_{i}`` (i=1..25).
    """
    import cv2

    contours, _ = cv2.findContours(all_contours_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    total_area = 0.0
    total_perimeter = 0.0
    total_centroid_x = 0.0
    total_centroid_y = 0.0
    hu_moments_list: List[np.ndarray] = []
    slope_list: List[float] = []
    curvature_list: List[float] = []
    zernike_moments_list: List[np.ndarray] = []
    orientations: List[float] = []
    entropies: List[float] = []
    fractal_dimensions: List[float] = []
    circularity_list: List[float] = []
    rect_lengths: List[float] = []
    rect_widths: List[float] = []
    convex_hull_areas: List[float] = []
    convex_hull_perimeters: List[float] = []

    centroid_count = 0

    for contour in contours:
        area = float(cv2.contourArea(contour))
        total_area += area

        perimeter = float(cv2.arcLength(contour, True))
        total_perimeter += perimeter

        moments = cv2.moments(contour)
        if moments["m00"] != 0:
            total_centroid_x += moments["m10"] / moments["m00"]
            total_centroid_y += moments["m01"] / moments["m00"]
            centroid_count += 1

        hu = cv2.HuMoments(moments).flatten()
        hu_moments_list.append(hu)

        if len(contour) > 2:
            for i in range(1, len(contour) - 1):
                dx = contour[i][0][0] - contour[i - 1][0][0]
                dy = contour[i][0][1] - contour[i - 1][0][1]
                slope = abs(dy / dx) if dx != 0 else 0.0
                slope_list.append(float(slope))

                dx2 = contour[i + 1][0][0] - 2 * contour[i][0][0] + contour[i - 1][0][0]
                dy2 = contour[i + 1][0][1] - 2 * contour[i][0][1] + contour[i - 1][0][1]
                curvature_list.append(float(abs(dx2 + dy2)))

        zernike_moments_list.append(_calculate_zernike_moments(all_contours_image))
        orientations.append(_calculate_orientation(contour))
        entropies.append(_calculate_entropy(all_contours_image))
        fractal_dimensions.append(_calculate_fractal_dimension(all_contours_image))

        if perimeter != 0:
            circularity_list.append(4 * np.pi * area / (perimeter * perimeter))

        rect = cv2.minAreaRect(contour)
        rect_lengths.append(float(rect[1][0]))
        rect_widths.append(float(rect[1][1]))

        hull = cv2.convexHull(contour)
        hull_area = float(cv2.contourArea(hull))
        convex_hull_areas.append(hull_area)
        convex_hull_perimeters.append(float(cv2.arcLength(hull, True)))

    avg_centroid_x = total_centroid_x / centroid_count if centroid_count > 0 else 0.0
    avg_centroid_y = total_centroid_y / centroid_count if centroid_count > 0 else 0.0
    avg_hu = np.mean(hu_moments_list, axis=0) if hu_moments_list else np.zeros(_NUM_HU)
    avg_zernike = np.mean(zernike_moments_list, axis=0) if zernike_moments_list else np.zeros(_NUM_ZERNIKE)

    out: Dict[str, float] = {
        "total_area": total_area,
        "total_perimeter": total_perimeter,
        "avg_centroid_x": float(avg_centroid_x),
        "avg_centroid_y": float(avg_centroid_y),
        "avg_slope": float(np.mean(slope_list)) if slope_list else 0.0,
        "avg_curvature": float(np.mean(curvature_list)) if curvature_list else 0.0,
        "avg_orientation": float(np.mean(orientations)) if orientations else 0.0,
        "avg_entropy": float(np.mean(entropies)) if entropies else 0.0,
        "avg_fractal_dimension": float(np.mean(fractal_dimensions)) if fractal_dimensions else 0.0,
        "avg_circularity": float(np.mean(circularity_list)) if circularity_list else 0.0,
        "avg_rect_length": float(np.mean(rect_lengths)) if rect_lengths else 0.0,
        "avg_rect_width": float(np.mean(rect_widths)) if rect_widths else 0.0,
        "avg_convex_hull_area": float(np.mean(convex_hull_areas)) if convex_hull_areas else 0.0,
        "avg_convex_hull_perimeter": float(np.mean(convex_hull_perimeters)) if convex_hull_perimeters else 0.0,
    }

    for i in range(_NUM_HU):
        out[f"hu_moments_{i + 1}"] = float(avg_hu[i])
    for i in range(_NUM_ZERNIKE):
        out[f"zernike_moments_{i + 1}"] = float(avg_zernike[i])

    return out


def extract_features(image_path: str, mask_path: str) -> Dict[str, float]:
    """Extract radiomics features from a NIfTI image+mask pair.

    Parameters
    ----------
    image_path : str
        Path to a T1/T2/T1C NIfTI file (``.nii`` or ``.nii.gz``).
    mask_path : str
        Path to the corresponding mask NIfTI file.

    Returns
    -------
    dict
        Flat dict with keys matching the model's 33 image-derived feature names
        (e.g. ``total_area_Mean``, ``hu_moments_1_Q1``, ``zernike_moments_10_Min``).
        Returns all zeros if no valid slices are found.
    """
    import cv2
    import nibabel as nib

    image_nifti = nib.load(image_path)
    mask_nifti = nib.load(mask_path)

    image_data = image_nifti.get_fdata()
    mask_data = mask_nifti.get_fdata()
    binary_mask = np.where(mask_data > 0, 1, 0)

    num_slices = image_data.shape[2]
    extracted_slices: List[np.ndarray] = []

    for idx in range(num_slices):
        masked = image_data[:, :, idx] * binary_mask[:, :, idx]
        if np.sum(masked) > 0:
            extracted_slices.append(masked)

    if not extracted_slices:
        return _empty_feature_dict()

    # Collect per-slice feature dicts.
    per_slice: List[Dict[str, float]] = []
    for extracted_slice in extracted_slices:
        try:
            clustered = _cluster_image(extracted_slice, n_clusters=4)
        except Exception:
            continue

        contours_image = np.zeros_like(extracted_slice, dtype=np.uint8)
        for cluster_label in range(1, 5):
            cluster_mask = np.where(clustered == cluster_label, 255, 0).astype(np.uint8)
            edges = cv2.Canny(cluster_mask, 50, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contours_image = cv2.drawContours(contours_image.copy(), contours, -1, 255, 1)

        contours_image = cv2.equalizeHist(contours_image)

        try:
            features = _slice_features(contours_image)
        except Exception:
            continue
        per_slice.append(features)

    if not per_slice:
        return _empty_feature_dict()

    # Aggregate per-slice values into per-feature arrays, then compute stats.
    out: Dict[str, float] = {}

    all_keys = list(per_slice[0].keys())
    for key in all_keys:
        values = np.array([s.get(key, 0.0) for s in per_slice], dtype=float)
        stats = _compute_stats(values)
        for stat_name, stat_val in stats.items():
            out[f"{key}_{stat_name}"] = stat_val

    # Guarantee every expected key is present (in case of edge cases).
    expected = _empty_feature_dict()
    for k, v in expected.items():
        if k not in out:
            out[k] = v

    return out
