"""
EfficientNet-B0 错误分析脚本

输出：
1. 归一化混淆矩阵图
2. Top 10 易混淆类别图
3. Top 10 易混淆类别 CSV
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import confusion_matrix
from torch.utils.data import DataLoader
from torchvision import datasets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from model_service.config import config
    from model_service.utils.dataset import get_transforms
    from model_service.utils.model import create_model
except ImportError:  # 支持从 model_service 目录或项目根目录直接运行
    from config import config
    from utils.dataset import get_transforms
    from utils.model import create_model


MODEL_NAME = "efficientnet_b0"
TOP_N = 10

FIGURE_DIR = os.path.join(BASE_DIR, "log", "figures")
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(FIGURE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def collect_predictions():
    """在测试集上收集真实标签和预测标签。"""
    _, test_transform = get_transforms()
    test_dataset = datasets.Flowers102(
        root=config.data_dir,
        split="test",
        transform=test_transform,
        download=False,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )

    model = create_model(MODEL_NAME).to(config.device)
    checkpoint_path = os.path.join(config.save_dir, f"{MODEL_NAME}_stage2_best.pth")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"未找到模型权重: {checkpoint_path}")

    state_dict = torch.load(checkpoint_path, map_location=config.device)
    model.load_state_dict(state_dict)
    model.eval()

    all_labels = []
    all_preds = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(config.device)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu()

            all_labels.extend(labels.tolist())
            all_preds.extend(preds.tolist())

    return np.array(all_labels), np.array(all_preds)


def plot_normalized_confusion_matrix(cm_normalized, save_path):
    """绘制归一化混淆矩阵。"""
    class_ids = [str(i + 1) for i in range(config.num_classes)]

    plt.figure(figsize=(18, 16))
    sns.heatmap(
        cm_normalized,
        cmap="Blues",
        vmin=0,
        vmax=1,
        xticklabels=class_ids,
        yticklabels=class_ids,
        square=True,
        cbar_kws={"label": "Normalized Ratio"},
    )
    plt.title("Normalized Confusion Matrix of EfficientNet-B0")
    plt.xlabel("Predicted Class ID")
    plt.ylabel("True Class ID")
    plt.xticks(fontsize=5, rotation=90)
    plt.yticks(fontsize=5, rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def get_top_confused_pairs(cm, top_n=TOP_N):
    """从混淆矩阵中提取非对角线的 Top-N 易混淆类别对。"""
    pairs = []
    class_totals = cm.sum(axis=1)

    for true_idx in range(cm.shape[0]):
        for pred_idx in range(cm.shape[1]):
            if true_idx == pred_idx:
                continue

            count = int(cm[true_idx, pred_idx])
            if count == 0:
                continue

            total = int(class_totals[true_idx])
            error_ratio = count / total if total else 0
            pairs.append(
                {
                    "true_class_id": true_idx + 1,
                    "true_class_name": config.flower_classes[true_idx],
                    "predicted_class_id": pred_idx + 1,
                    "predicted_class_name": config.flower_classes[pred_idx],
                    "count": count,
                    "true_class_total": total,
                    "error_ratio": error_ratio,
                }
            )

    pairs.sort(key=lambda item: (item["count"], item["error_ratio"]), reverse=True)
    return pairs[:top_n]


def save_top_confused_pairs_csv(pairs, save_path):
    """保存 Top-N 易混淆类别对为 CSV。"""
    fieldnames = [
        "true_class_id",
        "true_class_name",
        "predicted_class_id",
        "predicted_class_name",
        "count",
        "true_class_total",
        "error_ratio_percent",
    ]

    with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pair in pairs:
            writer.writerow(
                {
                    "true_class_id": pair["true_class_id"],
                    "true_class_name": pair["true_class_name"],
                    "predicted_class_id": pair["predicted_class_id"],
                    "predicted_class_name": pair["predicted_class_name"],
                    "count": pair["count"],
                    "true_class_total": pair["true_class_total"],
                    "error_ratio_percent": round(pair["error_ratio"] * 100, 2),
                }
            )


def plot_top_confused_pairs(pairs, save_path):
    """绘制 Top-N 易混淆类别对柱状图。"""
    labels = [
        f"{p['true_class_id']} {p['true_class_name']}\n-> "
        f"{p['predicted_class_id']} {p['predicted_class_name']}"
        for p in pairs
    ]
    counts = [p["count"] for p in pairs]

    plt.figure(figsize=(10, 7))
    y_positions = np.arange(len(pairs))
    plt.barh(y_positions, counts, color="#4C78A8")
    plt.yticks(y_positions, labels, fontsize=8)
    plt.gca().invert_yaxis()
    plt.xlabel("Misclassification Count")
    plt.title("Top 10 Confused Class Pairs of EfficientNet-B0")

    for y, count in zip(y_positions, counts):
        plt.text(count + 0.1, y, str(count), va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def main():
    print("开始分析 EfficientNet-B0 测试集混淆情况...")
    y_true, y_pred = collect_predictions()

    labels = list(range(config.num_classes))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_normalized = confusion_matrix(y_true, y_pred, labels=labels, normalize="true")
    accuracy = 100.0 * np.trace(cm) / np.sum(cm)

    confusion_matrix_path = os.path.join(
        FIGURE_DIR,
        "efficientnet_b0_confusion_matrix_normalized.png",
    )
    top_pairs_figure_path = os.path.join(
        FIGURE_DIR,
        "efficientnet_b0_top10_confused_pairs.png",
    )
    top_pairs_csv_path = os.path.join(
        LOG_DIR,
        "efficientnet_b0_top10_confused_pairs.csv",
    )

    plot_normalized_confusion_matrix(cm_normalized, confusion_matrix_path)
    top_pairs = get_top_confused_pairs(cm, top_n=TOP_N)
    save_top_confused_pairs_csv(top_pairs, top_pairs_csv_path)
    plot_top_confused_pairs(top_pairs, top_pairs_figure_path)

    print(f"测试集 Top-1 准确率: {accuracy:.2f}%")
    print(f"[已保存] {confusion_matrix_path}")
    print(f"[已保存] {top_pairs_figure_path}")
    print(f"[已保存] {top_pairs_csv_path}")


if __name__ == "__main__":
    main()
