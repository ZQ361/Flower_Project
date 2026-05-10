"""
训练函数
"""

import torch
import os
from tqdm import tqdm


def train_one_epoch(model, train_loader, criterion, optimizer, device):
    """训练一个 epoch"""
    model.train()# 切换到训练模式
    running_loss = 0.0 # 记录每个 epoch的损失总和
    correct = 0 # 记录正确分类的样本数量
    total = 0 # 总样本数量

    for images, labels in tqdm(train_loader, desc='训练', leave=False):
        images, labels = images.to(device), labels.to(device)# 将图像和标签移动到设备，准备进行计算（如GPU）

        optimizer.zero_grad()# 清空梯度
        outputs = model(images)# 前向传播
        loss = criterion(outputs, labels)# 计算损失
        loss.backward()# 反向传播
        optimizer.step()# 更新参数

        running_loss += loss.item()# 累加损失
        _, predicted = outputs.max(1)# 获取预测类别
        total += labels.size(0)# 累加总样本数量
        correct += predicted.eq(labels).sum().item()# 累加正确分类的样本数量

    epoch_loss = running_loss / len(train_loader) # 计算每个 epoch的损失
    epoch_acc = 100. * correct / total # 计算每个 epoch的准确率

    return epoch_loss, epoch_acc # 返回每个epoch的损失和准确率



def validate(model, val_loader, criterion, device):
    """验证"""
    model.eval()# 切换到评估模式
    running_loss = 0.0 # 记录每个 epoch的损失总和
    correct = 0 # 记录正确分类的样本数量
    total = 0 # 总样本数量

    with torch.no_grad():# 不计算梯度
        for images, labels in tqdm(val_loader, desc='验证', leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)# outputs 是模型输出的 logits（未归一化的预测分数），类型是 torch.Tensor，形状为 [batch_size, num_classes]  
            # outputs是batch_size（32）个样本的预测分数，每个样本有num_classes个类别，每个类别有1个类别数，为浮点数，表示该类别对应的预测概率，这些概率的和为1
            #outputs 是模型输出的 logits，使用 argmax 取得预测类别；如需置信度，可再经过 softmax 转为概率分布。
            # 例如，outputs = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
            # 表示2个样本，每个样本有3个类别，每个类别有3个预测分数，这些分数的和为1
            # 例如，outputs[0, 0] = 0.1，表示样本0的类别0的预测分数为0.1
            loss = criterion(outputs, labels)# 计算损失，类型为 torch.Tensor
            
            running_loss += loss.item()# 累加损失，.item() 方法将张量转换为标量，类型是 float
            _, predicted = outputs.max(1)# 获取预测类别，返回最大值的索引和最大值
            # 在 batch_size 个样本中，从每个样本得出来一个最大值及其下标索引，predicted 就是 batch_size 个最大值的下标索引
            # 对第1个维度（类别维度）取最大值，返回两个值：最大值和对应的索引，_ 接收最大值（我们不需要）， predicted 接收类别索引（范围 0-101）
            # [batch_size, num_classes]（从不同维度就像是在一个表格，从每个水平方向取出最大值或从每个垂直方向取最大值）
            #    维度0 ↑     维度1 ↑
            total += labels.size(0)# 累加总样本数量，.size(0) 方法返回第0个维度的大小，labels本就是一维张量，所以返回的是样本数量，即 batch_size（最后一个的话就直接返回样本数）
            correct += predicted.eq(labels).sum().item()# 累加正确分类的样本数量

    epoch_loss = running_loss / len(val_loader) # 整个epoch的损失除以批次数量得到平均损失
    epoch_acc = 100. * correct / total # 计算每个 epoch的准确率，100.是将准确率转换为百分比

    return epoch_loss, epoch_acc


# def train_stage(model, train_loader, val_loader, criterion, optimizer,
#                 scheduler, num_epochs, device, save_path, stage_name):
#     """通用训练阶段函数"""
#     best_acc = 0.0
#
#     # 记录数据以供画图
#     history = {
#         "train_loss": [],
#         "train_acc": [],
#         "val_loss": [],
#         "val_acc": []
#     }
#
#     for epoch in range(num_epochs):
#         # 训练
#         train_loss, train_acc = train_one_epoch(
#             model, train_loader, criterion, optimizer, device
#         )
#
#         # 验证
#         val_loss, val_acc = validate(model, val_loader, criterion, device)
#
#         # 记录历史数据
#         history["train_loss"].append(train_loss)
#         history["train_acc"].append(train_acc)
#         history["val_loss"].append(val_loss)
#         history["val_acc"].append(val_acc)
#
#         # 更新学习率
#         if scheduler:
#             scheduler.step(val_acc)
#
#         print(f"[{stage_name}] Epoch {epoch + 1}/{num_epochs} | "# +1 是因为 epoch 从0开始，所以要加1显示当前 epoch
#               f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
#               f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
#
#         # 保存最佳模型
#         if val_acc > best_acc:
#             best_acc = val_acc# 更新最佳准确率
#             torch.save(model.state_dict(), save_path)# 保存最佳模型
#             print(f"  -> 保存最佳模型 (准确率: {val_acc:.2f}%)")# 打印最佳模型的准确率
#
#     torch.save(history, save_path.replace(".pth", "_history.pth"))
#     return best_acc
def train_stage(model, train_loader, val_loader, criterion, optimizer,
                scheduler, num_epochs, device, save_path, stage_name, model_name=None):
    """通用训练阶段函数"""
    best_acc = 0.0
    best_epoch = 0

    history = {
        "model_name": model_name,
        "stage_name": stage_name,
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": []
    }

    for epoch in range(num_epochs):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )

        val_loss, val_acc = validate(model, val_loader, criterion, device)

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if scheduler:
            scheduler.step(val_acc)

        print(f"[{stage_name}] Epoch {epoch + 1}/{num_epochs} | "
              f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch + 1
            torch.save(model.state_dict(), save_path)
            print(f"  -> 保存最佳模型 (准确率: {val_acc:.2f}%)")

    history["best_acc"] = best_acc
    history["best_epoch"] = best_epoch
    torch.save(history, save_path.replace(".pth", "_history.pth"))

    return best_acc