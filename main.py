"""
游戏入口模块
包含游戏主菜单和程序入口函数
实现游戏模式选择(开始游戏/回放游戏/设置/退出)
"""

from game import Game
from Replay_System import run_replay_mode
import data
import pygame
import sys
import os
import json
import settings
import math
from console import Console, ConsoleState
from source.menu_btn_style import create_button  # 导入工厂函数
from source.main_loading_menu import show_loading_menu  # 导入加载菜单
from data import init_pygame, BACKGROUND  # 导入初始化函数和颜色常量

class ButtonManager:
    """管理按钮创建和样式的类"""
    @staticmethod
    def create_button(style, x, y, width, height, text, screen):
        return create_button(style, x, y, width, height, text, screen)

def create_menu_buttons(screen, button_style):
    """创建主菜单按钮的函数"""
    button_width = data.MENU_BUTTON_WIDTH
    button_height = data.MENU_BUTTON_HEIGHT
    start_y = screen.get_height() * data.MENU_BUTTON_START_Y_RATIO
    
    return [
        ButtonManager.create_button(
            button_style,
            screen.get_width() // 2 - button_width // 2, 
            start_y, 
            button_width, 
            button_height, 
            data.BUTTON_TEXT_START, 
            screen
        ),
        ButtonManager.create_button(
            button_style,
            screen.get_width() // 2 - button_width // 2, 
            start_y + data.MENU_BUTTON_SPACING, 
            button_width, 
            button_height, 
            data.BUTTON_TEXT_REPLAY, 
            screen
        ),
        ButtonManager.create_button(
            button_style,
            screen.get_width() // 2 - button_width // 2, 
            start_y + data.MENU_BUTTON_SPACING * 2, 
            button_width, 
            button_height, 
            data.BUTTON_TEXT_SETTINGS, 
            screen
        ),
        ButtonManager.create_button(
            button_style,
            screen.get_width() // 2 - button_width // 2, 
            start_y + data.MENU_BUTTON_SPACING * 3, 
            button_width, 
            button_height, 
            data.BUTTON_TEXT_EXIT, 
            screen
        )
    ]

def draw_buttons(surface, buttons, title_pos, line_y):
    """集中绘制按钮及其相关元素"""
    # 绘制装饰线
    line_width = 180 * (surface.get_width() / data.BASE_WIDTH)
    line_start_x = surface.get_width() // 2 - line_width
    line_end_x = surface.get_width() // 2 + line_width
    pygame.draw.line(surface, data.ACCENT_COLOR, (line_start_x, line_y), (line_end_x, line_y), 3)
    
    # 绘制所有按钮
    for button in buttons:
        button.draw(surface)

