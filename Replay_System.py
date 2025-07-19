# -*- coding: utf-8 -*-
"""
游戏回放系统模块
包含回放功能实现、回放控制和UI界面
"""

import pygame
import sys
import os
import glob
import time
import bisect
import data
from enum import Enum
from data import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND, load_player_image, get_font, calculate_speed, PANEL_COLOR, TEXT_COLOR, INFO_COLOR
from player import Player

# === 回放状态枚举 ===
class ReplayState(Enum):
    """
    回放状态枚举
    定义回放系统的各种播放状态
    """
    PLAYING = 1    # 正常播放状态
    PAUSED = 2     # 暂停状态
    FAST_FORWARD = 3  # 快进状态
    REWIND = 4      # 后退状态

# === 回放系统类 ===
class GameReplayer:
    """
    游戏回放类
    负责加载、解析和控制回放数据
    """
    
    def __init__(self, filename, screen):
        """
        初始化回放器
        
        参数:
            filename (str): 回放文件名
            screen (pygame.Surface): 游戏窗口表面
        """
        self.filename = filename  # 回放文件名
        self.screen = screen      # 游戏窗口表面
        self.frames = []           # 存储所有帧数据
        self.current_time = 0.0    # 当前播放时间 (秒)
        self.playback_speed = 1.0  # 播放速度倍数
        self.state = ReplayState.PLAYING  # 当前回放状态
        self.start_time = 0        # 回放开始时间
        self.total_time = 0        # 回放总时长
        self.last_update_time = 0  # 上次更新时间
        self.player = Player()     # 回放玩家对象
        
        # 加载录制数据
        self.load_recording()
    
    def load_recording(self):
        """加载并解析回放文件"""
        try:
            with open(self.filename, 'r') as f:
                # 初始化文件头变量
                screen_width = SCREEN_WIDTH
                screen_height = SCREEN_HEIGHT
                record_fps = 8  # 默认值
                
                # 逐行读取文件
                for line in f:
                    if line.startswith("SCREEN_WIDTH:"):
                        # 解析屏幕宽度
                        screen_width = int(line.split(":")[1].strip())
                    elif line.startswith("SCREEN_HEIGHT:"):
                        # 解析屏幕高度
                        screen_height = int(line.split(":")[1].strip())
                    elif line.startswith("START_TIME:"):
                        # 解析开始时间
                        self.start_time = float(line.split(":")[1].strip())
                    elif "," in line:  # 数据行
                        # 分割帧数据
                        parts = line.strip().split(",")
                        if len(parts) == 6:
                            # 创建帧元组: (时间, x位置, y位置, x速度, y速度, 冲刺状态)
                            frame = (
                                float(parts[0]),  # 时间戳
                                float(parts[1]),  # pos_x
                                float(parts[2]),  # pos_y
                                float(parts[3]),  # vel_x
                                float(parts[4]),  # vel_y
                                bool(int(parts[5])),  # sprinting
                            )
                            self.frames.append(frame)
                
                # 检查是否有有效数据
                if self.frames:
                    # 设置总时长 (最后一帧的时间戳)
                    self.total_time = self.frames[-1][0]
                    print(f"已加载回放: {len(self.frames)}帧, 总时长: {self.total_time:.2f}秒")
                else:
                    print("错误: 回放文件中没有有效数据")
        except Exception as e:
            print(f"加载回放文件失败: {str(e)}")
            self.frames = []
    
    def get_frame_at_time(self, target_time):
        """
        获取指定时间点的帧数据 (使用插值计算中间状态)
        
        参数:
            target_time (float): 目标时间点 (秒)
        
        返回:
            tuple: 插值后的帧数据
        """
        if not self.frames:
            return None
        
        # 获取所有帧的时间列表
        frame_times = [frame[0] for frame in self.frames]
        # 使用二分查找找到目标时间的位置
        idx = bisect.bisect_left(frame_times, target_time)
        
        # 如果目标时间在第一个帧之前
        if idx == 0:
            return self.frames[0]
        
        # 如果目标时间在最后一个帧之后
        if idx >= len(self.frames):
            return self.frames[-1]
        
        # 获取前后帧
        prev_frame = self.frames[idx-1]
        next_frame = self.frames[idx]
        
        # 计算插值比例
        time_diff = next_frame[0] - prev_frame[0]
        if time_diff == 0:
            return prev_frame
        
        ratio = (target_time - prev_frame[0]) / time_diff
        
        # 插值计算位置和速度
        interpolated_frame = (
            target_time,  # 目标时间
            # 线性插值x位置
            prev_frame[1] + (next_frame[1] - prev_frame[1]) * ratio,
            # 线性插值y位置
            prev_frame[2] + (next_frame[2] - prev_frame[2]) * ratio,
            # 线性插值x速度
            prev_frame[3] + (next_frame[3] - prev_frame[3]) * ratio,
            # 线性插值y速度
            prev_frame[4] + (next_frame[4] - prev_frame[4]) * ratio,
            prev_frame[5]  # sprinting状态不插值
        )
        
        return interpolated_frame
    
    def apply_frame(self, frame):
        """
        应用帧数据到玩家对象
        
        参数:
            frame (tuple): 帧数据
        """
        # 解包帧数据
        _, pos_x, pos_y, vel_x, vel_y, sprinting = frame
        # 更新玩家状态
        self.player.position = [pos_x, pos_y]
        self.player.velocity = [vel_x, vel_y]
        self.player.sprinting = sprinting
        self.player.rect.center = (int(pos_x), int(pos_y))
    
    def update(self, delta_time):
        """
        更新回放状态
        
        参数:
            delta_time (float): 时间差 (秒)
        """
        if self.state == ReplayState.PAUSED:  # 暂停状态不更新
            return
        
        # 计算实际时间步长 (考虑播放速度)
        actual_delta = delta_time * self.playback_speed
        
        # 根据状态更新当前时间
        if self.state == ReplayState.PLAYING:  # 正常播放
            self.current_time += actual_delta
        elif self.state == ReplayState.FAST_FORWARD:  # 快进 (2倍速)
            self.current_time += actual_delta * 2.0
        elif self.state == ReplayState.REWIND:  # 后退 (2倍速)
            self.current_time -= actual_delta * 2.0
        
        # 确保时间在有效范围内 [0, total_time]
        self.current_time = max(0, min(self.current_time, self.total_time))
        
        # 获取当前时间对应的帧并应用
        frame = self.get_frame_at_time(self.current_time)
        if frame:
            self.apply_frame(frame)
    
    def draw_ui(self, screen):
        """
        绘制回放控制UI
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        # 控制说明文本
        controls = [
            "空格键: 播放/暂停",
            "→: 快进",
            "←: 后退",
            "↑: 增加速度",
            "↓: 减少速度",
            "J: 跳转到指定时间",
            "ESC: 退出回放"
        ]
        
        # 计算面板尺寸 (基于最长的文本)
        max_width = 0
        for text in controls:
            # 获取文本宽度
            text_width = data.get_font(data.UI_DEFAULT_FONT_SIZE).size(text)[0]
            if text_width > max_width:
                max_width = text_width
        
        # 计算面板宽度和高度
        panel_width = max_width + data.UI_PADDING * 2
        panel_height = len(controls) * data.UI_LINE_SPACING + data.UI_PADDING * 2
        
        # 创建半透明面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 位置缩放 (右上角)
        panel_pos = data.scale_position(
            data.BASE_WIDTH - panel_width - 20, 
            20, 
            screen
        )
        screen.blit(panel, panel_pos)
        
        # 标题
        title = data.get_font(data.UI_TITLE_FONT_SIZE).render("游戏回放系统", True, data.INFO_COLOR)
        # 居中显示标题
        screen.blit(title, (panel_pos[0] + (panel_width - title.get_width()) // 2, panel_pos[1] + 10))
        
        # 回放时间信息
        time_text = data.get_font(data.UI_DEFAULT_FONT_SIZE).render(
            f"时间: {self.current_time:.1f}/{self.total_time:.1f}秒", 
            True, TEXT_COLOR
        )
        # 居中显示时间
        screen.blit(time_text, (panel_pos[0] + (panel_width - time_text.get_width()) // 2, panel_pos[1] + 50))
        
        # 状态信息
        state_text = data.get_font(data.UI_DEFAULT_FONT_SIZE).render(
            f"状态: {self.state.name} | 速度: x{self.playback_speed:.1f}", 
            True, TEXT_COLOR
        )
        # 居中显示状态
        screen.blit(state_text, (panel_pos[0] + (panel_width - state_text.get_width()) // 2, panel_pos[1] + 80))
        
        # 控制说明
        for i, text in enumerate(controls):
            ctrl_text = data.get_font(data.UI_DEFAULT_FONT_SIZE).render(text, True, TEXT_COLOR)
            screen.blit(ctrl_text, (panel_pos[0] + 10, panel_pos[1] + 120 + i * 30))
    
    def draw_progress_bar(self, screen):
        """
        绘制回放进度条
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        if not self.frames:  # 没有回放数据时不绘制
            return
        
        # 进度条尺寸
        bar_width = data.scale_value(600, screen)  # 缩放宽度
        bar_height = data.scale_value(20, screen, False)  # 缩放高度
        
        # 进度条位置 (底部居中)
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = screen.get_height() - data.scale_value(50, screen, False)
        
        # 进度条背景
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (60, 60, 80), bar_rect)
        pygame.draw.rect(screen, (100, 100, 120), bar_rect, 2)
        
        # 进度条前景 (已播放部分)
        progress = self.current_time / self.total_time
        fill_width = int(bar_width * progress)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, (80, 180, 250), fill_rect)
        
        # 当前位置标记
        marker_pos = bar_x + fill_width
        pygame.draw.line(screen, (255, 255, 255), 
                        (marker_pos, bar_y - 5), 
                        (marker_pos, bar_y + bar_height + 5), 3)
        
        # 时间标签
        time_text = data.get_font(data.UI_INFO_FONT_SIZE).render(
            f"{self.current_time:.1f}s / {self.total_time:.1f}s", 
            True, TEXT_COLOR
        )
        # 居中显示时间标签
        time_pos = (
            (screen.get_width() - time_text.get_width()) // 2,
            bar_y - data.UI_LINE_SPACING
        )
        screen.blit(time_text, time_pos)

