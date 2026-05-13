"""
EfficientNet-B0 数据增强消融实验结果绘图脚本。

训练 no-augmentation 模型后运行本脚本，生成消融实验测试准确率柱状图和 CSV 汇总。
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from model_service.config import config
from model_service.utils.dataset import get_transforms
from model_service.utils.model import create_model
from model_service.utils.train import validate


MODEL_NAME = "efficientnet_b0"
FULL_EXPERIMENT = "efficientnet_b0"
NO_AUG_EXPERIMENT = "efficientnet_b0_no_aug"
HEAD_ONLY_EXPERIMENT = "efficientnet_b0_head_only"

FIGURE_DIR = os.path.join(BASE_DIR, "log", "figures")
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(FIGURE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def load_history(experiment_name, stage):
    history_path = os.path.join(
        config.save_dir,
        f"{experiment_name}_{stage}_best_history.pth",
    )
    if not os.path.exists(history_path):
        raise FileNotFoundError(f"未找到 history 文件: {history_path}")
    return torch.load(history_path, map_location="cpu")


def get_test_loader():
    _, test_transform = get_transforms()
    test_dataset = datasets.Flowers102(
        root=config.data_dir,
        split="test",
        transform=test_transform,
        download=False,
    )
    return DataLoader(
        test_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )


def evaluate_checkpoint(experiment_name, stage, test_loader):
    checkpoint_path = os.path.join(
        config.save_dir,
        f"{experiment_name}_{stage}_best.pth",
    )
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"未找到 checkpoint 文件: {checkpoint_path}")

    model = create_model(MODEL_NAME).to(config.device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=config.device))
    criterion = nn.CrossEntropyLoss()
    test_loss, test_acc = validate(model, test_loader, criterion, config.device)
    return test_loss, test_acc


def collect_ablation_results():
    test_loader = get_test_loader()
    experiments = [
        ("Full Method", FULL_EXPERIMENT, "stage2"),
        ("Without Data Augmentation", NO_AUG_EXPERIMENT, "stage2"),
        ("Classifier Head Only", HEAD_ONLY_EXPERIMENT, "stage2"),
    ]

    results = []
    for label, experiment_name, stage in experiments:
        history = load_history(experiment_name, stage)
        _, test_acc = evaluate_checkpoint(experiment_name, stage, test_loader)
        val_acc = history["best_acc"]
        stop_epoch = history.get("stop_epoch", len(history["val_acc"]))

        results.append(
            {
                "method": label,
                "validation_accuracy": val_acc,
                "test_accuracy": test_acc,
                "stop_epoch": stop_epoch,
                "checkpoint_stage": stage,
            }
        )

    return results


def save_results_csv(results, save_path):
    with open(save_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "validation_accuracy",
                "test_accuracy",
                "stop_epoch",
                "checkpoint_stage",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "method": row["method"],
                    "validation_accuracy": round(row["validation_accuracy"], 2),
                    "test_accuracy": round(row["test_accuracy"], 2),
                    "stop_epoch": row["stop_epoch"],
                    "checkpoint_stage": row["checkpoint_stage"],
                }
            )


def plot_test_accuracy_bar(results, save_path):
    labels = [row["method"] for row in results]
    values = [row["test_accuracy"] for row in results]

    plt.figure(figsize=(7, 5))
    bars = plt.bar(labels, values, color=["#4C78A8", "#F58518", "#54A24B"])
    plt.ylabel("Test Accuracy (%)")
    plt.title("EfficientNet-B0 Ablation Study")
    plt.xticks(rotation=15, ha="right")
    plt.ylim(max(0, min(values) - 5), min(100, max(values) + 3))

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def main():
    print("开始生成 EfficientNet-B0 消融实验结果...")
    results = collect_ablation_results()

    csv_path = os.path.join(LOG_DIR, "efficientnet_b0_ablation_results.csv")
    figure_path = os.path.join(FIGURE_DIR, "efficientnet_b0_ablation_test_acc.png")

    save_results_csv(results, csv_path)
    plot_test_accuracy_bar(results, figure_path)

    for row in results:
        print(
            f"{row['method']}: "
            f"Val Acc={row['validation_accuracy']:.2f}%, "
            f"Test Acc={row['test_accuracy']:.2f}%, "
            f"Stop Epoch={row['stop_epoch']}, "
            f"Checkpoint={row['checkpoint_stage']}"
        )
    print(f"[已保存] {csv_path}")
    print(f"[已保存] {figure_path}")


if __name__ == "__main__":
    main()
