"""
游戏回放系统模块
实现游戏录制文件的加载、解析和回放功能
支持播放控制(暂停、快进、倒退)和可视化效果
"""

import pygame
import sys
import os
import glob
import time
import bisect  # 用于二分查找
import data
import random
import math
import traceback
from enum import Enum
from collections import namedtuple
from data import SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND, load_player_image, get_font, calculate_speed, PANEL_COLOR, TEXT_COLOR, INFO_COLOR, UI_PADDING, UI_LINE_SPACING, UI_PANEL_ALPHA, ADRENALINE_COLOR
from player import Player

class ReplayState(Enum):
    """
    回放状态枚举
    
    状态说明:
    PLAYING = 1       # 正常播放
    PAUSED = 2        # 暂停
    FAST_FORWARD = 3  # 快进
    REWIND = 4        # 倒退
    """
    PLAYING = 1
    PAUSED = 2
    FAST_FORWARD = 3
    REWIND = 4

# 定义快照数据结构
Snapshot = namedtuple('Snapshot', ['time', 'pos_x', 'pos_y', 'vel_x', 'vel_y', 'sprinting', 'adrenaline'])

class GameReplayer:
    """
    游戏回放器类
    
    功能概述:
    1. 加载和解析录制文件
    2. 管理回放状态和速度
    3. 应用输入和状态快照
    4. 渲染UI和特效
    5. 支持时间跳转
    
    属性说明:
    - filename: 回放文件名
    - screen: 游戏屏幕对象
    - commands: 高阶命令列表
    - inputs: 原始输入列表
    - snapshots: 状态快照列表
    - current_time: 当前回放时间
    - playback_speed: 回放速度倍数
    - state: 当前回放状态(ReplayState)
    - start_time: 录制开始时间
    - total_time: 回放总时长
    - last_update_time: 上次更新时间
    - player: 玩家对象(用于回放)
    - current_command_index: 当前处理到的命令索引
    - current_input_index: 当前处理到的输入索引
    - current_snapshot_index: 当前处理到的快照索引
    - last_frame_time: 上一帧时间
    - simulated_keys: 模拟按键状态
    - last_snapshot: 上一个快照
    - next_snapshot: 下一个快照
    - snapshot_blend: 快照混合比例
    - adrenaline_active: 肾上腺素状态
    - adrenaline_particles: 肾上腺素粒子特效
    """
    
    def __init__(self, filename, screen):
        """初始化回放器"""
        self.filename = filename  # 回放文件名
        self.screen = screen  # 游戏屏幕对象
        self.commands = []  # 高阶命令列表
        self.inputs = []  # 原始输入列表
        self.snapshots = []  # 状态快照列表
        self.current_time = 0.0  # 当前回放时间
        self.playback_speed = 1.0  # 回放速度倍数
        self.state = ReplayState.PLAYING  # 初始状态为播放
        self.start_time = 0  # 录制开始时间
        self.total_time = 0  # 回放总时长
        self.last_update_time = 0  # 上次更新时间
        self.player = Player()  # 玩家对象(用于回放)
        self.current_command_index = 0  # 当前命令索引
        self.current_input_index = 0  # 当前输入索引
        self.current_snapshot_index = 0  # 当前快照索引
        self.last_frame_time = 0  # 上一帧时间
        self.simulated_keys = {  # 模拟按键状态
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_LSHIFT: False,
            pygame.K_RSHIFT: False,
            pygame.K_q: False
        }
        self.last_snapshot = None  # 上一个快照
        self.next_snapshot = None  # 下一个快照
        self.snapshot_blend = 0.0  # 快照混合比例
        self.adrenaline_active = False  # 肾上腺素状态
        self.adrenaline_particles = []  # 肾上腺素粒子特效
        self.load_recording()  # 加载录制文件
    
    def load_recording(self):
        """
        加载和解析录制文件
        
        说明:
        1. 读取文件头信息(版本、分辨率等)
        2. 解析不同类型的数据行(命令、输入、快照)
        3. 根据版本号处理不同格式
        """
        try:
            record_version = 1  # 默认版本
            with open(self.filename, 'r') as f:
                for line in f:
                    # 处理文件头信息
                    if line.startswith("VERSION:"):
                        record_version = int(line.split(":")[1].strip())
                        continue
                    elif line.startswith("SCREEN_WIDTH:"):
                        continue
                    elif line.startswith("SCREEN_HEIGHT:"):
                        continue
                    elif line.startswith("START_TIME:"):
                        self.start_time = float(line.split(":")[1].strip())
                        continue
                    elif line.startswith("RECORD_FPS:"):
                        continue
                    elif "," in line:
                        # 根据版本处理不同格式
                        if record_version == 1:
                            parts = line.strip().split(",")
                            if len(parts) >= 6:
                                # 创建快照对象
                                snapshot = Snapshot(
                                    time=float(parts[0]),
                                    pos_x=float(parts[1]),
                                    pos_y=float(parts[2]),
                                    vel_x=float(parts[3]),
                                    vel_y=float(parts[4]),
                                    sprinting=bool(int(parts[5])),
                                    adrenaline=False  # 版本1不支持肾上腺素
                                )
                                self.snapshots.append(snapshot)
                        elif record_version >= 2:
                            # 分离前缀和数据
                            prefix, data_part = line.split(":", 1)
                            data_parts = data_part.strip().split(",")
                            timestamp = float(data_parts[0])
                            # 处理命令
                            if prefix == "C":
                                command = data_parts[1] if len(data_parts) > 1 else ""
                                self.commands.append((timestamp, command))
                            # 处理输入变化
                            elif prefix == "I":
                                changes = data_parts[1] if len(data_parts) > 1 else ""
                                self.inputs.append((timestamp, changes))
                            # 处理快照
                            elif prefix == "S":
                                if len(data_parts) >= 6:
                                    adrenaline_state = False
                                    # 版本2支持肾上腺素状态
                                    if len(data_parts) >= 7:
                                        try:
                                            adrenaline_state = bool(int(data_parts[6]))
                                        except:
                                            adrenaline_state = False
                                    # 创建快照对象
                                    snapshot = Snapshot(
                                        time=timestamp,
                                        pos_x=float(data_parts[1]),
                                        pos_y=float(data_parts[2]),
                                        vel_x=float(data_parts[3]),
                                        vel_y=float(data_parts[4]),
                                        sprinting=bool(int(data_parts[5])),
                                        adrenaline=adrenaline_state
                                    )
                                    self.snapshots.append(snapshot)
            # 计算总时长
            if self.snapshots:
                self.total_time = max(
                    self.snapshots[-1].time if self.snapshots else 0,
                    self.commands[-1][0] if self.commands else 0,
                    self.inputs[-1][0] if self.inputs else 0
                )
                print(f"已加载回放 (版本 {record_version}):")
                print(f"  高阶指令: {len(self.commands)}条")
                print(f"  原始输入: {len(self.inputs)}条")
                print(f"  状态快照: {len(self.snapshots)}个")
                print(f"  总时长: {self.total_time:.2f}秒")
                self.find_surrounding_snapshots(self.current_time)
            else:
                print("错误: 回放文件中没有有效数据")
        except Exception as e:
            print(f"加载回放文件失败: {str(e)}")
            traceback.print_exc()
            self.snapshots = []
            self.commands = []
            self.inputs = []
    
    def find_surrounding_snapshots(self, target_time):
        """
        查找目标时间前后的快照
        
        参数:
        - target_time: 目标时间
        
        返回:
        - (prev, next): 目标时间前后的快照元组
        """
        if not self.snapshots or len(self.snapshots) < 2:
            return None, None
        # 提取快照时间列表
        snapshot_times = [snapshot.time for snapshot in self.snapshots]
        # 使用二分查找定位目标时间
        idx = bisect.bisect_left(snapshot_times, target_time)
        if idx == 0:
            return self.snapshots[0], self.snapshots[1] if len(self.snapshots) > 1 else self.snapshots[0]
        elif idx >= len(self.snapshots):
            return self.snapshots[-2], self.snapshots[-1] if len(self.snapshots) > 1 else self.snapshots[-1]
        return self.snapshots[idx-1], self.snapshots[idx]
    
    def apply_command(self, command_str):
        """
        应用高阶命令
        
        参数:
        - command_str: 命令字符串
        """
        if not command_str: return
        commands = command_str.split(",")
        # 根据命令设置模拟按键状态
        self.simulated_keys[pygame.K_w] = 'W' in commands
        self.simulated_keys[pygame.K_s] = 'S' in commands
        self.simulated_keys[pygame.K_a] = 'A' in commands
        self.simulated_keys[pygame.K_d] = 'D' in commands
        self.simulated_keys[pygame.K_LSHIFT] = 'SHIFT' in commands
        self.simulated_keys[pygame.K_RSHIFT] = 'SHIFT' in commands
        # 更新玩家状态
        self.player.update(self.simulated_keys, 1.0 / data.RECORD_FPS)
    
    def apply_input_changes(self, input_str):
        """
        应用原始输入变化
        
        参数:
        - input_str: 输入变化字符串
        """
        if not input_str: return
        changes = input_str.split(";")
        for change in changes:
            if ":" in change:
                key, state = change.split(":")
                if key.upper() == "SHIFT":
                    # Shift键同时影响左右Shift
                    self.simulated_keys[pygame.K_LSHIFT] = bool(int(state))
                    self.simulated_keys[pygame.K_RSHIFT] = bool(int(state))
                else:
                    try:
                        key_lower = key.lower()
                        # 获取按键常量
                        key_code = getattr(pygame, f"K_{key_lower}")
                        self.simulated_keys[key_code] = bool(int(state))
                    except AttributeError:
                        print(f"警告: 未知按键 {key}")
    
    def apply_interpolated_snapshot(self):
        """
        应用插值快照
        
        说明:
        1. 根据前后快照和当前时间计算插值
        2. 更新玩家位置和状态
        3. 处理肾上腺素效果
        """
        if not self.last_snapshot or not self.next_snapshot: return
        prev = self.last_snapshot
        next = self.next_snapshot
        # 计算混合比例
        if prev.time > next.time:
            prev, next = next, prev
        total = next.time - prev.time
        if total > 0:
            blend = (self.current_time - prev.time) / total
        else:
            blend = 0.0
        
        # 插值计算位置和速度
        target_x = prev.pos_x + (next.pos_x - prev.pos_x) * blend
        target_y = prev.pos_y + (next.pos_y - prev.pos_y) * blend
        target_vel_x = prev.vel_x + (next.vel_x - prev.vel_x) * blend
        target_vel_y = prev.vel_y + (next.vel_y - prev.vel_y) * blend
        
        # 根据混合比例确定冲刺状态
        sprinting = prev.sprinting if blend < 0.5 else next.sprinting
        adrenaline = prev.adrenaline if blend < 0.5 else next.adrenaline
        
        # 处理肾上腺素激活
        if adrenaline and not self.adrenaline_active:
            self._activate_adrenaline_effect()
        self.adrenaline_active = adrenaline
        
        # 平滑更新玩家位置和速度
        self.player.position[0] += (target_x - self.player.position[0]) * 0.3
        self.player.position[1] += (target_y - self.player.position[1]) * 0.3
        self.player.velocity[0] += (target_vel_x - self.player.velocity[0]) * 0.5
        self.player.velocity[1] += (target_vel_y - self.player.velocity[1]) * 0.5
        self.player.sprinting = sprinting
        self.player.rect.center = (int(self.player.position[0]), int(self.player.position[1]))
    
    def update(self, delta_time):
        """
        更新回放状态
        
        参数:
        - delta_time: 距离上一帧的时间
        """
        if self.state == ReplayState.PAUSED: return  # 暂停状态不更新
        
        # 计算实际时间增量(考虑回放速度)
        actual_delta = delta_time * self.playback_speed
        current_frame_time = time.time()
        
        # 倒退状态卡顿检测
        if (self.state == ReplayState.REWIND and 
            abs(current_frame_time - self.last_frame_time) < 0.001 and
            self.current_time > 0):
            print("检测到卡住，重置索引")
            self.reset_indices()
            
        self.last_frame_time = current_frame_time
        
        # 根据状态更新当前时间
        if self.state == ReplayState.PLAYING:
            self.current_time += actual_delta
        elif self.state == ReplayState.FAST_FORWARD:
            self.current_time += actual_delta * 2.0
        elif self.state == ReplayState.REWIND:
            self.current_time -= actual_delta * 2.0
        
        # 限制时间范围
        self.current_time = max(0, min(self.current_time, self.total_time))
        
        # 查找当前时间前后的快照
        self.last_snapshot, self.next_snapshot = self.find_surrounding_snapshots(self.current_time)
        
        # 倒退状态的特殊处理
        if self.state == ReplayState.REWIND:
            # 重置命令索引
            self.current_command_index = 0
            for i, (timestamp, _) in enumerate(self.commands):
                if timestamp <= self.current_time:
                    self.current_command_index = i
                else:
                    break
                    
            # 重置输入索引
            self.current_input_index = 0
            for i, (timestamp, _) in enumerate(self.inputs):
                if timestamp <= self.current_time:
                    self.current_input_index = i
                else:
                    break
        
        # 处理当前时间之前的命令
        while (self.current_command_index < len(self.commands) and 
               self.commands[self.current_command_index][0] <= self.current_time):
            _, command = self.commands[self.current_command_index]
            self.apply_command(command)
            self.current_command_index += 1
            
        # 处理当前时间之前的输入变化
        while (self.current_input_index < len(self.inputs) and 
               self.inputs[self.current_input_index][0] <= self.current_time):
            _, input_changes = self.inputs[self.current_input_index]
            self.apply_input_changes(input_changes)
            self.current_input_index += 1
        
        # 应用快照插值
        if self.last_snapshot and self.next_snapshot:
            self.apply_interpolated_snapshot()
            
        # 更新肾上腺素粒子
        self._update_adrenaline_particles(delta_time)
    
    def draw_ui(self, screen):
        """
        渲染回放UI界面
        
        参数:
        - screen: 游戏屏幕对象
        """
        # 获取字体
        default_font_size = data.get_scaled_font(data.REPLAY_DEFAULT_FONT_SIZE, screen)
        title_font_size = data.get_scaled_font(data.REPLAY_TITLE_FONT_SIZE, screen)
        font = data.get_font(default_font_size)
        title_font = data.get_font(title_font_size)
        
        # 控制说明
        controls = [
            "空格键: 播放/暂停",
            "→: 快进",
            "←: 后退",
            "↑: 增加速度",
            "↓: 减少速度",
            "J: 跳转到指定时间",
            "ESC: 退出回放"
        ]
        
        # 计算面板尺寸
        max_width = 0
        for text in controls:
            text_width = font.size(text)[0]
            if text_width > max_width:
                max_width = text_width
                
        # 时间文本
        time_text = f"时间: {self.current_time:.1f}/{self.total_time:.1f}秒"
        time_width = font.size(time_text)[0]
        
        # 状态文本
        state_text = f"状态: {self.state.name} | 速度: x{self.playback_speed:.1f}"
        if self.adrenaline_active:
            state_text += " | 肾上腺素激活"
        state_width = font.size(state_text)[0]
        
        max_width = max(max_width, time_width, state_width)
        panel_width = max_width + 2 * UI_PADDING
        panel_height = UI_PADDING * 2 + (len(controls) + 3) * UI_LINE_SPACING
        
        # 创建面板
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*PANEL_COLOR[:3], UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        
        # 定位面板
        panel_pos = data.scale_position(
            data.BASE_WIDTH - panel_width - 20, 
            20, 
            screen
        )
        screen.blit(panel, panel_pos)
        
        # 渲染标题
        title = title_font.render("游戏回放系统", True, INFO_COLOR)
        screen.blit(title, (panel_pos[0] + (panel_width - title.get_width()) // 2, panel_pos[1] + 10))
        
        # 渲染时间信息
        time_text = font.render(time_text, True, TEXT_COLOR)
        screen.blit(time_text, (panel_pos[0] + (panel_width - time_text.get_width()) // 2, panel_pos[1] + 50))
        
        # 渲染状态信息
        state_text = font.render(state_text, True, TEXT_COLOR)
        screen.blit(state_text, (panel_pos[0] + (panel_width - state_text.get_width()) // 2, panel_pos[1] + 80))
        
        # 渲染控制说明
        y_pos = panel_pos[1] + 120
        for text in controls:
            ctrl_text = font.render(text, True, TEXT_COLOR)
            screen.blit(ctrl_text, (panel_pos[0] + UI_PADDING, y_pos))
            y_pos += UI_LINE_SPACING
    
    def draw_progress_bar(self, screen):
        """
        渲染进度条
        
        参数:
        - screen: 游戏屏幕对象
        """
        if self.total_time <= 0: return
        
        # 获取字体
        info_font_size = data.get_scaled_font(data.REPLAY_INFO_FONT_SIZE, screen)
        font = data.get_font(info_font_size)
        
        # 计算进度条尺寸
        bar_width = data.scale_value(600, screen)
        bar_height = data.scale_value(20, screen, False)
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = screen.get_height() - data.scale_value(50, screen, False)
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        
        # 绘制背景
        pygame.draw.rect(screen, (60, 60, 80), bar_rect)
        pygame.draw.rect(screen, (100, 100, 120), bar_rect, 2)
        
        # 计算填充宽度
        progress = self.current_time / self.total_time
        fill_width = int(bar_width * progress)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, (80, 180, 250), fill_rect)
        
        # 绘制标记
        marker_pos = bar_x + fill_width
        pygame.draw.line(screen, (255, 255, 255), 
                        (marker_pos, bar_y - 5), 
                        (marker_pos, bar_y + bar_height + 5), 3)
        
        # 渲染时间文本
        time_text = font.render(
            f"{self.current_time:.1f}s / {self.total_time:.1f}s", 
            True, TEXT_COLOR
        )
        time_pos = (
            (screen.get_width() - time_text.get_width()) // 2,
            bar_y - UI_LINE_SPACING
        )
        screen.blit(time_text, time_pos)

    def draw_effects(self, screen):
        """
        渲染特效(肾上腺素粒子)
        
        参数:
        - screen: 游戏屏幕对象
        """
        # 渲染粒子
        for particle in self.adrenaline_particles:
            # 计算透明度(基于生命周期)
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*ADRENALINE_COLOR[:3], alpha)
            # 绘制粒子
            pygame.draw.circle(
                screen, 
                color, 
                (int(particle['pos'][0]), int(particle['pos'][1])),
                int(particle['size'] * (particle['life'] / particle['max_life']))
            )
        
        # 如果肾上腺素激活，绘制脉冲效果
        if self.adrenaline_active:
            pulse = abs(math.sin(pygame.time.get_ticks() / 200.0))
            radius = 50 + 10 * pulse
            pygame.draw.circle(
                screen, 
                ADRENALINE_COLOR, 
                (int(self.player.position[0]), int(self.player.position[1])),
                int(radius), 
                3
            )

    def reset_indices(self):
        """
        重置所有索引(用于解决倒退状态卡顿问题)
        """
        # 重置命令索引
        self.current_command_index = 0
        for i, (timestamp, _) in enumerate(self.commands):
            if timestamp <= self.current_time:
                self.current_command_index = i
        
        # 重置输入索引
        self.current_input_index = 0
        for i, (timestamp, _) in enumerate(self.inputs):
            if timestamp <= self.current_time:
                self.current_input_index = i
        
        # 重置快照索引
        self.current_snapshot_index = 0
        for i, snapshot in enumerate(self.snapshots):
            if snapshot.time <= self.current_time:
                self.current_snapshot_index = i

    def _activate_adrenaline_effect(self):
        """激活肾上腺素特效(创建粒子)"""
        self.adrenaline_particles = []
        for _ in range(20):
            self._create_adrenaline_particle()

    def _create_adrenaline_particle(self):
        """创建单个肾上腺素粒子"""
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 200)
        size = random.uniform(3, 10)
        self.adrenaline_particles.append({
            'pos': list(self.player.position),  # 初始位置为玩家位置
            'vel': [math.cos(angle) * speed, math.sin(angle) * speed],  # 速度向量
            'size': size,  # 粒子大小
            'life': 1.0,  # 当前生命周期
            'max_life': random.uniform(0.3, 0.8)  # 最大生命周期
        })

    def _update_adrenaline_particles(self, delta_time):
        """更新肾上腺素粒子状态"""
        for particle in self.adrenaline_particles[:]:
            # 减少生命周期
            particle['life'] -= delta_time
            if particle['life'] <= 0:
                self.adrenaline_particles.remove(particle)
                continue
            # 更新位置
            particle['pos'][0] += particle['vel'][0] * delta_time
            particle['pos'][1] += particle['vel'][1] * delta_time
            # 减慢速度(模拟阻力)
            particle['vel'][0] *= 0.9
            particle['vel'][1] *= 0.9

def create_background_grid(screen):
    """
    创建背景网格
    
    参数:
    - screen: 游戏屏幕对象
    
    返回:
    - pygame.Surface: 背景网格表面
    """
    # 计算地面位置
    ground_y = screen.get_height() - data.scale_value(100, screen, False)
    background_grid = pygame.Surface(screen.get_size())
    background_grid.fill(BACKGROUND)
    
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

def run_replay_mode(screen):
    """
    运行回放模式
    
    参数:
    - screen: 游戏屏幕对象
    """
    pygame.display.set_caption("游戏回放模式")
    clock = pygame.time.Clock()
    
    # 查找所有回放文件
    replay_files = glob.glob("*.dem")
    
    # 如果没有回放文件，显示提示信息
    if not replay_files:
        no_replay_message(screen)
        return
    
    # 添加文件选择界面
    selected_index = select_replay_file(screen, replay_files)
    if selected_index is None:  # 用户取消选择
        return
    
    # 选择用户指定的回放文件
    replay_file = replay_files[selected_index]
    replayer = GameReplayer(replay_file, screen)
    
    # 创建背景网格
    background_grid = create_background_grid(screen)
    
    # 回放主循环
    running_replay = True
    while running_replay:
        # 处理事件
        running_replay = handle_replay_events(replayer)
        
        # 更新回放器
        delta_time = clock.tick(60) / 1000.0  # 转换为秒
        replayer.update(delta_time)
        
        # 渲染回放场景
        render_replay_scene(screen, background_grid, replayer)
        
        pygame.display.flip()

def select_replay_file(screen, replay_files):
    """
    显示回放文件选择界面
    
    参数:
    - screen: 游戏屏幕对象
    - replay_files: 回放文件列表
    
    返回:
    - int: 选择的文件索引，或 None(用户取消)
    """
    clock = pygame.time.Clock()
    selected_index = 0
    running = True
    
    # 获取字体
    title_font_size = data.get_scaled_font(36, screen)
    item_font_size = data.get_scaled_font(24, screen)
    title_font = data.get_font(title_font_size)
    item_font = data.get_font(item_font_size)
    
    # 计算面板尺寸
    max_width = 0
    for file in replay_files:
        text_width = item_font.size(file)[0]
        if text_width > max_width:
            max_width = text_width
    
    panel_width = max_width + 100
    panel_height = 100 + len(replay_files) * 40
    panel_x = (screen.get_width() - panel_width) // 2
    panel_y = (screen.get_height() - panel_height) // 2
    
    # 主循环
    while running:
        screen.fill(BACKGROUND)
        
        # 绘制面板背景
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((*PANEL_COLOR[:3], UI_PANEL_ALPHA))
        pygame.draw.rect(panel, (100, 150, 200), panel.get_rect(), 2)
        screen.blit(panel, (panel_x, panel_y))
        
        # 绘制标题
        title = title_font.render("选择回放文件", True, TEXT_COLOR)
        title_pos = (panel_x + (panel_width - title.get_width()) // 2, panel_y + 20)
        screen.blit(title, title_pos)
        
        # 绘制文件列表
        y_pos = panel_y + 70
        for i, file in enumerate(replay_files):
            color = (255, 255, 255) if i == selected_index else (180, 180, 180)
            file_text = item_font.render(file, True, color)
            screen.blit(file_text, (panel_x + 30, y_pos))
            y_pos += 40
        
        # 绘制说明
        help_font = data.get_font(data.get_scaled_font(18, screen))
        help_text = help_font.render("↑/↓: 选择文件  ENTER: 确认  ESC: 取消", True, TEXT_COLOR)
        help_pos = (panel_x + (panel_width - help_text.get_width()) // 2, panel_y + panel_height - 30)
        screen.blit(help_text, help_pos)
        
        pygame.display.flip()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None  # 用户取消
                elif event.key == pygame.K_RETURN:
                    return selected_index  # 确认选择
                elif event.key == pygame.K_UP:
                    selected_index = max(0, selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    selected_index = min(len(replay_files) - 1, selected_index + 1)
        
        clock.tick(60)
    
    return selected_index

def no_replay_message(screen):
    """
    显示无回放文件提示
    
    参数:
    - screen: 游戏屏幕对象
    """
    clock = pygame.time.Clock()
    running = True
    
    # 创建字体
    font = pygame.font.SysFont("simhei", 36)
    text = font.render("没有找到回放文件！按ESC返回主菜单", True, (255, 0, 0))
    text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    
    while running:
        screen.fill(BACKGROUND)
        screen.blit(text, text_rect)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

def handle_replay_events(replayer):
    """
    处理回放事件
    
    参数:
    - replayer: 回放器对象
    
    返回:
    - bool: 是否继续回放
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            return False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False  # 退出回放模式
            # 播放控制
            elif event.key == pygame.K_SPACE:
                # 暂停/播放
                if replayer.state == ReplayState.PAUSED:
                    replayer.state = ReplayState.PLAYING
                else:
                    replayer.state = ReplayState.PAUSED
            elif event.key == pygame.K_RIGHT:
                # 快进
                replayer.state = ReplayState.FAST_FORWARD
            elif event.key == pygame.K_LEFT:
                # 倒退
                replayer.state = ReplayState.REWIND
            elif event.key == pygame.K_UP:
                # 增加速度
                replayer.playback_speed = min(4.0, replayer.playback_speed + 0.5)
            elif event.key == pygame.K_DOWN:
                # 减少速度
                replayer.playback_speed = max(0.5, replayer.playback_speed - 0.5)
            elif event.key == pygame.K_j:
                # 跳转到指定时间（示例：跳转到中间）
                replayer.current_time = replayer.total_time / 2
                replayer.reset_indices()  # 重置索引
    return True

def render_replay_scene(screen, background_grid, replayer):
    """
    渲染回放场景
    
    参数:
    - screen: 游戏屏幕对象
    - background_grid: 背景网格表面
    - replayer: 回放器对象
    """
    # 绘制背景网格
    screen.blit(background_grid, (0, 0))
    
    # 绘制玩家
    pygame.draw.rect(screen, (0, 255, 0), replayer.player.rect)
    
    # 绘制特效
    replayer.draw_effects(screen)
    
    # 绘制UI
    replayer.draw_ui(screen)
    replayer.draw_progress_bar(screen)