# -*- coding: utf-8 -*-
# source/menu_btn_style.py
import pygame
import data

class CODButton:
    def __init__(self, x, y, width, height, text, screen):
        self.rect = pygame.Rect(x, y, width, height)
        self.base_rect = pygame.Rect(x, y, width, height)
        self.current_rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.state = "idle"
        self.glow_alpha = 0
        self.pulse_direction = 1
        self.anim_progress = 0
        self.anim_direction = 0
        self.screen = screen
    
    def draw(self, surface):
        scaled_x = data.scale_value(self.base_rect.x, self.screen, True)
        scaled_y = data.scale_value(self.base_rect.y, self.screen, False)
        scaled_width = data.scale_value(self.base_rect.width, self.screen, True)
        scaled_height = data.scale_value(self.base_rect.height, self.screen, False)
        
        t = self.ease_out_quad(self.anim_progress)
        height_diff = int(30 * t)
        new_height = scaled_height + height_diff
        new_y = scaled_y - height_diff // 2
        
        anim_rect = pygame.Rect(scaled_x, new_y, scaled_width, new_height)
        
        if self.state == "idle":
            color = data.BUTTON_IDLE
            border_color = (70, 80, 90)
            border_width = 2
        elif self.state == "hover":
            color = data.BUTTON_HOVER
            border_color = (100, 110, 120)
            border_width = 3
        else:  # active
            color = data.BUTTON_ACTIVE
            border_color = (200, 170, 40)
            border_width = 4
        
        pygame.draw.rect(surface, color, anim_rect, border_radius=4)
        pygame.draw.rect(surface, border_color, anim_rect, border_width, border_radius=4)
        
        if self.state == "hover" or self.state == "active":
            glow_surf = pygame.Surface((anim_rect.width + 30, anim_rect.height + 30), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*data.GLOW_COLOR[:3], self.glow_alpha), 
                             (0, 0, glow_surf.get_width(), glow_surf.get_height()), 
                             border_radius=8)
            surface.blit(glow_surf, (anim_rect.x - 15, anim_rect.y - 15))
            
            self.glow_alpha += 3 * self.pulse_direction
            if self.glow_alpha >= 120:
                self.pulse_direction = -1
            elif self.glow_alpha <= 30:
                self.pulse_direction = 1
        
        option_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, self.screen)
        font_option = data.get_font(option_font_size)
        text_surf = font_option.render(self.text, True, data.TEXT_COLOR)
        text_rect = text_surf.get_rect(center=anim_rect.center)
        surface.blit(text_surf, text_rect)
        
        if self.state == "hover" or self.state == "active":
            pygame.draw.line(surface, data.ACCENT_COLOR, 
                            (anim_rect.left + 10, anim_rect.bottom - 5),
                            (anim_rect.right - 10, anim_rect.bottom - 5), 2)
    
    def update(self, mouse_pos, mouse_click):
        scaled_x = data.scale_value(self.base_rect.x, self.screen, True)
        scaled_y = data.scale_value(self.base_rect.y, self.screen, False)
        scaled_width = data.scale_value(self.base_rect.width, self.screen, True)
        scaled_height = data.scale_value(self.base_rect.height, self.screen, False)
        
        detect_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        if detect_rect.collidepoint(mouse_pos):
            if mouse_click:
                self.state = "active"
                return True
            else:
                self.state = "hover"
                if self.anim_direction != 1:
                    self.anim_direction = 1
        else:
            self.state = "idle"
            if self.anim_direction != -1:
                self.anim_direction = -1
        
        if self.anim_direction != 0:
            self.anim_progress += self.anim_direction * 0.1
            self.anim_progress = max(0, min(1, self.anim_progress))
            
            if self.anim_progress == 0 or self.anim_progress == 1:
                self.anim_direction = 0
        
        return False
    
    def ease_out_quad(self, t):
        return 1 - (1 - t) * (1 - t)


class DefaultButton:
    def __init__(self, x, y, width, height, text, screen):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.state = "idle"
        self.screen = screen
    
    def draw(self, surface):
        scaled_x = data.scale_value(self.rect.x, self.screen, True)
        scaled_y = data.scale_value(self.rect.y, self.screen, False)
        scaled_width = data.scale_value(self.rect.width, self.screen, True)
        scaled_height = data.scale_value(self.rect.height, self.screen, False)
        
        button_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        if self.state == "idle":
            color = data.BUTTON_IDLE
        elif self.state == "hover":
            color = data.BUTTON_HOVER
        else:  # active
            color = data.BUTTON_ACTIVE
        
        pygame.draw.rect(surface, color, button_rect, border_radius=4)
        pygame.draw.rect(surface, (70, 80, 90), button_rect, 2, border_radius=4)
        
        option_font_size = data.get_scaled_font(data.MENU_OPTION_FONT_SIZE, self.screen)
        font_option = data.get_font(option_font_size)
        text_surf = font_option.render(self.text, True, data.TEXT_COLOR)
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos, mouse_click):
        scaled_x = data.scale_value(self.rect.x, self.screen, True)
        scaled_y = data.scale_value(self.rect.y, self.screen, False)
        scaled_width = data.scale_value(self.rect.width, self.screen, True)
        scaled_height = data.scale_value(self.rect.height, self.screen, False)
        
        detect_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        
        if detect_rect.collidepoint(mouse_pos):
            if mouse_click:
                self.state = "active"
                return True
            else:
                self.state = "hover"
        else:
            self.state = "idle"
        return False


# 按钮工厂函数
def create_button(style, x, y, width, height, text, screen):
    if style == "COD":
        return CODButton(x, y, width, height, text, screen)
    else:
        return DefaultButton(x, y, width, height, text, screen)