def main_menu(user_config):
    """
    游戏主菜单函数 - 只保留ESC键和~键功能

    参数:
        user_config (dict): 加载的用户配置
    """
    # 从配置中获取按钮样式
    button_style = user_config.get("button_style", "COD")
    
    print(f"主菜单使用的按钮样式: {button_style}")

    # 初始化Pygame
    screen = init_pygame()
    pygame.display.set_caption(data.MAIN_MENU_TITLE)

    # 初始化音频系统
    pygame.mixer.init()
    try:
        click_sound = pygame.mixer.Sound(data.SOUND_MENU_CLICK)
        hover_sound = pygame.mixer.Sound(data.SOUND_MENU_HOVER)
    except Exception as e:
        print(f"无法加载音效: {e}")
        click_sound = None
        hover_sound = None
    
    # 创建控制台对象
    console = Console()
    
    # 使用配置中的样式创建按钮
    buttons = create_menu_buttons(screen, button_style)
    
    # 当前选中的选项索引（基于鼠标悬停）
    current_selected = -1
    last_hover_index = -1
    
    # 主菜单循环
    running = True
    while running:
        # 获取当前鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 处理所有事件
        for event in pygame.event.get():
            # ===== 1. 处理窗口事件 =====
            if event.type == pygame.QUIT:
                running = False
            
            # 窗口大小调整事件
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # 重新创建按钮以适应新尺寸
                buttons = create_menu_buttons(screen, button_style)
            
            # ===== 2. 处理键盘事件 =====
            elif event.type == pygame.KEYDOWN:
                # 2.1 只保留控制台切换键（反引号键）
                if event.key == pygame.K_BACKQUOTE:
                    console.toggle()
                    continue
                
                # 2.2 只保留控制台事件处理
                if console.handle_event(event):
                    continue
                
                # 2.3 只保留ESC键退出功能
                elif event.key == pygame.K_ESCAPE:
                    running = False
            
            # ===== 3. 处理鼠标事件 =====
            # 3.1 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                # 更新鼠标位置
                mouse_pos = event.pos
                
                # 检查鼠标悬停状态
                found_hover = False
                for i, button in enumerate(buttons):
                    # 获取按钮缩放后的矩形
                    scaled_rect = get_scaled_button_rect(button)
                    
                    # 检查鼠标是否悬停在按钮上
                    if scaled_rect.collidepoint(mouse_pos):
                        # 更新当前选择
                        current_selected = i
                        
                        # 如果切换到新按钮，播放悬停音效
                        if i != last_hover_index and hover_sound:
                            hover_sound.play()
                        last_hover_index = i
                        found_hover = True
                        break
                
                # 如果没有按钮被悬停
                if not found_hover:
                    current_selected = -1
                    last_hover_index = -1
            
            # 3.2 鼠标点击事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 左键点击
                if event.button == 1:
                    # 检查点击了哪个按钮
                    for i, button in enumerate(buttons):
                        scaled_rect = get_scaled_button_rect(button)
                        
                        # 如果点击在当前按钮上
                        if scaled_rect.collidepoint(event.pos):
                            if click_sound:
                                click_sound.play()
                            
                            # 设置按钮点击状态
                            button.state = "active"
                            
                            # 立即绘制一次动画状态
                            screen.fill(data.BACKGROUND)
                            title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
                            font_title = data.get_font(title_font_size)
                            title = font_title.render(data.MAIN_MENU_TITLE, True, data.TEXT_COLOR)
                            title_pos = (
                                screen.get_width() // 2 - title.get_width() // 2,
                                data.scale_value(screen.get_height() * data.MENU_TITLE_Y_RATIO, screen, False)
                            )
                            line_y = data.scale_value(screen.get_height() * data.MENU_TITLE_LINE_Y_RATIO, screen, False)
                            draw_buttons(screen, buttons, title_pos, line_y)
                            pygame.display.flip()
                            pygame.time.delay(data.BUTTON_CLICK_ANIMATION_DELAY)  # 短暂延迟让动画可见
                            
                            # 处理菜单选择
                            result = handle_menu_selection(button.text, screen, console, button_style)
                            recreate_buttons, new_style = result
                        
                            # 更新按钮样式
                            if new_style != button_style:
                                button_style = new_style
                                user_config["button_style"] = new_style
                                print(f"按钮样式已更新为: {button_style}")
                        
                            # 重新创建按钮
                            if recreate_buttons:
                                buttons = create_menu_buttons(screen, button_style)
                            break
        
        # ===== 4. 更新界面状态 =====
        # 4.1 重置所有按钮状态
        for button in buttons:
            button.state = "idle"
        
        # 4.2 设置当前悬停按钮为悬停状态
        if current_selected >= 0 and current_selected < len(buttons):
            buttons[current_selected].state = "hover"
        
        # 4.3 更新按钮状态（包括动画）
        mouse_click = False  # 不处理点击，只处理悬停
        for button in buttons:
            button.update(mouse_pos, mouse_click)
        
        # ===== 5. 渲染界面 =====
        # 5.绘制背景
        screen.fill(BACKGROUND)
        
        # 5.2 渲染标题
        title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
        font_title = data.get_font(title_font_size)
        title = font_title.render(data.MAIN_MENU_TITLE, True, data.TEXT_COLOR)
        title_pos = (
            screen.get_width() // 2 - title.get_width() // 2,
            data.scale_value(screen.get_height() * data.MENU_TITLE_Y_RATIO, screen, False)
        )
        screen.blit(title, title_pos)
        
        # 5.3 计算装饰线位置
        line_y = data.scale_value(screen.get_height() * data.MENU_TITLE_LINE_Y_RATIO, screen, False)
        
        # 5.4 绘制所有按钮及其相关元素
        draw_buttons(screen, buttons, title_pos, line_y)
        
        # 5.5 绘制说明文字
        info_font_size = data.get_scaled_font(data.INFO_FONT_SIZE, screen)
        font_info = data.get_font(info_font_size)
        info_text = font_info.render(data.MAIN_MENU_INFO, True, (150, 150, 150))
        screen.blit(info_text, (screen.get_width() // 2 - info_text.get_width() // 2, 
                    screen.get_height() - data.MENU_INFO_BOTTOM_MARGIN))
        
        # 5.6 更新和渲染控制台
        console.update()
        console.render(screen)
        
        # 5.7 更新显示
        pygame.display.flip()
    
    # 退出游戏
    pygame.quit()
    sys.exit()

# ===== 辅助函数 =====
def get_scaled_button_rect(button):
    """
    获取按钮缩放后的矩形区域
    """
    scaled_x = data.scale_value(button.rect.x, button.screen, True)
    scaled_y = data.scale_value(button.rect.y, button.screen, False)
    scaled_width = data.scale_value(button.rect.width, button.screen, True)
    scaled_height = data.scale_value(button.rect.height, button.screen, False)
    return pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)

def handle_menu_selection(selection, screen, console, button_style):
    """
    处理菜单选择逻辑
    返回元组 (是否需要重新创建按钮, 新的按钮样式)
    """
    if selection == data.BUTTON_TEXT_START:
        start_game(screen, console)
        return (False, button_style)  # 不需要重新创建按钮，返回原样式
    elif selection == data.BUTTON_TEXT_REPLAY:
        run_replay_mode(screen)
        return (False, button_style)  # 不需要重新创建按钮，返回原样式
    elif selection == data.BUTTON_TEXT_SETTINGS:
        # 进入设置菜单，并返回元组
        return settings.settings_menu(screen, console, button_style, user_config)
    elif selection == data.BUTTON_TEXT_EXIT:
        pygame.quit()
        sys.exit()
    return (False, button_style)  # 默认返回原样式


def start_game(screen, console):
    """
    启动游戏主循环
    """
    game = Game(screen)
    game.console = console
    game.console.game = game
    game.run()

if __name__ == "__main__":
    """
    程序入口点
    """
    # 1. 尝试从加载菜单获取用户配置
    user_config_from_loading = show_loading_menu()
    
    # 2. 主程序内置的默认配置
    DEFAULT_MAIN_CONFIG = {
        "button_style": "COD",
        # 可以添加其他默认配置项
    }
    
    # 3. 合并配置 - 优先使用加载的配置，失败则使用主程序默认配置
    if user_config_from_loading and "button_style" in user_config_from_loading:
        print("使用从加载菜单获取的用户配置")
        user_config = user_config_from_loading
    else:
        print("加载用户配置失败，使用主程序内置默认配置")
        user_config = DEFAULT_MAIN_CONFIG

    # 4. 将合并后的配置传递给主菜单
    main_menu(user_config)