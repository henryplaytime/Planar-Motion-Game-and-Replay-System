# -*- coding: utf-8 -*-
"""
游戏控制台系统
提供命令行界面用于执行游戏指令
"""

import pygame
import re
import time
import data
from enum import Enum

class ConsoleState(Enum):
    """控制台状态枚举"""
    CLOSED = 0     # 控制台关闭
    OPEN = 1       # 控制台打开
    EXECUTING = 2  # 命令执行中
    RESIZING = 3   # 控制台大小调整中

class Console:
    """
    游戏控制台类
    提供命令行界面用于执行游戏指令
    """
    
    def __init__(self, game_instance=None):
        """
        初始化控制台
        
        参数:
            game_instance: 游戏实例引用 (可选)
        """
        self.state = ConsoleState.CLOSED
        self.input_text = ""
        self.history = []
        self.history_index = -1
        self.output_lines = []
        self.cursor_visible = True
        self.cursor_timer = 0
        self.game = game_instance
        self.max_output_lines = 20
        self.commands = {}
        self.last_resize_time = 0
        self.scroll_offset = 0  # 滚动偏移量
        
        # 控制台尺寸设置（初始值，实际值将在渲染时根据屏幕确定）
        self.console_height = 250  # 初始高度
        self.min_height = 100      # 最小高度
        self.max_height = 500      # 最大高度
        
        # 滚动条设置
        self.scroll_bar_height = 0
        self.scroll_bar_y = 0
        self.scroll_bar_dragging = False
        self.scroll_bar_drag_offset = 0
        
        # 初始化UI元素
        self.overlay = None
        self.console_bg = None
        self.font = None
        
        # 注册内置命令
        self._register_default_commands()

    def _register_default_commands(self):
        """注册默认命令"""
        self.register_command("help", self._cmd_help, "显示帮助信息")
        self.register_command("clear", self._cmd_clear, "清除控制台输出")
        self.register_command("exit", self._cmd_exit, "关闭控制台")
        self.register_command("time", self._cmd_time, "显示当前游戏时间")
        self.register_command("fps", self._cmd_fps, "显示当前帧率")
        self.register_command("pos", self._cmd_pos, "显示玩家位置")
        self.register_command("speed", self._cmd_speed, "设置玩家速度")
        self.register_command("record", self._cmd_record, "开始/停止录制")
        self.register_command("show", self._cmd_show, "显示/隐藏检测面板")
        self.register_command("version", self._cmd_version, "显示游戏版本信息")
        self.register_command("debug", self._cmd_debug, "切换调试模式")
        # 保留give命令但移除肾上腺素相关实现
        self.register_command("give", self._cmd_give, "给予玩家物品（此功能已禁用）")

    def _cmd_give(self, args):
        """给予玩家物品（此功能已禁用）"""
        self.add_output("错误: 此功能已被禁用")

    def register_command(self, name, function, description=""):
        """
        注册控制台命令
        
        参数:
            name: 命令名称
            function: 命令处理函数
            description: 命令描述
        """
        self.commands[name.lower()] = {
            "function": function,
            "description": description
        }

    def toggle(self):
        """切换控制台状态"""
        if self.state == ConsoleState.CLOSED:
            self.state = ConsoleState.OPEN
            self.input_text = ""
            self.cursor_visible = True
            self.cursor_timer = time.time()
            self.add_output("=== 游戏控制台 ===")
            self.add_output(f"版本: {data.RECORD_VERSION} (新版录制格式)")
            self.add_output("输入 'help' 获取命令列表")
            self.scroll_offset = 0  # 重置滚动位置
        else:
            self.state = ConsoleState.CLOSED

    def add_output(self, text):
        """添加输出行"""
        if not text:
            return
            
        # 自动分割长文本
        max_length = 100
        if len(text) > max_length:
            parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            for part in parts:
                self.output_lines.append(part)
        else:
            self.output_lines.append(text)
        
        # 限制输出行数
        if len(self.output_lines) > self.max_output_lines:
            self.output_lines = self.output_lines[-self.max_output_lines:]
        
        # 自动滚动到最新内容
        self.scroll_offset = 0

    def handle_event(self, event):
        """
        处理所有事件（键盘和鼠标）
        
        参数:
            event: pygame事件对象
        返回:
            bool: 是否已处理该事件
        """
        if self.state != ConsoleState.OPEN:
            return False

        # 处理鼠标滚轮事件优先级最高
        if event.type == pygame.MOUSEWHEEL:
            return self._handle_mouse_wheel(event)
    
        # 然后是其他鼠标事件...
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event)
    
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_mouse_up(event)
    
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_mouse_motion(event)
    
        # 键盘事件
        elif event.type == pygame.KEYDOWN:
            return self._handle_key_event(event)
        
        return False

    def _handle_key_event(self, event):
        """处理键盘事件"""
        # 回车键执行命令
        if event.key == pygame.K_RETURN:
            self._execute_command()
            return True
        
        # 退格键删除字符
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return True
        
        # Tab键自动补全
        elif event.key == pygame.K_TAB:
            self._auto_complete()
            return True
        
        # 上下箭头浏览历史
        elif event.key == pygame.K_UP:
            self._navigate_history(-1)
            return True
        elif event.key == pygame.K_DOWN:
            self._navigate_history(1)
            return True
        
        # Esc键关闭控制台
        elif event.key == pygame.K_ESCAPE:
            self.toggle()
            return True
        
        # Ctrl+L 清屏
        elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._cmd_clear([])
            return True
        
        # 普通字符输入
        elif event.unicode and event.unicode.isprintable():
            self.input_text += event.unicode
            return True
        
        return False

    def _handle_mouse_down(self, event):
        """处理鼠标按下事件"""
        mouse_pos = pygame.mouse.get_pos()
        screen = self.game.screen if self.game else None
        
        if not screen:
            return False
        
        # 获取缩放后的尺寸
        scaled_10 = data.scale_value(10, screen, False)
        scaled_console_height = data.scale_value(self.console_height, screen, False)
        
        # 检查是否点击了滚动条
        if hasattr(self, 'scroll_bar_rect') and self.scroll_bar_rect.collidepoint(mouse_pos):
            self.scroll_bar_dragging = True
            self.scroll_bar_drag_offset = mouse_pos[1] - self.scroll_bar_y
            return True
        
        # 检查是否点击了调整大小的区域
        resize_rect = pygame.Rect(
            0, scaled_console_height - scaled_10, 
            screen.get_width(), scaled_10
        )
        if resize_rect.collidepoint(mouse_pos):
            self.state = ConsoleState.RESIZING
            self.drag_start_y = mouse_pos[1]
            self.drag_start_height = self.console_height
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
            return True
        
        return False

    def _handle_mouse_up(self, event):
        """处理鼠标释放事件"""
        if self.scroll_bar_dragging:
            self.scroll_bar_dragging = False
            return True
        
        if self.state == ConsoleState.RESIZING:
            self.state = ConsoleState.OPEN
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            return True
        
        return False

    def _handle_mouse_motion(self, event):
        """处理鼠标移动事件"""
        mouse_pos = pygame.mouse.get_pos()
        screen = self.game.screen if self.game else None
        
        if not screen:
            return False
            
        # 获取缩放后的尺寸
        scaled_10 = data.scale_value(10, screen, False)
        scaled_20 = data.scale_value(20, screen, False)
        scaled_60 = data.scale_value(60, screen, False)
        scaled_console_height = data.scale_value(self.console_height, screen, False)
        
        # 处理滚动条拖动
        if self.scroll_bar_dragging:
            # 计算新的滚动条位置
            scroll_area_height = scaled_console_height - scaled_60
            new_y = mouse_pos[1] - self.scroll_bar_drag_offset
            
            # 限制滚动条在有效范围内
            scroll_bar_min_y = scaled_10
            scroll_bar_max_y = scroll_bar_min_y + scroll_area_height - self.scroll_bar_height
            
            if new_y < scroll_bar_min_y:
                new_y = scroll_bar_min_y
            elif new_y > scroll_bar_max_y:
                new_y = scroll_bar_max_y
                
            # 计算新的滚动偏移
            scroll_percentage = (new_y - scroll_bar_min_y) / (scroll_area_height - self.scroll_bar_height)
            max_scroll = max(0, len(self.output_lines) - self.max_output_lines)
            self.scroll_offset = int(scroll_percentage * max_scroll)
            
            return True
        
        # 处理控制台高度调整
        if self.state == ConsoleState.RESIZING:
            delta_y = mouse_pos[1] - self.drag_start_y
        
            # 将像素变化转换为原始高度变化
            height_scale = screen.get_height() / data.BASE_HEIGHT
            height_delta = delta_y / height_scale
        
            new_height = self.drag_start_height + height_delta
        
        # 限制在最小和最大高度之间
            if new_height < self.min_height:
                new_height = self.min_height
            elif new_height > self.max_height:
                new_height = self.max_height
            
            self.console_height = int(new_height)
        
            # 更新最大显示行数
            self.max_output_lines = max(5, int((self.console_height - 60) / 20))
            
            return True
        
        # 检查鼠标是否在调整大小的区域
        resize_rect = pygame.Rect(
            0, scaled_console_height - scaled_10, 
            screen.get_width(), scaled_10
        )
        
        # 检查鼠标是否在滚动条上
        scroll_bar_hover = hasattr(self, 'scroll_bar_rect') and self.scroll_bar_rect.collidepoint(mouse_pos)
        
        # 更新鼠标光标
        if resize_rect.collidepoint(mouse_pos) or scroll_bar_hover:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        return False

    def _handle_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        # 更新滚动偏移
        self.scroll_offset += event.y
        
        # 限制滚动范围
        max_scroll = max(0, len(self.output_lines) - self.max_output_lines)
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        elif self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll
        
        return True

    def _navigate_history(self, direction):
        """浏览命令历史"""
        if not self.history:
            return
            
        if direction < 0:  # 上箭头
            if self.history_index == -1:
                self.history_index = len(self.history) - 1
            else:
                self.history_index = max(0, self.history_index - 1)
        else:  # 下箭头
            if self.history_index == -1:
                return
            elif self.history_index >= len(self.history) - 1:
                self.history_index = -1
                self.input_text = ""
                return
            else:
                self.history_index += 1
                
        self.input_text = self.history[self.history_index]

    def _auto_complete(self):
        """命令自动补全"""
        if not self.input_text:
            return
            
        # 分割输入获取当前词
        parts = re.split(r'\s+', self.input_text.strip())
        current_word = parts[-1].lower() if parts else ""
        
        # 查找匹配命令
        matches = [cmd for cmd in self.commands if cmd.startswith(current_word)]
        
        if not matches:
            return
            
        # 只有一个匹配则补全
        if len(matches) == 1:
            if len(parts) == 1:  # 第一个词
                self.input_text = matches[0] + " "
            else:  # 后续词
                self.input_text = " ".join(parts[:-1]) + " " + matches[0] + " "
        else:
            self.add_output("可能的命令:")
            for match in matches:
                self.add_output(f"  {match} - {self.commands[match]['description']}")

    def _execute_command(self):
        """执行当前命令"""
        cmd_text = self.input_text.strip()
        if not cmd_text:
            return
            
        # 记录历史
        self.history.append(cmd_text)
        self.history_index = -1
        
        # 显示输入
        self.add_output(f"> {cmd_text}")
        self.input_text = ""
        
        # 解析命令
        parts = re.split(r'\s+', cmd_text)
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 执行命令
        if cmd_name in self.commands:
            try:
                self.state = ConsoleState.EXECUTING
                self.commands[cmd_name]["function"](args)
            except Exception as e:
                self.add_output(f"错误: {str(e)}")
            finally:
                self.state = ConsoleState.OPEN
        else:
            self.add_output(f"未知命令: {cmd_name}")
            self.add_output("输入 'help' 查看可用命令")

    def update(self):
        """更新控制台状态"""
        if self.state != ConsoleState.OPEN:
            return
            
        # 光标闪烁
        current_time = time.time()
        if current_time - self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time

    def _create_surfaces(self, screen):
        """创建控制台所需的表面"""
        # 确保screen有效
        if screen is None:
            return
            
        try:
            # 半透明覆盖层
            self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self.overlay.fill((0, 0, 0, 128))
            
            # 控制台背景
            self.console_bg = pygame.Surface((screen.get_width(), data.scale_value(self.console_height, screen, False)))
            self.console_bg.fill((20, 20, 30))
            pygame.draw.rect(self.console_bg, (50, 70, 100), self.console_bg.get_rect(), 2)
            
            # 字体
            font_size = data.get_scaled_font(20, screen)
            self.font = data.get_font(font_size)
        except (AttributeError, pygame.error) as e:
            print(f"创建控制台表面时出错: {str(e)}")
            self.overlay = None
            self.console_bg = None
            self.font = None

    def render(self, screen):
        """渲染控制台"""
        if self.state == ConsoleState.CLOSED or screen is None:
            return
             
        try:
            # 确保表面已创建

            current_time = time.time()
            need_create = (
                self.overlay is None or 
                self.console_bg is None or 
                self.font is None or
                self.console_bg.get_height() != data.scale_value(self.console_height, screen, False) or
                current_time - self.last_surface_create_time > 0.5  # 限制创建频率
            )
        
            if need_create:
                self._create_surfaces(screen)
                self.last_surface_create_time = current_time
            if self.overlay is None or self.console_bg is None or self.font is None:
                self._create_surfaces(screen)
                # 如果创建后仍然无效，则放弃渲染
                if self.overlay is None or self.console_bg is None or self.font is None:
                    return
                self.last_resize_time = time.time()
            
            # 检查是否需要重新创建表面（窗口大小改变）
            if (self.overlay.get_size() != screen.get_size() or
                time.time() - self.last_resize_time > 1.0):
                
                self._create_surfaces(screen)
                self.last_resize_time = time.time()
            
            # 获取缩放后的尺寸
            scaled_5 = data.scale_value(5, screen, False)
            scaled_10 = data.scale_value(10, screen, False)
            scaled_15 = data.scale_value(15, screen, False)
            scaled_20 = data.scale_value(20, screen, False)
            scaled_40 = data.scale_value(40, screen, False)
            scaled_50 = data.scale_value(50, screen, False)
            scaled_60 = data.scale_value(60, screen, False)
            scaled_console_height = data.scale_value(self.console_height, screen, False)
            
            # 绘制覆盖层
            screen.blit(self.overlay, (0, 0))
            
            # 绘制控制台背景
            screen.blit(self.console_bg, (0, 0))
            
            # 计算输出区域高度
            output_area_height = scaled_console_height - scaled_60
            
            # 计算可显示的行数
            visible_lines = int(min(self.max_output_lines, output_area_height // scaled_20))
            
            # 计算滚动条参数
            total_lines = len(self.output_lines)
            if total_lines > visible_lines:
                # 滚动条高度与可见区域比例成比例
                self.scroll_bar_height = max(20, int((visible_lines / total_lines) * output_area_height))
                scroll_area_height = output_area_height - self.scroll_bar_height
                
                # 计算滚动条位置
                max_scroll = total_lines - visible_lines
                scroll_percentage = self.scroll_offset / max_scroll if max_scroll > 0 else 0
                self.scroll_bar_y = scaled_10 + int(scroll_percentage * scroll_area_height)
                
                # 绘制滚动条背景
                scroll_bar_x = screen.get_width() - scaled_15
                scroll_bar_width = scaled_10
                pygame.draw.rect(screen, (50, 50, 70), 
                                (scroll_bar_x, scaled_10, 
                                 scroll_bar_width, output_area_height))
                
                # 绘制滚动条
                self.scroll_bar_rect = pygame.Rect(
                    scroll_bar_x, self.scroll_bar_y, 
                    scroll_bar_width, self.scroll_bar_height
                )
                pygame.draw.rect(screen, (100, 150, 200), self.scroll_bar_rect)
            else:
                self.scroll_bar_height = 0
                self.scroll_offset = 0
            
            # 绘制输出文本
            y_pos = scaled_10

            # 确保所有索引都是整数
            start_index = max(0, len(self.output_lines) - visible_lines - self.scroll_offset)
            start_index = int(start_index)
            end_index = min(start_index + visible_lines, len(self.output_lines))
            end_index = int(end_index)

            for i in range(start_index, end_index):
                if i >= len(self.output_lines) or i < 0:
                    continue
                    
                line = self.output_lines[i]
                text_surface = self.font.render(line, True, (200, 220, 255))
                screen.blit(text_surface, (scaled_10, y_pos))
                y_pos += scaled_20
            
            # 绘制输入行
            input_y = scaled_console_height - scaled_50
            pygame.draw.line(screen, (100, 150, 200), 
                            (0, input_y), 
                            (screen.get_width(), input_y), 2)
            
            # 绘制输入文本和光标
            input_text = f"> {self.input_text}"
            if self.cursor_visible:
                input_text += "_"
                
            input_surface = self.font.render(input_text, True, (255, 255, 200))
            screen.blit(input_surface, (scaled_10, input_y + scaled_5))
            
            # 绘制调整大小的手柄
            resize_handle_y = scaled_console_height - scaled_5
            pygame.draw.rect(screen, (100, 150, 200), 
                            (0, resize_handle_y, screen.get_width(), scaled_5))
            pygame.draw.rect(screen, (70, 120, 180), 
                            (screen.get_width()//2 - scaled_40, resize_handle_y, 
                             scaled_40 * 2, scaled_5 // 2))
        
        except (AttributeError, pygame.error) as e:
            print(f"渲染控制台时出错: {str(e)}")
            # 出错时重置表面，下次渲染时会尝试重新创建
            self.overlay = None
            self.console_bg = None
            self.font = None
            
    # ===== 内置命令实现 =====
    def _cmd_help(self, args):
        """显示帮助信息"""
        self.add_output("可用命令:")
        for name, cmd in sorted(self.commands.items()):
            self.add_output(f"  {name:8} - {cmd['description']}")

    def _cmd_clear(self, args):
        """清除控制台输出"""
        self.output_lines = []
        self.scroll_offset = 0  # 清除后重置滚动位置

    def _cmd_exit(self, args):
        """关闭控制台"""
        self.toggle()

    def _cmd_time(self, args):
        """显示游戏时间"""
        if self.game:
            game_time = pygame.time.get_ticks() / 1000.0
            self.add_output(f"游戏运行时间: {game_time:.1f}秒")
        else:
            self.add_output("未连接到游戏实例")

    def _cmd_fps(self, args):
        """显示帧率信息"""
        if self.game and hasattr(self.game, 'clock'):
            fps = self.game.clock.get_fps()
            self.add_output(f"当前帧率: {fps:.1f} FPS")
        else:
            self.add_output("无法获取帧率信息")

    def _cmd_pos(self, args):
        """显示玩家位置"""
        if self.game and hasattr(self.game, 'player'):
            x, y = self.game.player.position
            self.add_output(f"玩家位置: X={x:.1f}, Y={y:.1f}")
        else:
            self.add_output("无法获取玩家位置")

    def _cmd_speed(self, args):
        """设置玩家速度"""
        if not self.game or not hasattr(self.game, 'player'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if not args:
            self.add_output(f"当前速度: 行走={data.WALK_SPEED}, 奔跑={data.SPRINT_SPEED}")
            return
            
        try:
            speed = float(args[0])
            if speed <= 0:
                raise ValueError("速度必须大于0")
                
            data.WALK_SPEED = speed
            data.SPRINT_SPEED = speed * 1.28
            self.add_output(f"设置成功: 行走速度={speed}, 奔跑速度={speed*1.28:.1f}")
        except ValueError as e:
            self.add_output(f"错误: {str(e)}")
            
    def _cmd_record(self, args):
        """开始/停止录制"""
        if not self.game or not hasattr(self.game, 'start_recording'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if self.game.recording:
            self.game.stop_recording()
            self.add_output("录制已停止")
        else:
            self.game.start_recording()
            self.add_output("录制已开始")
    
    def _cmd_show(self, args):
        """显示/隐藏检测面板"""
        if not self.game or not hasattr(self.game, 'show_detection'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        self.game.show_detection = not self.game.show_detection
        status = "显示" if self.game.show_detection else "隐藏"
        self.add_output(f"检测面板: {status}")
    
    def _cmd_version(self, args):
        """显示游戏版本信息"""
        self.add_output(f"游戏录制系统版本: {data.RECORD_VERSION}")
        self.add_output("录制格式: 高阶指令 + 原始输入 + 状态快照")
        self.add_output(f"录制帧率: {data.RECORD_FPS} FPS")
    
    def _cmd_debug(self, args):
        """切换调试模式"""
        if not self.game:
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if hasattr(self.game, 'debug_mode'):
            self.game.debug_mode = not self.game.debug_mode
            status = "开启" if self.game.debug_mode else "关闭"
            self.add_output(f"调试模式: {status}")
        else:
            self.add_output("此游戏实例不支持调试模式")