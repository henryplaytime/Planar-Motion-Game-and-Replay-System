# -*- coding: utf-8 -*-
"""
物品系统模块
包含物品基类和具体物品实现
"""

import pygame
import os
import json
import sys

class Item:
    """
    物品基类
    所有物品都应继承此类
    """
    
    def __init__(self, item_id):
        """
        初始化物品
        
        参数:
            item_id (str): 物品ID
        """
        self.id = item_id
        self.config = self._load_config(item_id)  # 从配置加载物品数据
        self.name = self.config["name"]
        self.description = self.config["description"]
        self.image = self._load_image(self.config["image_path"])
        self.gray_image = None
        if self.image:
            self.gray_image = self._create_gray_image(self.image)
    
    def _load_config(self, item_id):
        """从JSON文件加载物品配置"""
        try:
            # 获取配置文件路径
            config_path = os.path.join(os.path.dirname(__file__), "config", "items.json")
            
            # 读取JSON配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 返回特定物品的配置
            return config_data[item_id]
        except Exception as e:
            print(f"加载物品配置失败: {str(e)}")
            # 返回默认配置
            return {
                "name": "未知物品",
                "description": "无法加载物品配置",
                "image_path": None,
                "duration": 0,
                "cooldown": 0,
                "speed_multiplier": 1.0
            }
    
    def _load_image(self, image_path):
        """加载物品图像"""
        if not image_path:
            return None
            
        try:
            # 构建完整路径
            image_full_path = os.path.join(os.path.dirname(__file__), image_path)
            
            # 尝试加载物品图像文件
            return pygame.image.load(image_full_path).convert_alpha()
        except:
            # 创建替代图像
            surface = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(surface, (200, 200, 200), (0, 0, 50, 50), border_radius=5)
            return surface
    
    def _create_gray_image(self, image):
        """创建物品的灰度图像（用于冷却状态）"""
        gray_image = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        # 将图像转换为灰度
        for x in range(image.get_width()):
            for y in range(image.get_height()):
                r, g, b, a = image.get_at((x, y))
                # 灰度公式
                gray = int(0.2989 * r + 0.5870 * g + 0.1140 * b)
                gray_image.set_at((x, y), (gray, gray, gray, a))
        return gray_image
    
    def use(self, player):
        """
        使用物品（由子类实现）
        
        参数:
            player (Player): 玩家对象
        """
        raise NotImplementedError("子类必须实现此方法")

class AdrenalineItem(Item):
    """肾上腺素物品类"""
    
    def __init__(self):
        super().__init__("adrenaline")
    
    def use(self, player):
        """使用肾上腺素"""
        # 检查玩家是否已经激活肾上腺素
        if player.adrenaline_active:
            return False
        
        # 检查肾上腺素是否在冷却中
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time < player.adrenaline_cooldown_end:
            return False
        
        # 激活肾上腺素效果
        player.adrenaline_active = True
        player.adrenaline_active_end = current_time + self.config["duration"]
        player.adrenaline_cooldown_end = current_time + self.config["cooldown"]
        player.adrenaline_flash_start = current_time
        player.adrenaline_edge_effect = True
        
        return True

# 物品注册表
ITEM_REGISTRY = {
    "adrenaline": AdrenalineItem
}

def get_item(item_id):
    """
    根据物品ID获取物品实例
    
    参数:
        item_id (str): 物品ID
        
    返回:
        Item: 物品实例
    """
    if item_id in ITEM_REGISTRY:
        return ITEM_REGISTRY[item_id]()
    return None