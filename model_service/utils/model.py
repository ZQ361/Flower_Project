"""
模型定义
"""

import torch
import torch.nn as nn
from torchvision import models
from model_service.config import config


# def create_model(num_classes=None):
#     """创建 MobileNetV2 模型"""
#     if num_classes is None:
#         num_classes = config.num_classes
#
#     # 加载预训练模型
#     model = models.mobilenet_v2(weights='DEFAULT')
#
#     # 修改分类头
#     model.classifier = nn.Sequential(
#         nn.Dropout(p=0.2),
#         nn.Linear(model.last_channel, num_classes)
#     )
#
#     return model

def create_model(model_name, num_classes=None):
    if num_classes is None:
        num_classes = config.num_classes

    if model_name == "mobilenet_v2":
        model = models.mobilenet_v2(weights="DEFAULT")
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(model.last_channel, num_classes)
        )

    elif model_name == "resnet18":
        model = models.resnet18(weights="DEFAULT")
        model.fc = nn.Linear(model.fc.in_features, num_classes)

    elif model_name == "efficientnet_b0":
        model = models.efficientnet_b0(weights="DEFAULT")
        # model.classifier[1] = nn.Linear(
        #     model.classifier[1].in_features,
        #     num_classes
        # )
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    else:
        raise ValueError("Unsupported model")

    return model


# def freeze_feature_extractor(model):
#     """冻结特征提取层"""
#     for param in model.features.parameters():
#         param.requires_grad = False

def freeze_feature_extractor(model, model_name):
    for param in model.parameters():
        param.requires_grad = False

    if model_name == "mobilenet_v2":
        for param in model.classifier.parameters():
            param.requires_grad = True

    elif model_name == "resnet18":
        for param in model.fc.parameters():
            param.requires_grad = True

    elif model_name == "efficientnet_b0":
        for param in model.classifier.parameters():
            param.requires_grad = True

def unfreeze_all_layers(model):# 解冻所有层，包括特征提取层和分类头
    """解冻所有层"""
    for param in model.parameters():
        param.requires_grad = True # 解冻所有层


def get_trainable_params_count(model):
    """获取可训练参数数量"""
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad) # 可训练参数数量
    total = sum(p.numel() for p in model.parameters()) # 总参数数量
    return trainable, total # 返回可训练参数数量和总参数数量