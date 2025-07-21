# -*- coding: utf-8 -*-
"""
游戏数据模块
包含游戏常量配置、工具函数和资源加载功能
"""

import pygame
import math
import os
import time

# === 屏幕设置 ===
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # 游戏窗口的默认分辨率
BASE_WIDTH, BASE_HEIGHT = 1920, 1080      # UI缩放基准分辨率

# === 颜色定义 ===
BACKGROUND = (30, 30, 50)          # 背景颜色
TEXT_COLOR = (220, 220, 255)        # 常规文本颜色
EXIT_BUTTON_COLOR = (200, 50, 50)  # 退出按钮颜色
KEY_PRESSED_COLOR = (0, 255, 0)     # 按键按下时的文本颜色
INFO_COLOR = (100, 200, 255)        # 信息文本颜色
PANEL_COLOR = (40, 40, 60, 200)     # 面板背景颜色 (RGBA)
UI_HIGHLIGHT = (80, 120, 200, 180)  # UI高亮色 (RGBA)

# === UI 常量 ===
UI_PADDING = 15                # UI元素的内边距
UI_LINE_SPACING = 25           # UI行间距
UI_PANEL_ALPHA = 180           # 面板透明度
ITEM_SLOT_SIZE = 60                # 物品槽大小
ITEM_SLOT_MARGIN = 20              # 物品槽边距

# === 字体大小常量 ===
TITLE_FONT_SIZE = 74           # 主标题字体大小
SUBTITLE_FONT_SIZE = 44        # 副标题字体大小
DEFAULT_FONT_SIZE = 24         # 默认字体大小
INFO_FONT_SIZE = 22            # 信息字体大小
SMALL_FONT_SIZE = 20           # 小号字体大小

# 主菜单字体大小
MENU_TITLE_FONT_SIZE = 60
MENU_OPTION_FONT_SIZE = 36

# 游戏界面字体大小
GAME_TITLE_FONT_SIZE = 44
GAME_DEFAULT_FONT_SIZE = 24

# 回放系统字体大小
REPLAY_TITLE_FONT_SIZE = 44
REPLAY_DEFAULT_FONT_SIZE = 24
REPLAY_INFO_FONT_SIZE = 22

# === 网格常量 ===
GRID_SIZE = 40                 # 网格基础尺寸
GRID_COLOR = (50, 50, 70)      # 网格线颜色
GROUND_COLOR = (100, 150, 100) # 地面线颜色
GROUND_OFFSET = 100            # 地面距离底部偏移

# === 玩家常量 ===
PLAYER_SIZE = (80, 80)         # 玩家图像尺寸
PLAYER_OUTER_COLOR = (100, 200, 255)  # 玩家外圈颜色
PLAYER_MIDDLE_COLOR = (255, 255, 255) # 玩家中圈颜色
PLAYER_INNER_COLOR = (70, 130, 180)   # 玩家内圈颜色

# === 录制系统常量 ===
RECORD_VERSION = 2             # 录制文件格式版本号
RECORD_FPS = 64                # 录制帧率 (每秒记录次数)
RECORD_PREFIX_COMMAND = "C:"   # 高阶指令前缀
RECORD_PREFIX_INPUT = "I:"     # 原始输入前缀
RECORD_PREFIX_SNAPSHOT = "S:" # 状态快照前缀

# === 移动参数 ===
WALK_SPEED = 250.0             # 行走速度 (像素/秒)
SPRINT_SPEED = 320.0           # 奔跑速度 (像素/秒)
ACCELERATION = 20.0            # 加速度 (像素/秒²)
DECELERATION = 15.0            # 减速度 (像素/秒²)
AIR_ACCELERATION = 10.0        # 空中加速度 (未使用)
FRICTION = 5.0                 # 摩擦系数

# === 监控的键位 ===
KEYS_TO_MONITOR = {
    pygame.K_d: "D键",         # 向右移动
    pygame.K_w: "W键",         # 向上移动
    pygame.K_a: "A键",         # 向左移动
    pygame.K_s: "S键",         # 向下移动
    pygame.K_LSHIFT: "左Shift键",  # 奔跑键
    pygame.K_RSHIFT: "右Shift键",  # 奔跑键
    pygame.K_F1: "F1键",       # 显示/隐藏键盘状态
    pygame.K_F2: "F2键"        # 开启/关闭录制
}

# === 工具函数 ===
def get_timestamp():
    """获取当前时间戳（字符串格式）"""
    return time.strftime("%Y%m%d_%H%M%S")

def is_within_screen(pos, screen):
    """检查位置是否在屏幕内"""
    x, y = pos
    return 0 <= x <= screen.get_width() and 0 <= y <= screen.get_height()

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
        # 缩放图像到指定尺寸
        return pygame.transform.scale(player_image, PLAYER_SIZE)
    except:
        # 创建替代图像
        surface = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        # 绘制圆形玩家表示
        center = (PLAYER_SIZE[0] // 2, PLAYER_SIZE[1] // 2)
        pygame.draw.circle(surface, PLAYER_OUTER_COLOR, center, 35)  # 外圈
        pygame.draw.circle(surface, PLAYER_MIDDLE_COLOR, center, 30)  # 中圈
        pygame.draw.circle(surface, PLAYER_INNER_COLOR, center, 20)   # 内圈
        return surface

def get_font(size=DEFAULT_FONT_SIZE):
    """
    获取指定大小的字体
    
    参数:
        size (int): 字体大小，默认为DEFAULT_FONT_SIZE
    
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

def get_scaled_font(base_size, screen, min_size=12):
    """
    获取缩放后的字体大小，确保最小字体大小
    
    参数:
        base_size (int): 基础字体大小
        screen (pygame.Surface): 当前屏幕表面
        min_size (极速): 最小字体大小
    
    返回:
        int: 缩放后的字体大小
    """
    # 计算水平和垂直方向的缩放比例
    width_scale = screen.get_width() / BASE_WIDTH
    height_scale = screen.get_height() / BASE_HEIGHT
    
    # 使用较小的缩放比例
    scale = min(width_scale, height_scale)
    
    # 计算缩放后的字体大小
    scaled_size = int(base_size * scale)
    
    # 确保字体不小于最小值
    return max(scaled_size, min_size)

def serialize_high_level_command(pressed_keys):
    """
    序列化高阶指令（用于录制系统）
    
    参数:
        pressed_keys (dict): 当前按下的按键状态
        
    返回:
        str: 序列化的高阶指令字符串
    """
    command = []
    if pressed_keys[pygame.K_w]: command.append('W')
    if pressed_keys[pygame.K_s]: command.append('S')
    if pressed_keys[pygame.K_a]: command.append('A')
    if pressed_keys[pygame.K_d]: command.append('D')
    if pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]: 
        command.append('SHIFT')
    return ",".join(command)

def get_rgba_color(base_rgba, alpha=None):
    """
    获取 RGBA 颜色，可选择覆盖 alpha 值
    
    参数:
        base_rgba (tuple): 基础 RGBA 颜色 (4个值)
        alpha (int, optional): 新的 alpha 值 (0-255)
    
    返回:
        tuple: RGBA 颜色元组
    """
    if alpha is None:
        return base_rgba
    return (base_rgba[0], base_rgba[1], base_rgba[2], alpha)