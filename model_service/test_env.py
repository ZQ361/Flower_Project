# test_env.py
import torch
from config import config
from utils.dataset import get_dataloaders
from utils.model import create_model


def quick_test():
    print("=" * 50)
    print("快速环境验证（不会影响训练）")
    print("=" * 50)

    # 1. 测试数据加载
    print("\n1. 测试数据加载...")
    train_loader, val_loader, test_loader = get_dataloaders()
    print(f"   ✅ 训练集 batches: {len(train_loader)}")
    print(f"   ✅ 验证集 batches: {len(val_loader)}")

    # 2. 测试模型创建
    print("\n2. 测试模型创建...")
    model = create_model().to(config.device)
    print(f"   ✅ 模型已创建，设备: {config.device}")

    # 3. 测试前向传播
    print("\n3. 测试前向传播...")
    images, labels = next(iter(train_loader))
    print(f"   输入形状: {images.shape}")

    images = images.to(config.device)

    with torch.no_grad():
        outputs = model(images)

    print(f"   输出形状: {outputs.shape}")
    print(f"   ✅ 前向传播成功！")

    # 4. 测试显存（修复后的版本）
    # 判断是否为 GPU（兼容字符串和 torch.device 两种写法）
    is_cuda = (config.device == 'cuda') or (hasattr(config.device, 'type') and config.device.type == 'cuda')

    if is_cuda:
        print(f"\n4. GPU 信息:")
        print(f"   GPU 名称: {torch.cuda.get_device_name(0)}")
        print(f"   显存占用: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        print(f"   显存缓存: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！可以开始训练！")
    print("=" * 50)


if __name__ == '__main__':
    quick_test()