"""
控制台系统模块
提供游戏内控制台功能，支持命令输入、历史记录、自动补全和执行
包含三个核心类：ConsoleState, ConsoleCore, ConsoleUI, Console
"""

import pygame
import re
import time
import data
from enum import Enum
from data import scale_value, get_scaled_font, get_font

class ConsoleState(Enum):
    """
    控制台状态枚举类
    
    状态说明:
    CLOSED = 0   # 控制台关闭状态
    OPEN = 1     # 控制台打开状态
    EXECUTING = 2  # 命令执行中状态
    """
    CLOSED = 0
    OPEN = 1
    EXECUTING = 2

class ConsoleCore:
    """
    控制台核心逻辑类
    
    功能概述:
    1. 管理命令注册和执行
    2. 处理输入历史和自动补全
    3. 管理控制台输出内容
    
    属性说明:
    - input_text: 当前输入的命令文本
    - history: 历史命令记录列表
    - history_index: 当前浏览的历史命令索引(-1表示不在历史记录中)
    - output_lines: 控制台输出行列表
    - max_output_lines: 控制台最大显示行数
    - commands: 注册的命令字典 {命令名: {function: 执行函数, description: 描述}}
    """
    def __init__(self):
        self.input_text = ""  # 当前输入的命令文本
        self.history = []  # 历史命令记录列表
        self.history_index = -1  # 当前浏览的历史命令索引(-1表示不在历史记录中)
        self.output_lines = []  # 控制台输出行列表
        self.max_output_lines = 20  # 控制台最大显示行数
        self.commands = {}  # 注册的命令字典 {命令名: {function: 执行函数, description: 描述}}
        self._register_default_commands()  # 注册默认命令
    
    def _register_default_commands(self):
        """注册默认命令到命令系统"""
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
        self.register_command("give", self._cmd_give, "给予玩家物品（此功能已禁用）")
    
    def register_command(self, name, function, description=""):
        """
        注册新命令
        
        参数:
        - name: 命令名称(不区分大小写)
        - function: 命令执行函数(接收args和game两个参数)
        - description: 命令描述文本(可选)
        """
        self.commands[name.lower()] = {"function": function, "description": description}
    
    def add_output(self, text):
        """
        添加输出到控制台
        
        功能:
        1. 自动分割过长的文本行
        2. 限制最大显示行数
        
        参数:
        - text: 要添加的输出文本
        """
        if not text: return
        max_length = 100  # 单行最大长度
        if len(text) > max_length:
            # 分割长文本为多行
            parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            for part in parts:
                self.output_lines.append(part)
        else:
            self.output_lines.append(text)
        
        # 限制行数不超过最大值
        if len(self.output_lines) > self.max_output_lines:
            self.output_lines = self.output_lines[-self.max_output_lines:]
    
    def _navigate_history(self, direction):
        """
        浏览历史命令
        
        参数:
        - direction: 浏览方向(-1: 上一条, 1: 下一条)
        """
        if not self.history: return
        if direction < 0:
            if self.history_index == -1:
                self.history_index = len(self.history) - 1
            else:
                self.history_index = max(0, self.history_index - 1)
        else:
            if self.history_index == -1: return
            elif self.history_index >= len(self.history) - 1:
                self.history_index = -1
                self.input_text = ""
                return
            else:
                self.history_index += 1
        self.input_text = self.history[self.history_index]
    
    def _auto_complete(self):
        """执行命令自动补全功能"""
        if not self.input_text: return
        parts = re.split(r'\s+', self.input_text.strip())
        current_word = parts[-1].lower() if parts else ""
        matches = [cmd for cmd in self.commands if cmd.startswith(current_word)]
        if not matches: return
        if len(matches) == 1:
            if len(parts) == 1:
                self.input_text = matches[0] + " "
            else:
                self.input_text = " ".join(parts[:-1]) + " " + matches[0] + " "
        else:
            self.add_output("可能的命令:")
            for match in matches:
                self.add_output(f"  {match} - {self.commands[match]['description']}")
    
    def _execute_command(self, game=None):
        """
        执行当前输入的命令
        
        参数:
        - game: 游戏实例(可选)
        """
        cmd_text = self.input_text.strip()
        if not cmd_text: return
        self.history.append(cmd_text)  # 添加到历史记录
        self.history_index = -1  # 重置历史索引
        self.add_output(f"> {cmd_text}")  # 回显命令
        self.input_text = ""  # 清空输入
        
        # 解析命令参数
        parts = re.split(r'\s+', cmd_text)
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 执行命令
        if cmd_name in self.commands:
            try:
                self.commands[cmd_name]["function"](args, game)
            except Exception as e:
                self.add_output(f"错误: {str(e)}")
        else:
            self.add_output(f"未知命令: {cmd_name}")
            self.add_output("输入 'help' 查看可用命令")
    
    # ================= 命令函数实现 =================
    
    def _cmd_help(self, args, game=None):
        """显示帮助信息命令"""
        self.add_output("可用命令:")
        for name, cmd in sorted(self.commands.items()):
            self.add_output(f"  {name:8} - {cmd['description']}")
    
    def _cmd_clear(self, args, game=None):
        """清除控制台输出命令"""
        self.output_lines = []
    
    def _cmd_exit(self, args, game=None):
        """关闭控制台命令"""
        pass  # 实际关闭逻辑在Console类中
    
    def _cmd_time(self, args, game=None):
        """显示当前游戏时间命令"""
        if game:
            game_time = pygame.time.get_ticks() / 1000.0
            self.add_output(f"游戏运行时间: {game_time:.1f}秒")
        else:
            self.add_output("未连接到游戏实例")
    
    def _cmd_fps(self, args, game=None):
        """显示当前帧率命令"""
        if game and hasattr(game, 'clock'):
            fps = game.clock.get_fps()
            self.add_output(f"当前帧率: {fps:.1f} FPS")
        else:
            self.add_output("无法获取帧率信息")
    
    def _cmd_pos(self, args, game=None):
        """显示玩家位置命令"""
        if game and hasattr(game, 'player'):
            x, y = game.player.position
            self.add_output(f"玩家位置: X={x:.1f}, Y={y:.1f}")
        else:
            self.add_output("无法获取玩家位置")
    
    def _cmd_speed(self, args, game=None):
        """设置玩家速度命令"""
        if not game or not hasattr(game, 'player'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if not args:
            # 显示当前速度
            self.add_output(f"当前速度: 行走={data.WALK_SPEED}, 奔跑={data.SPRINT_SPEED}")
            return
            
        try:
            speed = float(args[0])
            if speed <= 0:
                raise ValueError("速度必须大于0")
                
            # 更新速度参数
            data.WALK_SPEED = speed
            data.SPRINT_SPEED = speed * 1.28
            self.add_output(f"设置成功: 行走速度={speed}, 奔跑速度={speed*1.28:.1f}")
        except ValueError as e:
            self.add_output(f"错误: {str(e)}")
            
    def _cmd_record(self, args, game=None):
        """开始/停止录制命令"""
        if not game or not hasattr(game, 'start_recording'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if game.recording:
            game.stop_recording()
            self.add_output("录制已停止")
        else:
            game.start_recording()
            self.add_output("录制已开始")
    
    def _cmd_show(self, args, game=None):
        """显示/隐藏检测面板命令"""
        if not game or not hasattr(game, 'show_detection'):
            self.add_output("错误: 未连接到游戏实例")
            return
            
        game.show_detection = not game.show_detection
        status = "显示" if game.show_detection else "隐藏"
        self.add_output(f"检测面板: {status}")
    
    def _cmd_version(self, args, game=None):
        """显示游戏版本信息命令"""
        self.add_output(f"游戏录制系统版本: {data.RECORD_VERSION}")
        self.add_output("录制格式: 高阶指令 + 原始输入 + 状态快照")
        self.add_output(f"录制帧率: {data.RECORD_FPS} FPS")
    
    def _cmd_debug(self, args, game=None):
        """切换调试模式命令"""
        if not game:
            self.add_output("错误: 未连接到游戏实例")
            return
            
        if hasattr(game, 'debug_mode'):
            game.debug_mode = not game.debug_mode
            status = "开启" if game.debug_mode else "关闭"
            self.add_output(f"调试模式: {status}")
        else:
            self.add_output("此游戏实例不支持调试模式")
    
    def _cmd_give(self, args, game=None):
        """给予玩家物品命令(已禁用)"""
        self.add_output("错误: 此功能已被禁用")

class ConsoleUI:
    """
    控制台UI渲染类
    
    功能概述:
    1. 渲染控制台界面元素
    2. 管理滚动条和光标
    3. 处理屏幕适配
    
    属性说明:
    - console_height: 控制台默认高度(像素)
    - scroll_offset: 当前滚动偏移量(行)
    - scroll_bar_height: 滚动条高度
    - scroll_bar_y: 滚动条Y位置
    - scroll_bar_dragging: 是否正在拖动滚动条
    - scroll_bar_drag_offset: 拖动偏移量
    - cursor_visible: 光标可见状态
    - cursor_timer: 光标闪烁计时器
    - overlay: 半透明覆盖层表面
    - console_bg: 控制台背景表面
    - font: 控制台字体
    - last_surface_create_time: 上次创建表面的时间
    - scroll_bar_rect: 滚动条矩形区域
    """
    def __init__(self):
        self.console_height = 250  # 控制台默认高度
        self.scroll_offset = 0  # 当前滚动偏移量
        self.scroll_bar_height = 0  # 滚动条高度
        self.scroll_bar_y = 0  # 滚动条Y位置
        self.scroll_bar_dragging = False  # 是否正在拖动滚动条
        self.scroll_bar_drag_offset = 0  # 拖动偏移量
        self.cursor_visible = True  # 光标可见状态
        self.cursor_timer = 0.0  # 光标闪烁计时器
        self.overlay = None  # 半透明覆盖层表面
        self.console_bg = None  # 控制台背景表面
        self.font = None  # 控制台字体
        self.last_surface_create_time = 0  # 上次创建表面的时间
        self.scroll_bar_rect = None  # 滚动条矩形区域
    
    def create_surfaces(self, screen):
        """
        创建控制台所需的表面
        
        参数:
        - screen: 游戏主屏幕表面
        """
        if screen is None: return
        try:
            # 创建半透明覆盖层
            self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self.overlay.fill((0, 0, 0, 128))
            
            # 创建控制台背景
            self.console_bg = pygame.Surface(
                (screen.get_width(), scale_value(self.console_height, screen, False)))
            self.console_bg.fill((20, 20, 30))
            pygame.draw.rect(self.console_bg, (50, 70, 100), self.console_bg.get_rect(), 2)
            
            # 创建字体
            font_size = get_scaled_font(20, screen)
            self.font = get_font(font_size)

        except Exception as e:
            print(f"创建控制台表面时出错: {str(e)}")
            self.overlay = None
            self.console_bg = None
            self.font = None
    
    def render(self, screen, core, state, input_text):
        """
        渲染控制台UI
        
        参数:
        - screen: 游戏主屏幕表面
        - core: ConsoleCore实例
        - state: 控制台状态(ConsoleState)
        - input_text: 当前输入文本
        """
        if state == ConsoleState.CLOSED or screen is None: return
        
        # 定期检查是否需要重新创建表面
        current_time = time.time()
        if (self.overlay is None or self.console_bg is None or self.font is None or
            current_time - self.last_surface_create_time > 1.0):
            self.create_surfaces(screen)
            self.last_surface_create_time = current_time
        
        if self.overlay is None or self.console_bg is None or self.font is None: return
        
        # 计算缩放值
        scaled_5 = scale_value(5, screen, False)
        scaled_10 = scale_value(10, screen, False)
        scaled_15 = scale_value(15, screen, False)
        scaled_20 = scale_value(20, screen, False)
        scaled_40 = scale_value(40, screen, False)
        scaled_50 = scale_value(50, screen, False)
        scaled_60 = scale_value(60, screen, False)
        scaled_console_height = scale_value(self.console_height, screen, False)
        
        # 渲染控制台背景
        screen.blit(self.overlay, (0, 0))
        screen.blit(self.console_bg, (0, 0))
        
        # 渲染输出区域
        output_area_height = scaled_console_height - scaled_60
        visible_lines = min(core.max_output_lines, int(output_area_height // scaled_20))
        total_lines = len(core.output_lines)
        max_scroll = max(0, total_lines - visible_lines)
        if self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll
        
        y_pos = scaled_10
        start_index = self.scroll_offset
        end_index = min(start_index + visible_lines, total_lines)
        
        # 渲染输出文本
        for i in range(start_index, end_index):
            if i < len(core.output_lines):
                line = core.output_lines[i]
                text_surface = self.font.render(line, True, (200, 220, 255))
                screen.blit(text_surface, (scaled_10, y_pos))
                y_pos += scaled_20
        
        # 渲染输入区域
        input_y = scaled_console_height - scaled_50
        pygame.draw.line(screen, (100, 150, 200), 
                        (0, input_y), (screen.get_width(), input_y), 2)
        
        # 渲染输入文本和光标
        input_text = f"> {input_text}"
        if self.cursor_visible:
            input_text += "_"
        input_surface = self.font.render(input_text, True, (255, 255, 200))
        screen.blit(input_surface, (scaled_10, input_y + scaled_5))

class Console:
    """
    控制台主类
    
    功能概述:
    1. 管理控制台状态
    2. 处理用户输入事件
    3. 协调核心逻辑和UI渲染
    
    属性说明:
    - state: 当前控制台状态(ConsoleState)
    - core: ConsoleCore实例
    - ui: ConsoleUI实例
    - game: 关联的游戏实例(可选)
    """
    def __init__(self, game_instance=None):
        self.state = ConsoleState.CLOSED  # 初始状态为关闭
        self.core = ConsoleCore()  # 控制台核心逻辑
        self.ui = ConsoleUI()  # 控制台UI渲染
        self.game = game_instance  # 关联的游戏实例
    
    def toggle(self):
        """切换控制台打开/关闭状态"""
        if self.state == ConsoleState.CLOSED:
            # 打开控制台
            self.state = ConsoleState.OPEN
            self.core.input_text = ""
            self.ui.cursor_visible = True
            self.ui.cursor_timer = time.time()
            self.core.add_output("=== 游戏控制台 ===")
            self.core.add_output("输入 'help' 获取命令列表")
            self.ui.scroll_offset = 0
        else:
            # 关闭控制台
            self.state = ConsoleState.CLOSED
    
    def update(self):
        """更新控制台状态(每帧调用)"""
        if self.state == ConsoleState.OPEN:
            # 更新光标闪烁效果
            current_time = time.time()
            if current_time - self.ui.cursor_timer > 0.5:
                self.ui.cursor_visible = not self.ui.cursor_visible
                self.ui.cursor_timer = current_time
    
    def handle_event(self, event):
        """
        处理用户输入事件
        
        参数:
        - event: pygame事件对象
        
        返回:
        - bool: 是否已处理该事件
        """
        if self.state != ConsoleState.OPEN:
            return False
        
        # 根据事件类型分发处理
        if event.type == pygame.MOUSEWHEEL:
            return self._handle_mouse_wheel(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event, self.game.screen if self.game else None)
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_mouse_up(event)
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_mouse_motion(event, self.game.screen if self.game else None)
        elif event.type == pygame.KEYDOWN:
            return self._handle_key_event(event)
        return False
    
    def _handle_mouse_wheel(self, event):
        """处理鼠标滚轮事件(控制台滚动)"""
        self.ui.scroll_offset -= event.y  # 根据滚轮方向调整滚动位置
        max_scroll = max(0, len(self.core.output_lines) - self.core.max_output_lines)
        # 限制滚动范围
        if self.ui.scroll_offset < 0:
            self.ui.scroll_offset = 0
        elif self.ui.scroll_offset > max_scroll:
            self.ui.scroll_offset = max_scroll
        return True
    
    def _handle_mouse_down(self, event, screen):
        """处理鼠标按下事件(开始拖动滚动条)"""
        if not screen: return False
        mouse_pos = pygame.mouse.get_pos()
        scaled_console_height = scale_value(self.ui.console_height, screen, False)
        
        # 只处理滚动条拖动
        if self.ui.scroll_bar_rect and self.ui.scroll_bar_rect.collidepoint(mouse_pos):
            self.ui.scroll_bar_dragging = True
            self.ui.scroll_bar_drag_offset = mouse_pos[1] - self.ui.scroll_bar_y
            return True
        
        return False
    
    def _handle_mouse_up(self, event):
        """处理鼠标释放事件(结束拖动滚动条)"""
        if self.ui.scroll_bar_dragging:
            self.ui.scroll_bar_dragging = False
            return True
        
        return False
    
    def _handle_mouse_motion(self, event, screen):
        """处理鼠标移动事件(拖动滚动条)"""
        if not screen: return False
        mouse_pos = pygame.mouse.get_pos()
        scaled_10 = scale_value(10, screen, False)
        scaled_console_height = scale_value(self.ui.console_height, screen, False)
        scaled_60 = scale_value(60, screen, False)
        
        if self.ui.scroll_bar_dragging:
            scroll_area_height = scaled_console_height - scaled_60
            new_y = mouse_pos[1] - self.ui.scroll_bar_drag_offset
            scroll_bar_min_y = scaled_10
            scroll_bar_max_y = scroll_bar_min_y + scroll_area_height - self.ui.scroll_bar_height
            
            # 限制滚动条位置
            if new_y < scroll_bar_min_y:
                new_y = scroll_bar_min_y
            elif new_y > scroll_bar_max_y:
                new_y = scroll_bar_max_y
                
            # 计算滚动位置百分比
            scroll_percentage = (new_y - scroll_bar_min_y) / (scroll_area_height - self.ui.scroll_bar_height)
            max_scroll = max(0, len(self.core.output_lines) - self.core.max_output_lines)
            self.ui.scroll_offset = int(scroll_percentage * max_scroll)
            return True
        
        return False
    
    def _handle_key_event(self, event):
        """
        处理键盘事件
        
        支持的按键:
        - 回车: 执行命令
        - 退格: 删除字符
        - Tab: 自动补全
        - 上下箭头: 浏览历史
        - ESC: 关闭控制台
        - Ctrl+L: 清屏
        """
        if event.key == pygame.K_RETURN:
            self.core._execute_command(self.game)
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.core.input_text = self.core.input_text[:-1]
            return True
        elif event.key == pygame.K_TAB:
            self.core._auto_complete()
            return True
        elif event.key == pygame.K_UP:
            self.core._navigate_history(-1)  # 上一条历史
            return True
        elif event.key == pygame.K_DOWN:
            self.core._navigate_history(1)  # 下一条历史
            return True
        elif event.key == pygame.K_ESCAPE:
            self.toggle()  # 切换控制台状态
            return True
        elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.core._cmd_clear([])  # Ctrl+L 清屏
            return True
        elif event.unicode and event.unicode.isprintable():
            self.core.input_text += event.unicode  # 添加可打印字符
            return True
        return False
    
    def render(self, screen):
        """
        渲染控制台到屏幕
        
        参数:
        - screen: 游戏主屏幕表面
        """
        self.ui.render(screen, self.core, self.state, self.core.input_text)