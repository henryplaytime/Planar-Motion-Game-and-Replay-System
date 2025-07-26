"""
游戏数据模块
包含游戏全局常量、工具函数和资源加载功能
提供屏幕适配、颜色定义、物理参数等核心数据
"""

import pygame
import math
import os
import time

# === 屏幕设置 ===
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # 默认屏幕分辨率
BASE_WIDTH, BASE_HEIGHT = 1920, 1080  # 基准分辨率(用于缩放计算)

# === 颜色定义 ===
BACKGROUND = (30, 30, 50)  # 背景色(深蓝灰)
TEXT_COLOR = (220, 220, 255)  # 文本颜色(浅蓝白)
EXIT_BUTTON_COLOR = (200, 50, 50)  # 退出按钮颜色(红色)
KEY_PRESSED_COLOR = (0, 255, 0)  # 按键按下时的颜色(绿色)
INFO_COLOR = (100, 200, 255)  # 信息文本颜色(天蓝色)
PANEL_COLOR = (40, 40, 60, 200)  # UI面板颜色(深蓝灰带透明度)
UI_HIGHLIGHT = (80, 120, 200, 180)  # UI高亮颜色(蓝色带透明度)
ADRENALINE_COLOR = (255, 50, 50, 180)  # 肾上腺素效果颜色(红色半透明)

# === UI 常量 ===
UI_PADDING = 15  # UI元素内边距
UI_LINE_SPACING = 25  # UI行间距
UI_PANEL_ALPHA = 180  # UI面板透明度
ITEM_SLOT_SIZE = 60  # 物品槽尺寸
ITEM_SLOT_MARGIN = 20  # 物品槽外边距

# === 字体大小常量 ===
TITLE_FONT_SIZE = 74  # 标题字体大小
SUBTITLE_FONT_SIZE = 44  # 副标题字体大小
DEFAULT_FONT_SIZE = 24  # 默认字体大小
INFO_FONT_SIZE = 22  # 信息文本字体大小
SMALL_FONT_SIZE = 20  # 小号字体大小
MENU_TITLE_FONT_SIZE = 60  # 菜单标题字体大小
MENU_OPTION_FONT_SIZE = 36  # 菜单选项字体大小
GAME_TITLE_FONT_SIZE = 44  # 游戏内标题字体大小
GAME_DEFAULT_FONT_SIZE = 24  # 游戏内默认字体大小
REPLAY_TITLE_FONT_SIZE = 44  # 回放模式标题字体大小
REPLAY_DEFAULT_FONT_SIZE = 24  # 回放模式默认字体大小
REPLAY_INFO_FONT_SIZE = 22  # 回放模式信息文本字体大小

# === 网格常量 ===
GRID_SIZE = 40  # 网格单元格大小
GRID_COLOR = (50, 50, 70)  # 网格线颜色(深蓝灰)
GROUND_COLOR = (100, 150, 100)  # 地面颜色(草绿色)
GROUND_OFFSET = 100  # 地面距离屏幕底部偏移量

# === 玩家常量 ===
PLAYER_SIZE = (80, 80)  # 玩家尺寸(宽,高)
PLAYER_OUTER_COLOR = (100, 200, 255)  # 玩家外层颜色(浅蓝)
PLAYER_MIDDLE_COLOR = (255, 255, 255)  # 玩家中层颜色(白色)
PLAYER_INNER_COLOR = (70, 130, 180)  # 玩家内层颜色(深蓝)

# === 录制系统常量 ===
RECORD_VERSION = 2  # 录制文件格式版本
RECORD_FPS = 64  # 录制帧率
RECORD_PREFIX_COMMAND = "C:"  # 高阶指令前缀
RECORD_PREFIX_INPUT = "I:"  # 原始输入前缀
RECORD_PREFIX_SNAPSHOT = "S:"  # 状态快照前缀

# === 移动参数 ===
WALK_SPEED = 250.0  # 行走速度(像素/秒)
SPRINT_SPEED = 320.0  # 奔跑速度(像素/秒)
ACCELERATION = 20.0  # 加速度(像素/秒²)
DECELERATION = 15.0  # 减速度(像素/秒²)
AIR_ACCELERATION = 10.0  # 空中加速度(像素/秒²)
FRICTION = 5.0  # 摩擦力系数

# === 控制台参数 ===
CONSOLE_HEIGHT = 500  # 控制台默认高度
Max_Output_Lines = 20  # 控制台最大输出行数

# === 监控的键位 ===
KEYS_TO_MONITOR = {
    pygame.K_d: "D键",  # 右移键
    pygame.K_w: "W键",  # 上移键
    pygame.K_a: "A键",  # 左移键
    pygame.K_s: "S键",  # 下移键
    pygame.K_LSHIFT: "左Shift键",  # 冲刺键
    pygame.K_RSHIFT: "右Shift键",  # 冲刺键(备用)
    pygame.K_F1: "F1键",  # 显示/隐藏检测面板
    pygame.K_F2: "F2键"  # 开始/停止录制
}

