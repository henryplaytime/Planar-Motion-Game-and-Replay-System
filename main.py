"""
游戏入口模块
包含游戏主菜单和程序入口函数
实现游戏模式选择(开始游戏/回放游戏/退出)
"""

from game import Game
from Replay_System import run_replay_mode
import data
import pygame
import sys
from console import Console, ConsoleState

def main_menu():
    """
    游戏主菜单函数
    
    功能概述:
    1. 初始化Pygame和屏幕
    2. 创建控制台对象
    3. 显示主菜单选项
    4. 处理用户选择
    
    菜单选项:
    - 开始游戏: 进入游戏主循环
    - 回放游戏: 进入回放模式
    - 退出: 退出游戏
    """
    # 初始化Pygame
    pygame.init()
    # 创建可调整大小的窗口
    screen = pygame.display.set_mode((data.SCREEN_WIDTH, data.SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("游戏主菜单")
    
    # 创建控制台对象
    console = Console()
    
    # 主菜单循环
    while True:
        # 渲染菜单
        render_menu(screen, console)
        
        # 处理事件
        handle_menu_events(screen, console)

def render_menu(screen, console):
    """
    渲染主菜单界面
    
    参数:
    - screen: 游戏屏幕对象
    - console: 控制台对象
    """
    screen.fill(data.BACKGROUND)  # 填充背景色
    
    # 计算适配屏幕的字体大小
    title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
    option_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, screen)
    font_title = data.get_font(title_font_size)
    font_option = data.get_font(option_font_size)
    
    # 渲染标题
    title = font_title.render("游戏主菜单", True, data.TEXT_COLOR)
    title_pos = (
        screen.get_width() // 2 - title.get_width() // 2,
        data.scale_value(screen.get_height() * 0.2, screen, False)
    )
    screen.blit(title, title_pos)
    
    # 定义菜单选项
    options = [
        ("开始游戏", data.INFO_COLOR),
        ("回放游戏", data.INFO_COLOR),
        ("退出", data.EXIT_BUTTON_COLOR)
    ]
    
    # 渲染菜单选项
    for i, (text, color) in enumerate(options):
        option = font_option.render(text, True, color)
        x = screen.get_width() // 2 - option.get_width() // 2
        y = data.scale_value(screen.get_height() * 0.4 + i * screen.get_height() * 0.1, screen, False)
        screen.blit(option, (x, y))
    
    # 更新和渲染控制台
    console.update()
    console.render(screen)
    
    pygame.display.flip()  # 更新显示

def handle_menu_events(screen, console):
    """
    处理主菜单事件
    
    参数:
    - screen: 游戏屏幕对象
    - console: 控制台对象
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 退出事件
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:  # 窗口大小变化
            # 重新创建屏幕对象
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:  # 按键事件
            handle_menu_keydown(event, console, screen)
        elif event.type == pygame.MOUSEBUTTONDOWN:  # 鼠标点击事件
            handle_menu_mouse_click(event, console, screen)

def handle_menu_keydown(event, console, screen):
    """
    处理主菜单按键事件
    
    参数:
    - event: 事件对象
    - console: 控制台对象
    - screen: 游戏屏幕对象
    """
    if event.key == pygame.K_BACKQUOTE:  # 反引号键
        console.toggle()  # 切换控制台
    else:
        # 控制台处理事件
        if console.handle_event(event):  
            return
    
    # 处理其他按键
    if event.key == pygame.K_1:  # 数字1键 - 开始游戏
        start_game(screen, console)
    elif event.key == pygame.K_2:  # 数字2键 - 回放游戏
        run_replay_mode(screen)
    elif event.key == pygame.K_3:  # 数字3键 - 退出
        pygame.quit()
        sys.exit()

def handle_menu_mouse_click(event, console, screen):
    """
    处理主菜单鼠标点击事件
    
    参数:
    - event: 事件对象
    - console: 控制台对象
    - screen: 游戏屏幕对象
    """
    if console.state != ConsoleState.CLOSED:  # 控制台打开时不处理菜单点击
        return
    
    # 获取鼠标位置
    x, y = event.pos
    
    # 定义菜单选项
    options = [
        ("开始游戏", data.INFO_COLOR),
        ("回放游戏", data.INFO_COLOR),
        ("退出", data.EXIT_BUTTON_COLOR)
    ]
    
    # 检查点击了哪个菜单选项
    for i, (text, _) in enumerate(options):
        # 计算当前字体大小(可能因屏幕缩放变化)
        current_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, screen)
        current_font = data.get_font(current_font_size)
        
        # 渲染选项表面以获取尺寸
        option_surface = current_font.render(text, True, options[i][1])
        option_width = option_surface.get_width()
        option_height = option_surface.get_height()
        
        # 计算选项位置
        option_x = screen.get_width() // 2 - option_width // 2
        option_y = data.scale_value(
            screen.get_height() * 0.4 + i * screen.get_height() * 0.1, 
            screen, 
            False
        )
        
        # 检查是否点击了该选项
        if (option_x <= x <= option_x + option_width and 
            option_y <= y <= option_y + option_height):
            if text == "开始游戏":
                start_game(screen, console)
            elif text == "回放游戏":
                run_replay_mode(screen)
            elif text == "退出":
                pygame.quit()
                sys.exit()

def start_game(screen, console):
    """
    启动游戏主循环
    
    参数:
    - screen: 游戏屏幕对象
    - console: 控制台对象
    """
    game = Game(screen)
    game.console = console
    game.console.game = game
    game.run()

if __name__ == "__main__":
    """
    程序入口点
    
    当直接运行此文件时，启动游戏主菜单
    """
    main_menu()