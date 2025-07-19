# -*- coding: utf-8 -*-
"""
主游戏模块
包含游戏主循环、UI渲染和录制功能
"""

import pygame
import sys
import data
import os
import time
from player import Player

class Game:
    """
    游戏主类
    管理游戏状态、输入处理和渲染
    """
    
    def __init__(self, screen):
        """
        初始化游戏
        
        参数:
            screen (pygame.Surface): 游戏窗口表面
        """
        self.screen = screen  # 游戏窗口表面
        self.player = Player()  # 玩家对象
        self.clock = pygame.time.Clock()  # 游戏时钟
        self.show_detection = False  # 是否显示键盘检测面板
        self.last_time = pygame.time.get_ticks() / 1000.0  # 上一帧时间 (秒)
        self.ground_y = data.SCREEN_HEIGHT - 100  # 地面y坐标
        
        # 初始化游戏元素
        self.create_background_grid()  # 创建背景网格
        self.create_ui_elements()  # 创建UI文本
        
        # === 录制相关属性 ===
        self.recording = False  # 是否正在录制
        self.record_file = None  # 录制文件对象
        self.record_start_time = 0  # 录制开始时间
        self.last_record_time = 0  # 上次记录时间
        self.record_interval = 1.0 / data.RECORD_FPS  # 记录间隔 (秒)
    
    def create_background_grid(self):
        """创建静态网格背景缓存"""
        self.background_grid = pygame.Surface((data.SCREEN_WIDTH, data.SCREEN_HEIGHT))
        self.background_grid.fill(data.BACKGROUND)  # 填充背景色
        
        # 绘制垂直线
        for x in range(0, data.SCREEN_WIDTH, 40):
            pygame.draw.line(self.background_grid, (50, 50, 70), 
                            (x, 0), (x, data.SCREEN_HEIGHT), 1)
        
        # 绘制水平线
        for y in range(0, data.SCREEN_HEIGHT, 40):
            pygame.draw.line(self.background_grid, (50, 50, 70), 
                            (0, y), (data.SCREEN_WIDTH, y), 1)
        
        # 绘制地面线
        pygame.draw.line(self.background_grid, (100, 150, 100), 
                        (0, self.ground_y), 
                        (data.SCREEN_WIDTH, self.ground_y), 3)
    
    def create_ui_elements(self):
        """预创建UI文本内容"""
        # 控制说明文本
        self.control_info_texts = [
            "WASD键: 移动玩家",
            "Shift键: 奔跑加速",
            "F1键: 显示/隐藏键盘状态",
            "F2键: 开启/关闭录制",
            "ESC键: 退出游戏"
        ]
        
        # 移动系统说明文本
        self.move_info_texts = [
            "移动系统: 平滑加速物理",
            "按下方向键加速",
            "松开方向键逐渐减速",
            "Shift键增加最大速度"
        ]
    
    def handle_events(self):
        """处理所有游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 窗口关闭事件
                self.stop_recording()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:  # 按键按下事件
                if event.key == pygame.K_ESCAPE:  # ESC键退出
                    self.stop_recording()
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_F1:  # F1切换面板显示
                    self.show_detection = not self.show_detection
                elif event.key == pygame.K_F2:  # F2开始/停止录制
                    if self.recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
            elif event.type == pygame.VIDEORESIZE:  # 窗口大小调整事件
                # 更新窗口大小
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
    
    def start_recording(self):
        """开始游戏录制"""
        if self.recording:
            return
        
        # 创建录制文件 (带时间戳)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"game_recording_{timestamp}.dem"
        self.record_file = open(filename, 'w')
        self.record_start_time = time.time()
        self.last_record_time = 0
        self.recording = True
        
        # 写入文件头信息
        self.record_file.write(f"SCREEN_WIDTH: {data.SCREEN_WIDTH}\n")
        self.record_file.write(f"SCREEN_HEIGHT: {data.SCREEN_HEIGHT}\n")
        self.record_file.write(f"RECORD_FPS: {data.RECORD_FPS}\n")  
        self.record_file.write(f"START_TIME: {self.record_start_time}\n")
        
        print(f"开始录制: {filename}")
    
    def stop_recording(self):
        """停止游戏录制"""
        if not self.recording:
            return
        
        if self.record_file:
            self.record_file.close()
            print("录制已停止")
        
        self.recording = False
        self.record_file = None
    
    def record_frame(self, player):
        """
        记录当前帧数据
        
        参数:
            player (Player): 玩家对象
        """
        if not self.recording or self.record_file is None:
                return
        
        current_time = time.time() - self.record_start_time
        
        # 检查是否需要记录 (基于RECORD_FPS)
        if current_time - self.last_record_time >= self.record_interval:
            # 写入帧数据: 时间,位置,速度,冲刺状态
            self.record_file.write(
                f"{current_time:.3f}," 
                f"{player.position[0]:.3f},{player.position[1]:.3f}," 
                f"{player.velocity[0]:.3f},{player.velocity[1]:.3f}," 
                f"{int(player.sprinting)}\n"
            )
            self.last_record_time = current_time
    
    def update(self):
        """
        更新游戏状态
        
        返回:
            tuple: (按下的按键, 时间差)
        """
        current_time = pygame.time.get_ticks() / 1000.0
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # 限制最大帧时间 (防止物理模拟不稳定)
        delta_time = min(delta_time, 0.033)
        
        # 获取当前按下的按键
        pressed_keys = pygame.key.get_pressed()
        # 更新玩家状态
        self.player.update(pressed_keys, delta_time)
        # 地面检测
        self.player.check_ground(self.ground_y)
        # 边界检测
        self.player.check_bounds()
        
        # 录制当前帧
        self.record_frame(self.player)
        
        return pressed_keys, delta_time
    
    def render(self, pressed_keys, delta_time):
        """
        渲染游戏画面
        
        参数:
            pressed_keys (dict): 按下的按键
            delta_time (float): 时间差
        """
        # 绘制背景
        self.screen.blit(self.background_grid, (0, 0))
        
        # 绘制玩家
        self.player.draw(self.screen)
        
        # 绘制玩家状态信息
        self.draw_player_status()
        
        # 录制状态指示器
        if self.recording:
            # 创建"录制中..."文本
            rec_text = data.get_font(data.get_scaled_font(24, self.screen)).render("录制中...", True, (255, 50, 50))
            # 计算位置 (右上角)
            rec_pos = data.scale_position(data.SCREEN_WIDTH - rec_text.get_width() - 20, 20, self.screen)
            self.screen.blit(rec_text, rec_pos)
        
        # 根据状态绘制不同面板
        if self.show_detection:
            self.draw_detection_panel(pressed_keys, delta_time)  # 键盘检测面板
        else:
            self.draw_control_info(pressed_keys)  # 控制说明面板
        
        pygame.display.flip()  # 更新显示
    
    def draw_player_status(self):
        """绘制玩家状态信息"""
        # 移动状态 (奔跑/行走)
        status = "奔跑中" if self.player.sprinting else "行走中"
        status_font = data.get_scaled_font(24, self.screen)
        status_text = data.get_font(status_font).render(status, True, 
                        (255, 200, 0) if self.player.sprinting else (200, 200, 255))
        
        # 为状态文本添加背景 (提高可读性)
        text_rect = status_text.get_rect(center=(int(self.player.position[0]), int(self.player.position[1] - 60)))
        bg_rect = text_rect.inflate(20, 10)  # 扩大矩形
        # 绘制半透明背景
        pygame.draw.rect(self.screen, (30, 30, 50, 180), bg_rect, border_radius=5)
        # 绘制边框
        pygame.draw.rect(self.screen, (100, 150, 200), bg_rect, 2, border_radius=5)
        # 绘制文本
        self.screen.blit(status_text, text_rect)
        
        # 速度信息
        speed = data.calculate_speed(self.player.velocity)
        speed_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"速度: {speed:.1f} 像素/秒", True, (180, 230, 255))
        # 计算位置 (左下角)
        speed_pos = data.scale_position(10, data.SCREEN_HEIGHT - 60, self.screen)
        self.screen.blit(speed_text, speed_pos)
        
        # 位置信息
        pos_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"位置: ({int(self.player.position[0])}, {int(self.player.position[1])})", 
            True, (180, 230, 255))
        # 计算位置 (左下角)
        pos_pos = data.scale_position(10, data.SCREEN_HEIGHT - 30, self.screen)
        self.screen.blit(pos_text, pos_pos)
        
        # 地面状态
        ground_status = "地面" if self.player.grounded else "空中"
        ground_text = data.get_font(data.get_scaled_font(20, self.screen)).render(
            f"状态: {ground_status}", True, 
            (150, 255, 150) if self.player.grounded else (255, 150, 150))
        # 计算位置 (左下角)
        ground_pos = data.scale_position(10, data.SCREEN_HEIGHT - 90, self.screen)
        self.screen.blit(ground_text, ground_pos)
    
    def draw_detection_panel(self, pressed_keys, delta_time):
        """
        绘制键盘状态检测面板
        
        参数:
            pressed_keys (dict): 按下的按键
            delta_time (float): 时间差
        """
        # 计算所需面板尺寸 (键位数量 + 额外信息行数)
        num_items = len(data.KEYS_TO_MONITOR) + 6
        panel_width = 450
        panel_height = data.UI_PADDING * 2 + num_items * data.UI_LINE_SPACING
        
        # 创建半透明面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 计算面板位置 (左上角)
        panel_pos = data.scale_position(20, 20, self.screen)
        self.screen.blit(panel, panel_pos)
        
        # 面板标题
        title_font = data.get_scaled_font(data.UI_TITLE_FONT_SIZE, self.screen)
        title = data.get_font(title_font).render("键盘状态检测", True, data.INFO_COLOR)
        title_pos = (panel_pos[0] + 20, panel_pos[1] + 10)
        self.screen.blit(title, title_pos)
        
        # 键位状态显示
        y_pos = title_pos[1] + 40
        default_font = data.get_scaled_font(data.UI_DEFAULT_FONT_SIZE, self.screen)
        
        for key, name in data.KEYS_TO_MONITOR.items():
            is_pressed = pressed_keys[key]
            status = "按下" if is_pressed else "未按下"
            # 按键按下时使用绿色，否则使用默认文本色
            color = data.KEY_PRESSED_COLOR if is_pressed else data.TEXT_COLOR
            text = data.get_font(default_font).render(f"{name}: {status}", True, color)
            self.screen.blit(text, (panel_pos[0] + 20, y_pos))
            y_pos += data.UI_LINE_SPACING
        
        # 录制状态显示
        rec_status = "开启" if self.recording else "关闭"
        rec_color = (255, 50, 50) if self.recording else (200, 200, 200)
        rec_text = data.get_font(default_font).render(f"录制状态: {rec_status}", True, rec_color)
        self.screen.blit(rec_text, (panel_pos[0] + 20, y_pos))
        y_pos += data.UI_LINE_SPACING * 1.5  # 增加额外间距
        
        # 物理信息显示
        info_texts = [
            f"当前速度: {data.calculate_speed(self.player.velocity):.1f} 像素/秒",
            f"加速度: {data.ACCELERATION} 像素/秒²",
            f"减速度: {data.DECELERATION} 像素/秒²",
            f"摩擦力: {data.FRICTION}",
            f"帧时间: {delta_time*1000:.1f} 毫秒"
        ]
        
        for text_str in info_texts:
            color = (200, 220, 255)
            text = data.get_font(default_font).render(text_str, True, color)
            self.screen.blit(text, (panel_pos[0] + 20, y_pos))
            y_pos += data.UI_LINE_SPACING
    
    def draw_control_info(self, pressed_keys):
        """
        绘制控制说明面板
        
        参数:
            pressed_keys (dict): 按下的按键
        """
        # 计算所需面板尺寸 (文本行数 + 状态行数)
        num_items = len(self.control_info_texts) + 3
        panel_width = 800
        panel_height = data.UI_PADDING * 2 + num_items * data.UI_LINE_SPACING
        
        # 创建半透明面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*data.PANEL_COLOR[:3], data.UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 计算面板位置 (居中)
        panel_pos = data.scale_position(
            (data.BASE_WIDTH - panel_width) // 2, 
            20, 
            self.screen
        )
        self.screen.blit(panel, panel_pos)
        
        # 主标题
        title_font = data.get_scaled_font(data.UI_TITLE_FONT_SIZE, self.screen)
        title = data.get_font(title_font).render("玩家控制演示 (平面移动游戏)", True, data.INFO_COLOR)
        title_pos = (
            panel_pos[0] + (panel_width - title.get_width()) // 2,
            panel_pos[1] + 10
        )
        self.screen.blit(title, title_pos)
        
        # 控制说明文本
        y_pos = title_pos[1] + 50
        default_font = data.get_scaled_font(data.UI_DEFAULT_FONT_SIZE, self.screen)
        
        for control in self.control_info_texts:
            text = data.get_font(default_font).render(control, True, (200, 220, 255))
            text_pos = (
                panel_pos[0] + (panel_width - text.get_width()) // 2,
                y_pos
            )
            self.screen.blit(text, text_pos)
            y_pos += data.UI_LINE_SPACING
        
        # F1键状态显示
        f1_status = "已按下" if pressed_keys[pygame.K_F1] else "未按下"
        f1_color = data.KEY_PRESSED_COLOR if pressed_keys[pygame.K_F1] else data.TEXT_COLOR
        f1_text = data.get_font(default_font).render(f"F1键状态: {f1_status}", True, f1_color)
        f1_pos = (
            panel_pos[0] + (panel_width - f1_text.get_width()) // 2,
            y_pos
        )
        self.screen.blit(f1_text, f1_pos)
        y_pos += data.UI_LINE_SPACING
        
        # F2键状态显示
        f2_status = "已按下" if pressed_keys[pygame.K_F2] else "未按下"
        f2_color = (255, 50, 50) if self.recording else data.TEXT_COLOR
        f2_text = data.get_font(default_font).render(f"F2键状态: {f2_status}", True, f2_color)
        f2_pos = (
            panel_pos[0] + (panel_width - f2_text.get_width()) // 2,
            y_pos
        )
        self.screen.blit(f2_text, f2_pos)
        y_pos += data.UI_LINE_SPACING
        
        # 录制状态显示
        rec_status = "开启" if self.recording else "关闭"
        rec_color = (255, 50, 50) if self.recording else (100, 200, 100)
        rec_font = data.get_scaled_font(data.UI_TITLE_FONT_SIZE - 8, self.screen)
        rec_text = data.get_font(rec_font).render(f"录制状态: {rec_status}", True, rec_color)
        rec_pos = (
            panel_pos[0] + (panel_width - rec_text.get_width()) // 2,
            y_pos
        )
        self.screen.blit(rec_text, rec_pos)
    
    def run(self):
        """运行游戏主循环"""
        while True:
            self.handle_events()  # 处理事件
            pressed_keys, delta_time = self.update()  # 更新状态
            self.render(pressed_keys, delta_time)  # 渲染画面
            self.clock.tick(60)  # 限制到60FPS