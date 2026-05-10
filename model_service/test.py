"""
测试脚本
"""

import torch
import torch.nn as nn
from config import config
from utils.dataset import get_dataloaders
from utils.model import create_model
from utils.train import validate
import os


def main():
    # 加载数据
    _, _, test_loader = get_dataloaders(batch_size=32)

    # 创建模型
    model = create_model()
    model = model.to(config.device)

    # 加载权重
    model_path = os.path.join(config.save_dir, 'mobilenetv2_flowers102_final.pth')
    model.load_state_dict(torch.load(model_path, map_location=config.device))

    # 测试
    criterion = nn.CrossEntropyLoss()
    test_loss, test_acc = validate(model, test_loader, criterion, config.device)

    print(f"测试集准确率: {test_acc:.2f}%")


if __name__ == '__main__':
    main()