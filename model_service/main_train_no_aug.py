"""
EfficientNet-B0 数据增强消融实验训练脚本。

该脚本不修改现有训练主流程，单独训练 without data augmentation 版本。
"""

import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from model_service.config import config
from model_service.utils.model import (
    create_model,
    freeze_feature_extractor,
    get_trainable_params_count,
    unfreeze_all_layers,
)
from model_service.utils.train import train_stage, validate


MODEL_NAME = "efficientnet_b0"
EXPERIMENT_NAME = "efficientnet_b0_no_aug"


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_no_aug_transforms():
    """训练、验证、测试均使用无随机增强的基础预处理。"""
    base_transform = transforms.Compose([
        transforms.Resize(config.image_size),
        transforms.CenterCrop(config.image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=config.mean, std=config.std),
    ])
    return base_transform, base_transform


def get_no_aug_dataloaders(batch_size=None):
    """获取 no-augmentation 实验使用的 DataLoader。"""
    if batch_size is None:
        batch_size = config.batch_size

    train_transform, val_transform = get_no_aug_transforms()

    train_dataset = datasets.Flowers102(
        root=config.data_dir,
        split="train",
        transform=train_transform,
        download=True,
    )
    val_dataset = datasets.Flowers102(
        root=config.data_dir,
        split="val",
        transform=val_transform,
        download=True,
    )
    test_dataset = datasets.Flowers102(
        root=config.data_dir,
        split="test",
        transform=val_transform,
        download=True,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )

    return train_loader, val_loader, test_loader


def main():
    set_seed(42)
    os.makedirs(config.save_dir, exist_ok=True)

    print(f"使用设备: {config.device}")
    print(f"当前消融实验: {EXPERIMENT_NAME}")
    print("训练集预处理: Resize + CenterCrop + ToTensor + Normalize（无随机增强）")

    print("\n加载数据...")
    train_loader, val_loader, test_loader = get_no_aug_dataloaders()
    print(f"训练集: {len(train_loader.dataset)} 张")
    print(f"验证集: {len(val_loader.dataset)} 张")
    print(f"测试集: {len(test_loader.dataset)} 张")

    print("\n创建模型...")
    model = create_model(MODEL_NAME).to(config.device)
    trainable, total = get_trainable_params_count(model)
    print(f"总参数量: {total:,}")
    print(f"可训练参数量: {trainable:,}")

    criterion = nn.CrossEntropyLoss()

    print("\n" + "=" * 60)
    print("阶段1：只训练分类头（冻结特征提取层）")
    print("=" * 60)

    freeze_feature_extractor(model, MODEL_NAME)
    optimizer = optim.Adam(model.classifier.parameters(), lr=config.lr_stage1)
    scheduler = None

    stage1_save_path = os.path.join(
        config.save_dir,
        f"{EXPERIMENT_NAME}_stage1_best.pth",
    )
    print(f"阶段1模型保存路径: {stage1_save_path}")

    best_acc_stage1 = train_stage(
        model,
        train_loader,
        val_loader,
        criterion,
        optimizer,
        scheduler,
        config.num_epochs_stage1,
        config.device,
        stage1_save_path,
        "阶段1",
        EXPERIMENT_NAME,
    )
    print(f"阶段1最佳验证准确率: {best_acc_stage1:.2f}%")

    print("\n" + "=" * 60)
    print("阶段2：全微调（解冻所有层）")
    print("=" * 60)

    model.load_state_dict(torch.load(stage1_save_path, map_location=config.device))
    unfreeze_all_layers(model)

    optimizer = optim.Adam(model.parameters(), lr=config.lr_stage2)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        patience=5,
        factor=0.5,
    )

    stage2_save_path = os.path.join(
        config.save_dir,
        f"{EXPERIMENT_NAME}_stage2_best.pth",
    )
    print(f"阶段2模型保存路径: {stage2_save_path}")

    best_acc_stage2 = train_stage(
        model,
        train_loader,
        val_loader,
        criterion,
        optimizer,
        scheduler,
        config.num_epochs_stage2,
        config.device,
        stage2_save_path,
        "阶段2",
        EXPERIMENT_NAME,
    )
    print(f"阶段2最佳验证准确率: {best_acc_stage2:.2f}%")

    print("\n" + "=" * 60)
    print("测试集评估")
    print("=" * 60)

    model.load_state_dict(torch.load(stage2_save_path, map_location=config.device))
    test_loss, test_acc = validate(model, test_loader, criterion, config.device)
    print(f"测试集准确率: {test_acc:.2f}%")

    final_path = os.path.join(
        config.save_dir,
        f"{EXPERIMENT_NAME}_flowers102_final.pth",
    )
    torch.save(model.state_dict(), final_path)
    print(f"\n最终模型已保存至: {final_path}")


if __name__ == "__main__":
    main()
