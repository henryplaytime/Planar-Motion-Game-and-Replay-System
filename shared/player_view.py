"""
游戏与回放共用的玩家表现层。

原则：这里不做游戏逻辑，也不 import game / Replay_System，只消费 player 对象。
"""
import pygame

import data


def draw_player_body(screen, player):
    """玩家本体。委托给 Player.draw()，因为纹理/精灵在 player.py 里。"""
    player.draw(screen)


def draw_player_state_label(screen, player):
    """玩家头顶的 行走/奔跑 状态标签。"""
    running = player.sprinting
    text = data.PLAYER_STATUS_RUNNING if running else data.PLAYER_STATUS_WALKING
    color = data.STATUS_RUNNING_COLOR if running else data.STATUS_WALKING_COLOR

    font = data.get_font(data.get_scaled_font(data.INFO_FONT_SIZE, screen))
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(
        int(player.position[0]),
        int(player.position[1] - 60),
    ))

    bg = rect.inflate(20, 10)
    pygame.draw.rect(screen, data.get_rgba_color(data.PANEL_COLOR), bg, border_radius=5)
    pygame.draw.rect(screen, data.UI_HIGHLIGHT, bg, 2, border_radius=5)
    screen.blit(surf, rect)


def draw_player_stats(screen, player):
    """左下角速度 / 位置 / 着地 / 肾上腺素。"""
    font = data.get_font(data.get_scaled_font(data.SMALL_FONT_SIZE, screen))

    speed = data.calculate_speed(player.velocity)
    speed_text = font.render(
        data.PLAYER_SPEED_FORMAT.format(speed), True, data.INFO_LIGHT_BLUE)
    screen.blit(speed_text, data.scale_position(10, data.SCREEN_HEIGHT - 60, screen))

    pos_text = font.render(
        data.PLAYER_POSITION_FORMAT.format(
            int(player.position[0]), int(player.position[1])),
        True, data.INFO_LIGHT_BLUE)
    screen.blit(pos_text, data.scale_position(10, data.SCREEN_HEIGHT - 30, screen))

    ground_status = data.PLAYER_STATUS_GROUND if player.grounded else data.PLAYER_STATUS_AIR
    ground_color = data.STATUS_GROUND_COLOR if player.grounded else data.STATUS_AIR_COLOR
    ground_text = font.render(
        data.PLAYER_STATUS_FORMAT.format(ground_status), True, ground_color)
    screen.blit(ground_text, data.scale_position(10, data.SCREEN_HEIGHT - 90, screen))

    if player.adrenaline_active:
        adren_text = font.render(
            data.PLAYER_ADRENALINE_ACTIVE, True, data.ADRENALINE_ACTIVE_COLOR)
        screen.blit(adren_text, data.scale_position(10, data.SCREEN_HEIGHT - 120, screen))