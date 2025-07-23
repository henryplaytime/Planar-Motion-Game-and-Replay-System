"""
物品系统模块
定义游戏中的物品类及其功能，包括物品配置加载、图像处理和使用效果
"""

import pygame
import os
import json
import sys

class Item:
    """
    基础物品类
    
    功能概述:
    1. 加载物品配置
    2. 加载和处理物品图像
    3. 提供物品使用接口
    
    属性说明:
    - id: 物品ID
    - config: 物品配置字典
    - name: 物品名称
    - description: 物品描述
    - image: 物品图像表面
    - gray_image: 物品的灰色图像(用于冷却等状态)
    """
    
    def __init__(self, item_id):
        """
        初始化物品对象
        
        参数:
        - item_id: 物品ID(字符串)
        """
        self.id = item_id  # 物品ID
        self.config = self._load_config(item_id)  # 加载物品配置
        self.name = self.config["name"]  # 物品名称
        self.description = self.config["description"]  # 物品描述
        self.image = self._load_image(self.config["image_path"])  # 加载物品图像
        self.gray_image = None  # 灰色图像(初始为None)
        if self.image:
            self.gray_image = self._create_gray_image(self.image)  # 创建灰色版本
    
    def _load_config(self, item_id):
        """
        加载物品配置
        
        参数:
        - item_id: 物品ID
        
        返回:
        - dict: 物品配置字典
        
        说明:
        从config/items.json中加载对应物品ID的配置
        如果加载失败，返回默认配置
        """
        try:
            # 构建配置文件路径
            config_path = os.path.join(os.path.dirname(__file__), "config", "items.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data[item_id]  # 返回对应ID的配置
        except Exception as e:
            print(f"加载物品配置失败: {str(e)}")
            # 返回默认配置
            return {
                "name": "未知物品",
                "description": "无法加载物品配置",
                "image_path": None,
                "duration": 0,  # 持续时间
                "cooldown": 0,  # 冷却时间
                "speed_multiplier": 1.0  # 速度倍率
            }
    
    def _load_image(self, image_path):
        """
        加载物品图像
        
        参数:
        - image_path: 图像文件路径(相对路径)
        
        返回:
        - pygame.Surface: 图像表面
        """
        if not image_path: 
            return None  # 没有图像路径则返回None
        try:
            # 构建完整图像路径
            image_full_path = os.path.join(os.path.dirname(__file__), image_path)
            return pygame.image.load(image_full_path).convert_alpha()  # 加载并转换
        except:
            # 加载失败则创建一个默认图像
            surface = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(surface, (200, 200, 200), (0, 0, 50, 50), border_radius=5)
            return surface
    
    def _create_gray_image(self, image):
        """
        创建物品的灰色图像(用于冷却状态)
        
        参数:
        - image: 原始图像表面
        
        返回:
        - pygame.Surface: 灰色图像表面
        """
        gray_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        # 遍历每个像素，转换为灰度
        for x in range(image.get_width()):
            for y in range(image.get_height()):
                r, g, b, a = image.get_at((x, y))
                gray = int(0.2989 * r + 0.5870 * g + 0.1140 * b)  # 灰度转换公式
                gray_image.set_at((x, y), (gray, gray, gray, a))
        return gray_image
    
    def use(self, player):
        """
        使用物品(抽象方法)
        
        参数:
        - player: 玩家对象
        
        返回:
        - bool: 使用是否成功
        
        说明:
        子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现此方法")

class AdrenalineItem(Item):
    """
    肾上腺素物品类(继承自Item)
    
    功能概述:
    1. 实现肾上腺素物品的具体效果
    2. 管理物品的激活和冷却
    """
    
    def __init__(self):
        """初始化肾上腺素物品，物品ID固定为'adrenaline'"""
        super().__init__("adrenaline")
    
    def use(self, player):
        """
        使用肾上腺素物品
        
        参数:
        - player: 玩家对象
        
        返回:
        - bool: 使用是否成功
        
        说明:
        1. 如果物品已在激活状态，则无法再次使用
        2. 如果物品在冷却中，则无法使用
        3. 使用成功后，设置玩家的肾上腺素状态
        """
        # 如果肾上腺素已激活，则不能再次使用
        if player.adrenaline_active:
            return False
            
        # 检查是否在冷却时间内
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time < player.adrenaline_cooldown_end:
            return False
            
        # 激活肾上腺素效果
        player.adrenaline_active = True
        player.adrenaline_active_end = current_time + self.config["duration"]  # 设置结束时间
        player.adrenaline_cooldown_end = current_time + self.config["cooldown"]  # 设置冷却结束时间
        player.adrenaline_flash_start = current_time  # 设置闪烁开始时间
        player.adrenaline_edge_effect = True  # 启用边缘效果
        return True

# 物品注册表
ITEM_REGISTRY = {
    "adrenaline": AdrenalineItem  # 注册肾上腺素物品类
}

def get_item(item_id):
    """
    根据物品ID获取物品对象
    
    参数:
    - item_id: 物品ID
    
    返回:
    - Item: 物品对象，如果未注册则返回None
    """
    if item_id in ITEM_REGISTRY:
        return ITEM_REGISTRY[item_id]()  # 创建物品对象并返回
    return None