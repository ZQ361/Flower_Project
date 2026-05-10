"""
主训练脚本
"""

import torch
import torch.nn as nn
import torch.optim as optim
import os
from config import config
from utils.dataset import get_dataloaders
from utils.model import create_model, freeze_feature_extractor, unfreeze_all_layers,get_trainable_params_count
from utils.train import train_stage,validate
import random
import numpy as np
import torch


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def main():
    set_seed(42)# 设置随机种子
    # 创建保存目录
    os.makedirs(config.save_dir, exist_ok=True)

    print(f"使用设备: {config.device}")

    # 1. 加载数据
    print("\n加载数据...")
    train_loader, val_loader, test_loader = get_dataloaders()
    print(f"训练集: {len(train_loader.dataset)} 张")
    print(f"验证集: {len(val_loader.dataset)} 张")
    print(f"测试集: {len(test_loader.dataset)} 张")

    # 2. 创建模型
    print("\n创建模型...")
    model = create_model(config.model_name)
    model = model.to(config.device)

    # 打印参数信息
    trainable, total = get_trainable_params_count(model)
    print(f"总参数量: {total:,}")
    print(f"可训练参数量: {trainable:,}")

    # 3. 损失函数
    criterion = nn.CrossEntropyLoss()

    # 打印当前训练模型
    print(f"当前训练模型: {config.model_name}")

    # ========== 阶段1：只训练分类头 ==========
    print("\n" + "=" * 60)
    print("阶段1：只训练分类头（冻结特征提取层）")
    print("=" * 60)

    freeze_feature_extractor(model, config.model_name)# 冻结特征提取层
    if config.model_name == "resnet18":
        optimizer = optim.Adam(model.fc.parameters(), lr=config.lr_stage1)
    else:
        optimizer = optim.Adam(model.classifier.parameters(), lr=config.lr_stage1)
    scheduler = None # 不使用学习率调度器

    stage1_save_path = os.path.join(
        config.save_dir,
        f"{config.model_name}_stage1_best.pth"
    )# 阶段1最佳模型保存路径
    print(f"阶段1模型保存路径: {stage1_save_path}")

    best_acc_stage1 = train_stage(
        model, train_loader, val_loader, criterion, optimizer,
        scheduler, config.num_epochs_stage1, config.device,
        stage1_save_path, "阶段1",config.model_name
    )
    print(f"阶段1最佳验证准确率: {best_acc_stage1:.2f}%")

    # ========== 阶段2：全微调 ==========
    print("\n" + "=" * 60)
    print("阶段2：全微调（解冻所有层）")
    print("=" * 60)

    # 加载阶段1的最佳模型
    model.load_state_dict(torch.load(stage1_save_path,map_location=config.device))
    unfreeze_all_layers(model)

    optimizer = optim.Adam(model.parameters(), lr=config.lr_stage2)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=5, factor=0.5 # 学习率调度器：验证准确率Plateau
    )

    stage2_save_path = os.path.join(
        config.save_dir,
        f"{config.model_name}_stage2_best.pth"
    )
    print(f"阶段2模型保存路径: {stage2_save_path}")

    best_acc_stage2 = train_stage(
        model, train_loader, val_loader, criterion, optimizer,
        scheduler, config.num_epochs_stage2, config.device,
        stage2_save_path, "阶段2",config.model_name
    )
    print(f"阶段2最佳验证准确率: {best_acc_stage2:.2f}%")

    # ========== 测试 ==========
    print("\n" + "=" * 60)
    print("测试集评估")
    print("=" * 60)
   
    model.load_state_dict(torch.load(stage2_save_path,map_location=config.device))
    test_loss, test_acc = validate(model, test_loader, criterion, config.device)
    print(f"测试集准确率: {test_acc:.2f}%")

    # 保存最终模型
    final_path = os.path.join(
        config.save_dir,
        f"{config.model_name}_flowers102_final.pth"
    )
    torch.save(model.state_dict(), final_path)
    print(f"\n最终模型已保存至: {final_path}")


if __name__ == '__main__':
    main()