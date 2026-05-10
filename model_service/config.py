"""
配置文件
"""

import torch
import os

# 获取当前配置文件所在目录
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # 路径配置
    # data_dir = './data'
    # save_dir = './checkpoints'
    data_dir = os.path.join(_BASE_DIR, 'data')
    save_dir = os.path.join(_BASE_DIR, 'checkpoints')

    # 模型选择
    model_name = "efficientnet_b0"
    # 可选：
    # "mobilenet_v2"
    # "resnet18"
    # "efficientnet_b0"

    # 数据参数
    image_size = 224 # 图像大小
    num_classes = 102 # 类别数量

    # 训练参数
    batch_size = 32
    num_epochs_stage1 = 20  # 阶段1：只训练分类头
    num_epochs_stage2 = 30  # 阶段2：全微调
    lr_stage1 = 1e-3  # 阶段1学习率
    lr_stage2 = 1e-5  # 阶段2学习率

    # 设备
    device = 'cuda' if torch.cuda.is_available() else 'cpu' # 设备选择（GPU或CPU）

    # 数据增强参数
    random_rotation = 15 # 随机旋转角度
    brightness = 0.2 # 亮度抖动
    contrast = 0.2 # 对比度抖动
    saturation = 0.2 # 饱和度抖动

    # ImageNet 标准化参数（用于预训练模型）
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    # 花卉类别名称列表（索引 0-101 对应 1-102）
    flower_classes = [
        "pink primrose",
        "hard-leaved pocket orchid",
        "canterbury bells",
        "sweet pea",
        "english marigold",
        "tiger lily",
        "moon orchid",
        "bird of paradise",
        "monkshood",
        "globe thistle",
        "snapdragon",
        "colt's foot",
        "king protea",
        "spear thistle",
        "yellow iris",
        "globe-flower",
        "purple coneflower",
        "peruvian lily",
        "balloon flower",
        "giant white arum lily",
        "fire lily",
        "pincushion flower",
        "fritillary",
        "red ginger",
        "grape hyacinth",
        "corn poppy",
        "prince of wales feathers",
        "stemless gentian",
        "artichoke",
        "sweet william",
        "carnation",
        "garden phlox",
        "love in the mist",
        "mexican aster",
        "alpine sea holly",
        "ruby-lipped cattleya",
        "cape flower",
        "great masterwort",
        "siam tulip",
        "lenten rose",
        "barbeton daisy",
        "daffodil",
        "sword lily",
        "poinsettia",
        "bolero deep blue",
        "wallflower",
        "marigold",
        "buttercup",
        "oxeye daisy",
        "common dandelion",
        "petunia",
        "wild pansy",
        "primula",
        "sunflower",
        "pelargonium",
        "bishop of llandaff",
        "gaura",
        "geranium",
        "orange dahlia",
        "pink-yellow dahlia",
        "cautleya spicata",
        "japanese anemone",
        "black-eyed susan",
        "silverbush",
        "californian poppy",
        "osteospermum",
        "spring crocus",
        "bearded iris",
        "windflower",
        "tree poppy",
        "gazania",
        "azalea",
        "water lily",
        "rose",
        "thorn apple",
        "morning glory",
        "passion flower",
        "lotus",
        "toad lily",
        "anthurium",
        "frangipani",
        "clematis",
        "hibiscus",
        "columbine",
        "desert-rose",
        "tree mallow",
        "magnolia",
        "cyclamen",
        "watercress",
        "canna lily",
        "hippeastrum",
        "bee balm",
        "ball moss",
        "foxglove",
        "bougainvillea",
        "camellia",
        "mallow",
        "mexican petunia",
        "bromelia",
        "blanket flower",
        "trumpet creeper",
        "blackberry lily"
    ]

config = Config()



