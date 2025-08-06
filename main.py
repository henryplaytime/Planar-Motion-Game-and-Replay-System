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
import math
from console import Console, ConsoleState
from source.menu_btn_style import create_button  # 导入工厂函数

# 全局按钮样式设置
BUTTON_STYLE = "COD"  # 默认使用COD风格

class ButtonManager:
    """管理按钮创建和样式的类"""
    @staticmethod
    def set_style(style):
        global BUTTON_STYLE
        BUTTON_STYLE = style
    
    @staticmethod
    def get_style():
        return BUTTON_STYLE
    
    @staticmethod
    def create_button(x, y, width, height, text, screen):
        return create_button(BUTTON_STYLE, x, y, width, height, text, screen)

def create_menu_buttons(screen):
    """创建主菜单按钮的函数"""
    button_width = 300
    button_height = 60
    start_y = data.SCREEN_HEIGHT * 0.4
    
    return [
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height, "开始游戏", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 100, button_width, button_height, "回放游戏", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 200, button_width, button_height, "设置", screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 300, button_width, button_height, "退出", screen)
    ]

def draw_buttons(surface, buttons, title_pos, line_y):
    """集中绘制按钮及其相关元素"""
    line_start_x = surface.get_width() // 2 - 180 * (surface.get_width() / data.BASE_WIDTH)
    line_end_x = surface.get_width() // 2 + 180 * (surface.get_width() / data.BASE_WIDTH)
    pygame.draw.line(surface, data.ACCENT_COLOR, (line_start_x, line_y), (line_end_x, line_y), 3)
    
    for button in buttons:
        button.draw(surface)

