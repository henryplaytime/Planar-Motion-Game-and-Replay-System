"""
物品系统模块
定义游戏中的物品类及其功能
"""

import pygame
import os
import json
import sys
import data

class Item:
    """
    基础物品类
    
    功能概述:
    1. 加载物品配置
    2. 加载和处理物品图像
    3. 提供物品使用接口
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
        
        返回:
        - dict: 物品配置字典
        """
        try:
            # 构建配置文件路径
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "config", 
                "item.json"
            )
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 从items键获取配置
            item_config = config_data["items"].get(item_id, {})
            
            # 添加缺失字段的默认值
            item_config.setdefault("image_path", None)
            item_config.setdefault("effects", {})
            
            return item_config
        except Exception as e:
            print(f"加载物品配置失败: {str(e)}")
            # 返回默认配置
            return {
                "name": "未知物品",
                "description": "无法加载物品配置",
                "image_path": None,
                "effects": {
                    "speed_multiplier": 1.0,
                    "duration": 0.0,
                    "cooldown": 0.0
                }
            }
    
    def _load_image(self, image_path):
        """
        加载物品图像
        
        返回:
        - pygame.Surface: 图像表面
        """
        if not image_path: 
            return None
        try:
            # 构建完整图像路径
            image_full_path = os.path.join(
                os.path.dirname(__file__), 
                image_path
            )
            return pygame.image.load(image_full_path).convert_alpha()
        except Exception as e:
            print(f"加载物品图片失败: {str(e)}")
            # 创建默认图像
            surface = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(surface, (200, 200, 200), (0, 0, 50, 50), border_radius=5)
            return surface
    
    def _create_gray_image(self, image):
        """
        创建物品的灰色图像(用于冷却状态)
        
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
        
        返回:
        - bool: 使用是否成功
        """
        raise NotImplementedError("子类必须实现此方法")

class AdrenalineItem(Item):
    """
    肾上腺素物品类
    
    功能概述:
    1. 实现肾上腺素物品的具体效果
    2. 管理物品的激活和冷却
    """
    
    def __init__(self):
        """初始化肾上腺素物品"""
        super().__init__("adrenaline")
    
    def use(self, player):
        """
        使用肾上腺素物品
        
        返回:
        - bool: 使用是否成功
        """
        # 获取配置
        effects = self.config.get("effects", {})
        duration = effects.get("duration", 5.0)
        cooldown = effects.get("cooldown", 15.0)
        speed_multiplier = effects.get("speed_multiplier", 1.5)
        
        # 激活肾上腺素效果
        return player.activate_adrenaline(duration, cooldown, speed_multiplier)

# 物品注册表
ITEM_REGISTRY = {
    "adrenaline": AdrenalineItem  # 注册肾上腺素物品类
}

def get_item(item_id):
    """
    根据物品ID获取物品对象
    
    返回:
    - Item: 物品对象
    """
    if item_id in ITEM_REGISTRY:
        return ITEM_REGISTRY[item_id]()  # 创建物品对象并返回
    return None