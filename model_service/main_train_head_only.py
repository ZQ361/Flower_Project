"""
EfficientNet-B0 分类头训练消融实验脚本。

该脚本冻结特征提取层，只训练分类头，最大训练 100 epoch。
用于和完整两阶段微调方法进行对比。
"""

import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from model_service.config import config
from model_service.utils.dataset import get_dataloaders
from model_service.utils.model import (
    create_model,
    freeze_feature_extractor,
    get_trainable_params_count,
)
from model_service.utils.train import train_stage, validate


MODEL_NAME = "efficientnet_b0"
EXPERIMENT_NAME = "efficientnet_b0_head_only"
NUM_EPOCHS = config.num_epochs_stage1 + config.num_epochs_stage2


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def main():
    set_seed(42)
    os.makedirs(config.save_dir, exist_ok=True)

    print(f"使用设备: {config.device}")
    print(f"当前消融实验: {EXPERIMENT_NAME}")
    print(f"训练策略: 冻结特征提取层，只训练分类头，最大训练 {NUM_EPOCHS} epoch")

    print("\n加载数据...")
    train_loader, val_loader, test_loader = get_dataloaders()
    print(f"训练集: {len(train_loader.dataset)} 张")
    print(f"验证集: {len(val_loader.dataset)} 张")
    print(f"测试集: {len(test_loader.dataset)} 张")

    print("\n创建模型...")
    model = create_model(MODEL_NAME).to(config.device)
    freeze_feature_extractor(model, MODEL_NAME)

    trainable, total = get_trainable_params_count(model)
    print(f"总参数量: {total:,}")
    print(f"可训练参数量: {trainable:,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=config.lr_stage1)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        patience=5,
        factor=0.5,
    )

    save_path = os.path.join(
        config.save_dir,
        f"{EXPERIMENT_NAME}_stage2_best.pth",
    )
    print(f"模型保存路径: {save_path}")

    best_acc = train_stage(
        model,
        train_loader,
        val_loader,
        criterion,
        optimizer,
        scheduler,
        NUM_EPOCHS,
        config.device,
        save_path,
        "阶段2",
        EXPERIMENT_NAME,
    )
    print(f"最佳验证准确率: {best_acc:.2f}%")

    print("\n" + "=" * 60)
    print("测试集评估")
    print("=" * 60)

    model.load_state_dict(torch.load(save_path, map_location=config.device))
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
