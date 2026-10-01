"""
全局 HUD：状态徽章。

展示当前 AppState 和（若存在）场景子状态。
挂在 AppLoop.render 的最后一步，所有场景自动拥有。
"""
import pygame

import data


def draw_state_badge(screen, state, sub_state=None):
    name = state.name if hasattr(state, "name") else str(state)
    text = name
    if sub_state is not None:
        sub_name = sub_state.name if hasattr(sub_state, "name") else str(sub_state)
        text = f"{name} / {sub_name}"

    font_size = data.get_scaled_font(data.SMALL_FONT_SIZE, screen)
    font = data.get_font(font_size)
    surface = font.render(text, True, (230, 220, 130))

    pad_x, pad_y = 10, 5
    bg = pygame.Surface(
        (surface.get_width() + pad_x * 2, surface.get_height() + pad_y * 2),
        pygame.SRCALPHA,
    )
    bg.fill((0, 0, 0, 160))
    pygame.draw.rect(bg, (100, 150, 200), bg.get_rect(), 1)

    pos = (10, screen.get_height() - bg.get_height() - 10)
    screen.blit(bg, pos)
    screen.blit(surface, (pos[0] + pad_x, pos[1] + pad_y))