# === 工具函数 ===
def get_timestamp():
    """
    获取当前时间戳(用于文件名)
    
    返回:
    - str: 格式为YYYYMMDD_HHMMSS的时间字符串
    """
    return time.strftime("%Y%m%d_%H%M%S")

def is_within_screen(pos, screen):
    """
    检查点是否在屏幕范围内
    
    参数:
    - pos: (x, y)坐标元组
    - screen: pygame屏幕对象
    
    返回:
    - bool: 如果点在屏幕内返回True
    """
    x, y = pos
    return 0 <= x <= screen.get_width() and 0 <= y <= screen.get_height()

def load_player_image():
    """
    加载玩家图像
    
    如果找不到图像文件，则创建一个圆形玩家图形
    
    返回:
    - pygame.Surface: 玩家图像表面
    """
    try:
        # 尝试从文件加载玩家图像
        player_image = pygame.image.load("player_image.png").convert_alpha()
        return pygame.transform.scale(player_image, PLAYER_SIZE)
    except:
        # 创建默认玩家图形
        surface = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        center = (PLAYER_SIZE[0] // 2, PLAYER_SIZE[1] // 2)
        # 绘制三层同心圆
        pygame.draw.circle(surface, PLAYER_OUTER_COLOR, center, 35)
        pygame.draw.circle(surface, PLAYER_MIDDLE_COLOR, center, 30)
        pygame.draw.circle(surface, PLAYER_INNER_COLOR, center, 20)
        return surface

def get_font(size=DEFAULT_FONT_SIZE):
    """
    获取字体对象
    
    参数:
    - size: 字体大小(可选，默认24)
    
    返回:
    - pygame.font.Font: 字体对象
    """
    return pygame.font.SysFont("simhei", size)

def init_pygame():
    """
    初始化Pygame
    
    创建游戏窗口并设置基本参数
    
    返回:
    - pygame.Surface: 初始化的屏幕对象
    """
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("玩家控制与键盘检测 (平面移动游戏)")
    pygame.key.set_repeat(0)  # 禁用按键重复
    pygame.event.set_blocked(pygame.TEXTINPUT)  # 禁用文本输入事件
    return screen

def calculate_speed(velocity):
    """
    计算速度向量的大小
    
    参数:
    - velocity: (x, y)速度向量
    
    返回:
    - float: 速度大小
    """
    return math.sqrt(velocity[0] ** 2 + velocity[1] ** 2)

def scale_position(x, y, screen):
    """
    缩放位置坐标(基于基准分辨率)
    
    参数:
    - x, y: 原始坐标
    - screen: 当前屏幕对象
    
    返回:
    - (scaled_x, scaled_y): 缩放后的坐标
    """
    width_ratio = screen.get_width() / BASE_WIDTH
    height_ratio = screen.get_height() / BASE_HEIGHT
    return x * width_ratio, y * height_ratio

def scale_value(value, screen, is_width=True):
    """
    缩放数值(基于基准分辨率)
    
    参数:
    - value: 原始值
    - screen: 当前屏幕对象
    - is_width: 是否基于宽度缩放(False则基于高度)
    
    返回:
    - float: 缩放后的值
    """
    if is_width:
        return value * (screen.get_width() / BASE_WIDTH)
    return value * (screen.get_height() / BASE_HEIGHT)

def get_scaled_font(base_size, screen, min_size=12):
    """
    获取缩放后的字体大小
    
    参数:
    - base_size: 基准字体大小
    - screen: 当前屏幕对象
    - min_size: 最小字体大小(可选，默认12)
    
    返回:
    - int: 缩放后的字体大小
    """
    width_scale = screen.get_width() / BASE_WIDTH
    height_scale = screen.get_height() / BASE_HEIGHT
    scale = min(width_scale, height_scale)  # 使用最小缩放因子保持比例
    scaled_size = int(base_size * scale)
    return max(scaled_size, min_size)  # 确保不小于最小尺寸

def serialize_high_level_command(pressed_keys):
    """
    序列化高阶命令(用于录制)
    
    参数:
    - pressed_keys: pygame.key.get_pressed()返回的状态列表
    
    返回:
    - str: 逗号分隔的命令字符串(W/S/A/D/SHIFT)
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
    获取RGBA颜色，可选择覆盖透明度
    
    参数:
    - base_rgba: 基础RGBA颜色元组(R,G,B,A)
    - alpha: 覆盖的透明度值(可选)
    
    返回:
    - tuple: (R, G, B, A)颜色元组
    """
    if alpha is None:
        return base_rgba
    return (base_rgba[0], base_rgba[1], base_rgba[2], alpha)