def main_menu():
    """
    游戏主菜单函数 - 只保留ESC键和~键功能
    """
    # 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode((data.SCREEN_WIDTH, data.SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("游戏主菜单")

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
    
    # 创建初始按钮
    buttons = create_menu_buttons(screen)
    
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
                buttons = create_menu_buttons(screen)
            
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
                            title = font_title.render("游戏主菜单", True, data.TEXT_COLOR)
                            title_pos = (
                                screen.get_width() // 2 - title.get_width() // 2,
                                data.scale_value(screen.get_height() * 0.2, screen, False)
                            )
                            line_y = data.scale_value(screen.get_height() * 0.25, screen, False)
                            draw_buttons(screen, buttons, title_pos, line_y)
                            pygame.display.flip()
                            pygame.time.delay(150)  # 短暂延迟让动画可见
                            
                            # 处理菜单选择，并检查是否需要重新创建按钮
                            recreate_buttons = handle_menu_selection(button.text, screen, console)
                            if recreate_buttons:
                                buttons = create_menu_buttons(screen)
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
        # 5.1 绘制背景
        screen.fill(data.BACKGROUND)
        
        # 5.2 渲染标题
        title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
        font_title = data.get_font(title_font_size)
        title = font_title.render("游戏主菜单", True, data.TEXT_COLOR)
        title_pos = (
            screen.get_width() // 2 - title.get_width() // 2,
            data.scale_value(screen.get_height() * 0.2, screen, False)
        )
        screen.blit(title, title_pos)
        
        # 5.3 计算装饰线位置
        line_y = data.scale_value(screen.get_height() * 0.25, screen, False)
        
        # 5.4 绘制所有按钮及其相关元素
        draw_buttons(screen, buttons, title_pos, line_y)
        
        # 5.5 绘制说明文字
        info_font_size = data.get_scaled_font(data.INFO_FONT_SIZE, screen)
        font_info = data.get_font(info_font_size)
        info_text = font_info.render("点击按钮选择功能 | 按ESC键退出 | ~键打开控制台", True, (150, 150, 150))
        screen.blit(info_text, (screen.get_width() // 2 - info_text.get_width() // 2, screen.get_height() - 50))
        
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

def handle_menu_selection(selection, screen, console):
    """
    处理菜单选择逻辑
    返回布尔值表示是否需要重新创建主菜单按钮
    """
    if selection == "开始游戏":
        start_game(screen, console)
        return False  # 不需要重新创建按钮
    elif selection == "回放游戏":
        run_replay_mode(screen)
        return False  # 不需要重新创建按钮
    elif selection == "设置":
        # 进入设置菜单，并返回是否需要重新创建按钮
        return settings_menu(screen, console)
    elif selection == "退出":
        pygame.quit()
        sys.exit()
    return False

def settings_menu(screen, console):
    """
    设置菜单函数
    允许用户调整游戏设置，如按钮样式
    返回布尔值表示是否需要重新创建主菜单按钮
    """
    # 初始化
    button_width = 300
    button_height = 60
    start_y = data.SCREEN_HEIGHT * 0.4

    # 创建按钮文本
    button_style_text = f"按钮样式: {'COD风格' if ButtonManager.get_style() == 'COD' else '默认'}"
    
    # 音频
    try:
        click_sound = pygame.mixer.Sound(data.SOUND_MENU_CLICK)
        hover_sound = pygame.mixer.Sound(data.SOUND_MENU_HOVER)
    except:
        click_sound = None
        hover_sound = None
    
    # 创建按钮
    buttons = [
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y, button_width, button_height, 
                    button_style_text, screen),
        ButtonManager.create_button(data.SCREEN_WIDTH//2 - button_width//2, start_y + 100, button_width, button_height, 
                    "返回", screen)
    ]
    
    # 当前选中的选项索引
    current_selected = -1
    last_hover_index = -1
    
    # 设置菜单循环
    running = True
    style_changed = False  # 记录按钮样式是否被更改
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # 窗口大小调整
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                # 更新所有按钮的屏幕引用
                for button in buttons:
                    button.screen = screen
            
            # 键盘事件
            elif event.type == pygame.KEYDOWN:
                # 控制台切换键
                if event.key == pygame.K_BACKQUOTE:
                    console.toggle()
                    continue
                # ESC键返回主菜单
                elif event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    if console.handle_event(event):
                        continue
            
            # 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                found_hover = False
                for i, button in enumerate(buttons):
                    scaled_rect = get_scaled_button_rect(button)
                    if scaled_rect.collidepoint(mouse_pos):
                        current_selected = i
                        if i != last_hover_index and hover_sound:
                            hover_sound.play()
                        last_hover_index = i
                        found_hover = True
                        break
                if not found_hover:
                    current_selected = -1
                    last_hover_index = -1
            
            # 鼠标点击事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    for i, button in enumerate(buttons):
                        scaled_rect = get_scaled_button_rect(button)
                        if scaled_rect.collidepoint(event.pos):
                            if click_sound:
                                click_sound.play()
                            
                            # 设置按钮点击状态
                            button.state = "active"
                            
                            # 立即绘制一次动画状态
                            screen.fill(data.BACKGROUND)
                            title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
                            font_title = data.get_font(title_font_size)
                            title = font_title.render("设置", True, data.TEXT_COLOR)
                            title_pos = (
                                screen.get_width() // 2 - title.get_width() // 2,
                                data.scale_value(screen.get_height() * 0.2, screen, False)
                            )
                            screen.blit(title, title_pos)
                            
                            for btn in buttons:
                                btn.draw(screen)
                            
                            pygame.display.flip()
                            pygame.time.delay(150)  # 短暂延迟让动画可见
                            
                            # 处理设置选择
                            if i == 0:  # 按钮样式切换
                                # 切换按钮样式
                                new_style = "Default" if ButtonManager.get_style() == "COD" else "COD"
                                ButtonManager.set_style(new_style)
                                
                                # 更新按钮文本
                                buttons[0].text = f"按钮样式: {'COD风格' if new_style == 'COD' else '默认'}"
                                
                                # 通知用户设置已更改
                                console.core.add_output(f"按钮样式已切换为 {'COD风格' if new_style == 'COD' else '默认'}")
                                style_changed = True  # 标记样式已更改
                            elif i == 1:  # 返回
                                running = False
                            break
        
        # 更新按钮状态
        for button in buttons:
            button.state = "idle"
        
        if current_selected >= 0 and current_selected < len(buttons):
            buttons[current_selected].state = "hover"
        
        mouse_click = False
        for button in buttons:
            button.update(mouse_pos, mouse_click)
        
        # 渲染
        screen.fill(data.BACKGROUND)
        
        # 绘制标题
        title_font_size = data.get_scaled_font(data.MENU_TITLE_FONT_SIZE, screen)
        font_title = data.get_font(title_font_size)
        title = font_title.render("设置", True, data.TEXT_COLOR)
        title_pos = (
            screen.get_width() // 2 - title.get_width() // 2,
            data.scale_value(screen.get_height() * 0.2, screen, False)
        )
        screen.blit(title, title_pos)
        
        # 绘制所有按钮
        for button in buttons:
            button.draw(screen)
        
        # 绘制说明文字
        info_font_size = data.get_scaled_font(data.INFO_FONT_SIZE, screen)
        font_info = data.get_font(info_font_size)
        info_text = font_info.render("按ESC键返回主菜单", True, (150, 150, 150))
        screen.blit(info_text, (screen.get_width() // 2 - info_text.get_width() // 2, screen.get_height() - 50))
        
        # 更新和渲染控制台
        console.update()
        console.render(screen)
        
        pygame.display.flip()
    
    # 返回样式是否被更改
    return style_changed

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
    main_menu()