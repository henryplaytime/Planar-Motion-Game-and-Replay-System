# -*- coding: utf-8 -*-
"""
游戏数据模块
包含游戏常量配置、工具函数和资源加载功能
"""

import pygame
import math
import os

# === 屏幕设置 ===
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # 游戏窗口的默认分辨率
BASE_WIDTH, BASE_HEIGHT = 1920, 1080      # UI缩放基准分辨率

# === 颜色定义 ===
BACKGROUND = (30, 30, 50)          # 背景颜色
TEXT_COLOR = (220, 220, 255)        # 常规文本颜色
KEY_PRESSED_COLOR = (0, 255, 0)     # 按键按下时的文本颜色
INFO_COLOR = (100, 200, 255)        # 信息文本颜色
PANEL_COLOR = (40, 40, 60, 200)     # 面板背景颜色 (RGBA)
UI_HIGHLIGHT = (80, 120, 200, 180)  # UI高亮色 (RGBA)

# === UI常量 ===
UI_PADDING = 15                # UI元素的内边距
UI_LINE_SPACING = 25           # UI行间距
UI_PANEL_ALPHA = 180           # 面板透明度
UI_TITLE_FONT_SIZE = 36        # 标题字体大小
UI_DEFAULT_FONT_SIZE = 24      # 默认字体大小
UI_INFO_FONT_SIZE = 20         # 信息字体大小
UI_SCALE_THRESHOLD = 1.0       # UI最小缩放比例

# === 移动参数 ===
WALK_SPEED = 250.0             # 行走速度 (像素/秒)
SPRINT_SPEED = 320.0           # 奔跑速度 (像素/秒)
ACCELERATION = 20.0            # 加速度 (像素/秒²)
DECELERATION = 15.0            # 减速度 (像素/秒²)
AIR_ACCELERATION = 10.0        # 空中加速度 (未使用)
FRICTION = 5.0                 # 摩擦系数

RECORD_FPS = 8                 # 录制帧率 (每秒记录次数)

# === 监控的键位 ===
KEYS_TO_MONITOR = {
    pygame.K_d: "D键",         # 向右移动
    pygame.K_w: "W键",         # 向上移动
    pygame.K_a: "A键",         # 向左移动
    pygame.K_s: "S键",         # 向下移动
    pygame.K_LSHIFT: "左Shift键",  # 奔跑键
    pygame.K_RSHIFT: "右Shift键",  # 奔跑键
}

def load_player_image():
    """
    加载玩家图像
    如果文件不存在则创建替代图像
    
    返回:
        pygame.Surface: 玩家图像表面
    """
    try:
        # 尝试加载玩家图像文件
        player_image = pygame.image.load("player_image.png").convert_alpha()
        # 缩放图像到80x80像素
        return pygame.transform.scale(player_image, (80, 80))
    except:
        # 创建替代图像
        surface = pygame.Surface((80, 80), pygame.SRCALPHA)
        # 绘制圆形玩家表示
        pygame.draw.circle(surface, (100, 200, 255), (40, 40), 35)  # 外圈
        pygame.draw.circle(surface, (255, 255, 255), (40, 40), 30)  # 中圈
        pygame.draw.circle(surface, (70, 130, 180), (40, 40), 20)   # 内圈
        return surface

def get_font(size=UI_DEFAULT_FONT_SIZE):
    """
    获取指定大小的字体
    
    参数:
        size (int): 字体大小，默认为UI_DEFAULT_FONT_SIZE
    
    返回:
        pygame.font.Font: 字体对象
    """
    return pygame.font.SysFont("simhei", size)

def init_pygame():
    """
    初始化Pygame并返回屏幕对象
    
    返回:
        pygame.Surface: 游戏窗口表面
    """
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("玩家控制与键盘检测 (平面移动游戏)")
    # 禁用按键重复事件
    pygame.key.set_repeat(0)
    # 屏蔽文本输入事件
    pygame.event.set_blocked(pygame.TEXTINPUT)
    return screen

def calculate_speed(velocity):
    """
    计算速度向量的大小
    
    参数:
        velocity (list): 包含[x, y]速度分量的列表
    
    返回:
        float: 速度大小
    """
    return math.sqrt(velocity[0] ** 2 + velocity[1] ** 2)

def scale_position(x, y, screen):
    """
    根据当前屏幕尺寸缩放位置
    
    参数:
        x (float): 原始x坐标
        y (float): 原始y坐标
        screen (pygame.Surface): 当前屏幕表面
    
    返回:
        tuple: 缩放后的(x, y)坐标
    """
    width_ratio = screen.get_width() / BASE_WIDTH
    height_ratio = screen.get_height() / BASE_HEIGHT
    return x * width_ratio, y * height_ratio

def scale_value(value, screen, is_width=True):
    """
    缩放尺寸值
    
    参数:
        value (float): 原始尺寸值
        screen (pygame.Surface): 当前屏幕表面
        is_width (bool): True表示缩放宽度，False表示缩放高度
    
    返回:
        float: 缩放后的尺寸值
    """
    if is_width:
        return value * (screen.get_width() / BASE_WIDTH)
    return value * (screen.get_height() / BASE_HEIGHT)

def get_scaled_font(base_size, screen):
    """
    获取缩放后的字体大小
    
    参数:
        base_size (int): 基础字体大小
        screen (pygame.Surface): 当前屏幕表面
    
    返回:
        int: 缩放后的字体大小
    """
    # 计算水平和垂直方向的缩放比例
    width_scale = screen.get_width() / BASE_WIDTH
    height_scale = screen.get_height() / BASE_HEIGHT
    # 取较小的缩放比例，但不小于阈值
    scale = min(
        max(UI_SCALE_THRESHOLD, width_scale),
        max(UI_SCALE_THRESHOLD, height_scale)
    )
    return int(base_size * scale)