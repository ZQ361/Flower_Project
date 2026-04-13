# download_dataset.py

from torchvision.datasets import Flowers102

# 数据集将下载到当前目录下的 './data' 文件夹中
# download=True 是自动下载的关键
print("开始下载/验证 Oxford 102 Flowers 数据集...")

# 下载训练集
train_set = Flowers102(
    root='./data',
    split='train',
    download=True
)

# 下载验证集
val_set = Flowers102(
    root='./data',
    split='val',
    download=True
)

# 下载测试集
test_set = Flowers102(
    root='./data',
    split='test',
    download=True
)

print("\n数据集准备完成！")
print(f"训练集图片数量: {len(train_set)}")
print(f"验证集图片数量: {len(val_set)}")
print(f"测试集图片数量: {len(test_set)}")