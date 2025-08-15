"""
可配置的主菜单界面实现
加载用户配置文件并传递给主程序
"""

import pygame
import sys
import os
import math
import json
from data import DEFAULT_MENU_CONFIG  # 从data.py导入默认配置

def load_font(path, size):
    """
    加载字体
    
    参数:
        path (str): 字体文件路径
        size (int): 字体大小
    """
    try:
        return pygame.font.Font(path, size)
    except pygame.error as e:
        print(f"无法加载字体: {e}")
        return pygame.font.SysFont(None, size)  # 回退到默认字体

def draw_animation_lines(screen, elapsed, config):
    """
    绘制循环动画线条
    
    参数:
        screen (pygame.Surface): 目标表面
        elapsed (int): 已过去的时间(毫秒)
        config (dict): 配置字典
    """
    if not config["animation_lines"]["enabled"]:
        return
        
    line_cfg = config["animation_lines"]
    screen_height = screen.get_height()
    screen_width = screen.get_width()
    
    # 计算线条位置
    line_y = screen_height // 2 + line_cfg["vertical_offset"]
    left_line_x = screen_width // 2 - line_cfg["length"] - line_cfg["horizontal_gap"]
    right_line_x = screen_width // 2 + line_cfg["horizontal_gap"]
    
    # 计算动画进度(0-1循环)
    progress = elapsed % line_cfg["duration"] / line_cfg["duration"]
    ease_progress = math.sin(progress * math.pi)  # 使用正弦函数实现平滑变化
    
    # 计算当前帧的线条长度
    current_left_length = line_cfg["length"] * abs(ease_progress)
    current_right_length = line_cfg["length"] * abs(ease_progress)
    
    # 绘制左侧线条(从右向左延伸)
    pygame.draw.line(
        screen, line_cfg["color"],
        (left_line_x + line_cfg["length"] - current_left_length, line_y),
        (left_line_x + line_cfg["length"], line_y),
        line_cfg["thickness"]
    )
    
    # 绘制右侧线条(从左向右延伸)
    pygame.draw.line(
        screen, line_cfg["color"],
        (right_line_x, line_y),
        (right_line_x + current_right_length, line_y),
        line_cfg["thickness"]
    )

def update_fade(fade_alpha, fade_in, elapsed, config):
    """
    更新淡入淡出效果
    
    参数:
        fade_alpha (int): 当前透明度
        fade_in (bool): 是否处于淡入阶段
        elapsed (int): 已过去的时间(毫秒)
        config (dict): 配置字典
    """
    if not config["fade"]["enabled"]:
        return fade_alpha, fade_in
        
    fade_cfg = config["fade"]
    duration = fade_cfg["duration"]
    
    if elapsed % duration < duration / 2:  # 淡入阶段
        fade_alpha = min(255, fade_cfg["initial_alpha"] + 255 * (elapsed % duration) / (duration / 2))
        fade_in = True
    else:  # 淡出阶段
        fade_alpha = max(0, 255 - 255 * (elapsed % duration - duration / 2) / (duration / 2))
        fade_in = False
    return fade_alpha, fade_in

def load_user_config():
    """
    加载用户配置文件
    返回用户配置字典，如果文件不存在或加载失败则返回空字典
    """
    config_path = "user/user_config.json"
    
    # 检查目录是否存在
    if not os.path.exists("user"):
        try:
            os.makedirs("user")
            print("已创建 user 目录")
        except Exception as e:
            print(f"创建 user 目录失败: {e}")
            return {}
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        print(f"用户配置文件不存在: {config_path}")
        return {}
    
    # 尝试加载配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            print(f"成功加载用户配置文件: {config_path}")
            return user_config
    except Exception as e:
        print(f"加载用户配置文件失败: {e}")
        return {}

def show_loading_menu():
    """
    显示加载菜单界面，当用户按下空格键或回车键时退出
    返回加载的用户配置字典
    """
    # 使用data.py中的默认配置
    config = DEFAULT_MENU_CONFIG
    
    # 加载用户配置文件
    user_config = load_user_config()
    
    # 初始化pygame
    pygame.init()
    screen = pygame.display.set_mode(config["window"]["size"], pygame.RESIZABLE)
    pygame.display.set_caption(config["window"]["title"])
    screen_width, screen_height = screen.get_size()
    
    # 设置标题文本
    title_text = None
    title_rect = None
    if config["title"]["enabled"]:
        title_cfg = config["title"]
        font = load_font(title_cfg["font_path"], title_cfg["font_size"])
        title_text = font.render(title_cfg["text"], True, title_cfg["color"])
        title_x = int(title_cfg["position"][0] * screen_width)
        title_y = int(title_cfg["position"][1] * screen_height)
        title_rect = title_text.get_rect(center=(title_x, title_y))
    
    # 设置提示文本
    prompt_text = None
    prompt_rect = None
    if config["prompt"]["enabled"]:
        prompt_cfg = config["prompt"]
        font = load_font(prompt_cfg["font_path"], prompt_cfg["font_size"])
        prompt_text = font.render(prompt_cfg["text"], True, prompt_cfg["color"])
        prompt_x = int(prompt_cfg["position"][0] * screen_width)
        prompt_y = int(prompt_cfg["position"][1] * screen_height)
        prompt_rect = prompt_text.get_rect(center=(prompt_x, prompt_y))
    
    # 初始化音频系统
    if config["music"]["enabled"] and pygame.mixer.get_init() is None:
        pygame.mixer.init()
    
    # 播放背景音乐
    if config["music"]["enabled"]:
        try:
            pygame.mixer.music.load(config["music"]["path"])
            pygame.mixer.music.play(-1)  # 循环播放
            pygame.mixer.music.set_volume(config["music"]["volume"])
        except pygame.error as e:
            print(f"音乐播放失败: {e}")
    
    # 初始化动画计时器
    line_start_time = pygame.time.get_ticks()
    
    # 初始化淡入淡出参数
    fade_alpha = config["fade"]["initial_alpha"]
    fade_in = True
    
    # 主循环
    clock = pygame.time.Clock()
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - line_start_time
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    # 按空格键或回车键退出
                    running = False
        
        # 清屏
        screen.fill(config["window"]["background_color"])
        
        # 绘制标题
        if title_text and title_rect:
            screen.blit(title_text, title_rect)
        
        # 绘制动画线条
        if config["animation_lines"]["enabled"]:
            draw_animation_lines(screen, elapsed, config)
        
        # 绘制提示文本
        if prompt_text and prompt_rect:
            if config["fade"]["enabled"]:
                fade_alpha, fade_in = update_fade(fade_alpha, fade_in, elapsed, config)
                prompt_text.set_alpha(fade_alpha)
            screen.blit(prompt_text, prompt_rect)
        
        pygame.display.flip()
        clock.tick(config["game"]["fps"])
    
    # 清理资源
    if pygame.mixer.get_init() and config["music"]["enabled"]:
        pygame.mixer.music.stop()
    pygame.quit()
    
    # 返回加载的用户配置
    return user_config

if __name__ == "__main__":
    # 测试模式
    user_config = show_loading_menu()
    print("加载的用户配置:", user_config)