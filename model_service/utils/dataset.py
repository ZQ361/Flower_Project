"""
数据集加载
"""


from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from model_service.config import config


def get_transforms():
    """获取数据预处理"""
    # 训练时数据增强
    train_transform = transforms.Compose([
        transforms.Resize(config.image_size),# 调整大小，缩放
        transforms.RandomResizedCrop(config.image_size, scale=(0.8, 1.0)),# 随机随机裁剪
        transforms.RandomHorizontalFlip(p=0.5),# 随机水平翻转
        transforms.RandomRotation(config.random_rotation),# 随机旋转
        transforms.ColorJitter(# 颜色抖动
            brightness=config.brightness,# 亮度抖动
            contrast=config.contrast,# 对比度抖动
            saturation=config.saturation,# 饱和度抖动
        ),
        transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.3),# 高斯模糊
        transforms.ToTensor(),# 转换为张量
        transforms.Normalize(mean=config.mean, std=config.std)# 标准化
    ])

    # 验证/测试时（无增强）
    val_transform = transforms.Compose([
        transforms.Resize(config.image_size),# 缩放
        transforms.CenterCrop(config.image_size),# 居中裁剪
        transforms.ToTensor(),# 转换为张量
        transforms.Normalize(mean=config.mean, std=config.std)# 标准化
    ])

    return train_transform, val_transform


def get_dataloaders(batch_size=None):
    """获取 DataLoader"""
    if batch_size is None:
        batch_size = config.batch_size

    train_transform, val_transform = get_transforms()

    # 加载数据集
    train_dataset = datasets.Flowers102(
        root=config.data_dir,
        split='train',
        transform=train_transform,
        download=True
    )

    val_dataset = datasets.Flowers102(
        root=config.data_dir,
        split='val',
        transform=val_transform,
        download=True
    )

    test_dataset = datasets.Flowers102(
        root=config.data_dir,
        split='test',
        transform=val_transform,
        download=True
    )

    # 创建 DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,# 随机打乱
        num_workers=2,# 并行加载数据的线程数
        pin_memory = True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory = True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    return train_loader, val_loader, test_loader