# === 背景网格创建函数 ===
def create_background_grid(screen):
    """
    创建静态网格背景缓存
    
    参数:
        screen (pygame.Surface): 游戏窗口表面
    
    返回:
        pygame.Surface: 背景网格表面
    """
    # 计算地面位置
    ground_y = screen.get_height() - data.scale_value(100, screen, False)
    # 创建背景表面
    background_grid = pygame.Surface(screen.get_size())
    background_grid.fill(data.BACKGROUND)
    
    # 计算网格大小
    grid_size = data.scale_value(40, screen)
    
    # 绘制垂直线
    for x in range(0, screen.get_width(), int(grid_size)):
        pygame.draw.line(background_grid, (50, 50, 70), 
                        (x, 0), (x, screen.get_height()), 1)
    # 绘制水平线
    for y in range(0, screen.get_height(), int(grid_size)):
        pygame.draw.line(background_grid, (50, 50, 70), 
                        (0, y), (screen.get_width(), y), 1)
    
    # 绘制地面线
    pygame.draw.line(background_grid, (100, 150, 100), 
                    (0, ground_y), 
                    (screen.get_width(), ground_y), 3)
    return background_grid

# === 回放模式主循环 ===
def run_replay_mode(screen):
    """
    运行回放模式主循环
    
    参数:
        screen (pygame.Surface): 游戏窗口表面
    """
    # 初始化Pygame
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("游戏回放模式")
    clock = pygame.time.Clock()
    
    # 初始化字体系统
    pygame.font.init()
    
    # 检查回放文件
    replay_files = glob.glob("*.dem")
    
    # 没有回放文件的情况
    if not replay_files:
        # 创建提示文本
        font = pygame.font.SysFont("simhei", 48)
        title = font.render("没有找到回放文件", True, (255, 100, 100))
        subtitle = font.render("请先玩游戏并录制回放", True, (200, 200, 200))
        
        # 显示提示循环
        while True:
            screen.fill(BACKGROUND)
            # 居中显示标题
            screen.blit(title, (screen.get_width()//2 - title.get_width()//2, screen.get_height()//2 - 50))
            screen.blit(subtitle, (screen.get_width()//2 - subtitle.get_width()//2, screen.get_height()//2 + 50))
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整
                    screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            pygame.display.flip()
            clock.tick(60)
    
    # === 回放文件选择界面 ===
    selected_file = None
    font_title = pygame.font.SysFont("simhei", data.UI_TITLE_FONT_SIZE)
    font_file = pygame.font.SysFont("simhei", data.UI_DEFAULT_FONT_SIZE)
    
    # 文件选择循环
    while not selected_file:
        screen.fill(BACKGROUND)
        
        # 绘制标题
        title = font_title.render("选择回放文件", True, INFO_COLOR)
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 100))
        
        # 绘制文件列表
        for i, filename in enumerate(replay_files):
            color = (200, 200, 255)
            # 显示文件名 (带序号)
            text = font_file.render(f"{i+1}. {os.path.basename(filename)}", True, color)
            screen.blit(text, (screen.get_width()//2 - text.get_width()//2, 200 + i*60))
        
        # 绘制提示
        hint = font_file.render("按ESC返回主菜单", True, (150, 200, 150))
        screen.blit(hint, (screen.get_width()//2 - hint.get_width()//2, screen.get_height() - 100))
        
        pygame.display.flip()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:  # 键盘选择
                if pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(replay_files):
                        selected_file = replay_files[index]
            elif event.type == pygame.MOUSEBUTTONDOWN:  # 鼠标选择
                x, y = event.pos
                for i in range(len(replay_files)):
                    text_y = 200 + i*60
                    if text_y <= y <= text_y + 40:
                        selected_file = replay_files[i]
                        break
    
    # 创建回放器和背景
    replayer = GameReplayer(selected_file, screen)
    background = create_background_grid(screen)
    
    # 检查是否有有效数据
    if not replayer.frames:
        print("错误: 没有有效的回放数据")
        pygame.quit()
        return
    
    # 设置窗口标题 (显示回放文件名)
    pygame.display.set_caption(f"游戏回放: {os.path.basename(selected_file)}")
    
    last_time = time.time()
    running = True
    
    # === 回放主循环 ===
    while running:
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 窗口关闭
                running = False
            elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                background = create_background_grid(screen)  # 重新创建背景
            elif event.type == pygame.KEYDOWN:  # 按键处理
                if event.key == pygame.K_ESCAPE:  # ESC退出
                    running = False
                elif event.key == pygame.K_SPACE:  # 空格键播放/暂停
                    if replayer.state == ReplayState.PAUSED:
                        replayer.state = ReplayState.PLAYING
                    else:
                        replayer.state = ReplayState.PAUSED
                elif event.key == pygame.K_RIGHT:  # 右箭头快进
                    replayer.state = ReplayState.FAST_FORWARD
                elif event.key == pygame.K_LEFT:  # 左箭头后退
                    replayer.state = ReplayState.REWIND
                elif event.key == pygame.K_UP:  # 上箭头增加速度
                    replayer.playback_speed = min(5.0, replayer.playback_speed + 0.5)
                elif event.key == pygame.K_DOWN:  # 下箭头减少速度
                    replayer.playback_speed = max(0.1, replayer.playback_speed - 0.5)
                elif event.key == pygame.K_j:  # J键跳转时间
                    try:
                        target_time = float(input("请输入跳转时间(秒): "))
                        replayer.current_time = max(0, min(target_time, replayer.total_time))
                    except:
                        print("无效的时间输入")
        
        # 更新回放状态
        replayer.update(delta_time)
        
        # 渲染
        screen.blit(background, (0, 0))  # 绘制背景
        replayer.player.draw(screen)      # 绘制玩家
        
        # 显示回放UI
        replayer.draw_ui(screen)          # 绘制控制UI
        replayer.draw_progress_bar(screen)  # 绘制进度条
        
        pygame.display.flip()
        clock.tick(60)  # 限制到60FPS
    
    pygame.quit()