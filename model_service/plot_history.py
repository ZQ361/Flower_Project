# plot_history.py
# -*- coding: utf-8 -*-

"""
训练历史记录可视化脚本

功能：
1. 读取各模型训练过程中保存的 history.pth 文件
2. 绘制 train/val 的 loss 曲线
3. 绘制 train/val 的 accuracy 曲线
4. 绘制三种模型在 Stage2 的验证集精度对比图
5. 自动将图片保存到 log/figures/ 目录

使用前提：
- 你的 history 文件里应包含以下字段：
    train_loss
    val_loss
    train_acc
    val_acc
- 文件是用 torch.save(history, path) 保存的
"""

import os
import torch
import matplotlib.pyplot as plt


# =========================
# 1. 基础配置
# =========================

# 当前脚本所在目录（即 model_service）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 图片保存目录
SAVE_DIR = os.path.join(BASE_DIR, "log", "figures")
os.makedirs(SAVE_DIR, exist_ok=True)

# 历史记录文件路径
# 你后续如果文件名有变化，只需要改这里
HISTORY_PATHS = {
    "mobilenet_v2_stage1": os.path.join(BASE_DIR, "checkpoints", "mobilenet_v2_stage1_best_history.pth"),
    "mobilenet_v2_stage2": os.path.join(BASE_DIR, "checkpoints", "mobilenet_v2_stage2_best_history.pth"),
    "resnet18_stage1": os.path.join(BASE_DIR, "checkpoints", "resnet18_stage1_best_history.pth"),
    "resnet18_stage2": os.path.join(BASE_DIR, "checkpoints", "resnet18_stage2_best_history.pth"),
    "efficientnet_b0_stage1": os.path.join(BASE_DIR, "checkpoints", "efficientnet_b0_stage1_best_history.pth"),
    "efficientnet_b0_stage2": os.path.join(BASE_DIR, "checkpoints", "efficientnet_b0_stage2_best_history.pth"),
}


# =========================
# 2. 工具函数：加载 history
# =========================
def load_history(path):
    """
    加载单个 history 文件

    参数:
        path (str): history 文件路径

    返回:
        dict: 训练历史字典
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到文件: {path}")

    history = torch.load(path, map_location="cpu")
    return history


# =========================
# 3. 工具函数：画单个 history 的 loss 曲线
# =========================
def plot_loss_curve(history, title, save_path):
    """
    绘制并保存 loss 曲线

    参数:
        history (dict): 历史记录
        title (str): 图标题
        save_path (str): 保存路径
    """
    train_loss = history["train_loss"]
    val_loss = history["val_loss"]
    epochs = range(1, len(train_loss) + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_loss, marker='o', label="Train Loss")
    plt.plot(epochs, val_loss, marker='s', label="Val Loss")

    plt.title(title)
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


# =========================
# 4. 工具函数：画单个 history 的 accuracy 曲线
# =========================
def plot_acc_curve(history, title, save_path):
    """
    绘制并保存 accuracy 曲线

    参数:
        history (dict): 历史记录
        title (str): 图标题
        save_path (str): 保存路径
    """
    train_acc = history["train_acc"]
    val_acc = history["val_acc"]
    epochs = range(1, len(train_acc) + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(epochs, train_acc, marker='o', label="Train Accuracy")
    plt.plot(epochs, val_acc, marker='s', label="Val Accuracy")

    plt.title(title)
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


# =========================
# 5. 画一个模型某阶段的两张图
# =========================
def plot_single_history(name, path):
    """
    为单个 history 文件绘制两张图：
    1. Loss 曲线
    2. Accuracy 曲线

    参数:
        name (str): 名称，用于图名和文件名
        path (str): history 文件路径
    """
    history = load_history(path)

    # 生成更友好的标题
    pretty_name = name.replace("_", " ").title()

    loss_save_path = os.path.join(SAVE_DIR, f"{name}_loss.png")
    acc_save_path = os.path.join(SAVE_DIR, f"{name}_acc.png")

    plot_loss_curve(
        history=history,
        title=f"{pretty_name} Loss Curve",
        save_path=loss_save_path
    )

    plot_acc_curve(
        history=history,
        title=f"{pretty_name} Accuracy Curve",
        save_path=acc_save_path
    )

    print(f"[已保存] {loss_save_path}")
    print(f"[已保存] {acc_save_path}")


# =========================
# 6. 三模型 Stage2 验证精度对比图
# =========================
def plot_stage2_val_acc_comparison():
    """
    绘制三种模型在 Stage2 的验证集精度对比图
    非常适合放论文中进行模型比较
    """
    model_files = {
        "MobileNetV2": HISTORY_PATHS["mobilenet_v2_stage2"],
        "ResNet18": HISTORY_PATHS["resnet18_stage2"],
        "EfficientNet-B0": HISTORY_PATHS["efficientnet_b0_stage2"],
    }

    plt.figure(figsize=(8, 5))

    for model_name, file_path in model_files.items():
        history = load_history(file_path)
        val_acc = history["val_acc"]
        epochs = range(1, len(val_acc) + 1)

        plt.plot(epochs, val_acc, marker='o', label=model_name)

        # 标出最佳点
        best_acc = max(val_acc)
        best_epoch = val_acc.index(best_acc) + 1
        plt.scatter(best_epoch, best_acc)
        plt.text(best_epoch, best_acc, f"{best_acc:.2f}", fontsize=9)

    plt.title("Validation Accuracy Comparison of Three Models (Stage 2)")
    plt.xlabel("Epoch")
    plt.ylabel("Validation Accuracy (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    save_path = os.path.join(SAVE_DIR, "stage2_val_acc_comparison.png")
    plt.savefig(save_path, dpi=300)
    plt.close()

    print(f"[已保存] {save_path}")


# =========================
# 7. 主函数
# =========================
def main():
    """
    主函数：
    1. 逐个画出所有 history 的 loss / acc 曲线
    2. 画 Stage2 三模型对比图
    """
    print("开始绘制训练曲线...")

    for name, path in HISTORY_PATHS.items():
        try:
            plot_single_history(name, path)
        except Exception as e:
            print(f"[跳过] {name} 画图失败：{e}")

    # 画三模型 Stage2 验证精度对比图
    try:
        plot_stage2_val_acc_comparison()
    except Exception as e:
        print(f"[失败] Stage2 对比图绘制失败：{e}")

    print("全部绘图完成！")


if __name__ == "__main__":
    main()