"""
录制文件 (.dem) 3.0 格式的唯一读写入口。

格式规范见文件末尾"格式规范"注释。

设计原则:
- 只处理 3.0；旧版本(v1/v2)由 record_format_legacy.py 处理
- 实体注册段 E: 显式列出所有 eid，解析 S:/C:/I: 时按 eid 派发
- flags 用 "k=v;k=v" 键值对，按 etype 的 schema 转类型
- 时间基准统一: 录制端 time.time() - start_time；回放端直接用这个 t
"""
import time
from collections import namedtuple
from typing import List, Tuple, Dict, Optional

import pygame

import data


# ============ 常量 ============
ETYPE_PLAYER = "P"
ETYPE_ALLY = "F"
ETYPE_ENEMY = "E"
ETYPE_NEUTRAL = "N"

# flags schema: 每个 etype 允许出现的 flag 及类型。未列出的 flag 一律以 str 存
PLAYER_FLAGS = {"sprint": bool, "adr": bool, "gnd": bool}
NPC_FLAGS = {"hp": int, "state": str, "target": int, "anim": str, "alive": bool}

FLAG_SCHEMA = {
    ETYPE_PLAYER: PLAYER_FLAGS,
    ETYPE_ALLY: NPC_FLAGS,
    ETYPE_ENEMY: NPC_FLAGS,
    ETYPE_NEUTRAL: NPC_FLAGS,
}


# ============ 数据结构 ============
EntitySpec = namedtuple("EntitySpec", ["eid", "etype", "name"])

EntityFrameData = namedtuple(
    "EntityFrameData",
    ["eid", "position", "velocity", "flags", "command"],
)

Snapshot = namedtuple(
    "Snapshot",
    ["time", "eid", "pos_x", "pos_y", "vel_x", "vel_y", "flags"],
)


class RecordHeader:
    def __init__(self, version, screen_width, screen_height, record_fps, start_time):
        self.version = version
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.record_fps = record_fps
        self.start_time = start_time


class Recording:
    def __init__(self, header, entities, commands, inputs, snapshots):
        self.header = header
        self.entities: List[EntitySpec] = entities
        self.commands: List[Tuple[float, int, str]] = commands   # (time, eid, cmd)
        self.inputs: List[Tuple[float, int, str]] = inputs       # (time, eid, changes)
        self.snapshots: List[Snapshot] = snapshots

        # 按 eid 索引，方便回放端按实体分派
        self.snapshots_by_eid: Dict[int, List[Snapshot]] = {}
        for snap in snapshots:
            self.snapshots_by_eid.setdefault(snap.eid, []).append(snap)

        self.total_time = 0.0
        if snapshots or commands or inputs:
            self.total_time = max(
                snapshots[-1].time if snapshots else 0.0,
                commands[-1][0] if commands else 0.0,
                inputs[-1][0] if inputs else 0.0,
            )


# ============ flags 序列化 / 反序列化 ============
def _serialize_flags(flags: dict) -> str:
    if not flags:
        return ""
    return ";".join(f"{k}={_flag_to_str(v)}" for k, v in flags.items())


def _flag_to_str(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)


def _parse_flags(etype: str, flags_str: str) -> dict:
    schema = FLAG_SCHEMA.get(etype, {})
    result = {}
    if not flags_str:
        return result
    for pair in flags_str.split(";"):
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k = k.strip()
        converter = schema.get(k, str)
        try:
            if converter is bool:
                result[k] = bool(int(v))
            elif converter is int:
                result[k] = int(v)
            else:
                result[k] = converter(v)
        except (ValueError, TypeError):
            result[k] = v
    return result


# ============ 写 ============
class RecordWriter:
    """写 .dem 3.0。生命周期: open() → write_frame()* → close()。"""

    _KEYS = (
        ("w", pygame.K_w),
        ("a", pygame.K_a),
        ("s", pygame.K_s),
        ("d", pygame.K_d),
        ("shift", pygame.K_LSHIFT),
    )

    def __init__(self, path):
        self.path = path
        self.file = None
        self.start_time = 0.0
        self.last_record_time = 0.0
        self.last_snapshot_time = 0.0
        self.last_key_states = {k: False for k, _ in self._KEYS}
        self.record_interval = 1.0 / data.RECORD_FPS
        self.registered_eids = set()

    def open(self, entities: Optional[List[EntitySpec]] = None):
        self.file = open(self.path, "w")
        self.start_time = time.time()
        self.last_record_time = 0.0
        self.last_snapshot_time = 0.0
        self.last_key_states = {k: False for k, _ in self._KEYS}
        self.registered_eids = set()

        self.file.write(f"VERSION: {data.RECORD_VERSION}\n")
        self.file.write(f"SCREEN_WIDTH: {data.SCREEN_WIDTH}\n")
        self.file.write(f"SCREEN_HEIGHT: {data.SCREEN_HEIGHT}\n")
        self.file.write(f"RECORD_FPS: {data.RECORD_FPS}\n")
        self.file.write(f"START_TIME: {self.start_time}\n")

        if entities:
            for spec in entities:
                self._write_entity(spec)

    def _write_entity(self, spec: EntitySpec):
        if spec.eid in self.registered_eids:
            return
        self.file.write(f"E:{spec.eid},{spec.etype},{spec.name}\n")
        self.registered_eids.add(spec.eid)

    def register_entity(self, spec: EntitySpec):
        """运行时动态注册新实体（比如 NPC 进场）。"""
        if self.file is None:
            return
        self._write_entity(spec)

    def close(self):
        if self.file is not None:
            self.file.close()
        self.file = None

    def write_frame(self, entities: List[EntityFrameData], pressed_keys):
        """
        entities: 本帧所有实体的状态
        pressed_keys: pygame.key.get_pressed()，只有 eid=0 用
        """
        if self.file is None:
            return
        current_time = time.time() - self.start_time

        # 1. 高阶命令 (每 record_interval 采一次)
        write_command = current_time - self.last_record_time >= self.record_interval
        if write_command:
            for e in entities:
                if e.command:
                    self.file.write(f"C:{current_time:.3f},{e.eid},{e.command}\n")
            self.last_record_time = current_time

        # 2. 玩家输入变化 (只有变化才写)
        if pressed_keys is not None:
            changes = []
            for key, code in self._KEYS:
                state = bool(pressed_keys[code])
                if state != self.last_key_states[key]:
                    changes.append(f"{key.upper()}:{int(state)}")
                    self.last_key_states[key] = state
            if changes:
                self.file.write(f"I:{current_time:.3f},0,{';'.join(changes)}\n")

        # 3. 快照 (每 0.2s 采一次，所有实体各一行)
        if current_time - self.last_snapshot_time >= 0.2:
            for e in entities:
                flags_str = _serialize_flags(e.flags)
                self.file.write(
                    f"S:{current_time:.3f},{e.eid},"
                    f"{e.position[0]:.3f},{e.position[1]:.3f},"
                    f"{e.velocity[0]:.3f},{e.velocity[1]:.3f},"
                    f"{flags_str}\n"
                )
            self.last_snapshot_time = current_time


# ============ 读 ============
def load(path) -> Recording:
    """读 .dem 3.0。文件必须是 3.0；否则应走 record_loader 派发到 legacy。"""
    header = RecordHeader(
        version=data.RECORD_VERSION,
        screen_width=data.SCREEN_WIDTH,
        screen_height=data.SCREEN_HEIGHT,
        record_fps=data.RECORD_FPS,
        start_time=0.0,
    )
    entities: List[EntitySpec] = []
    etype_by_eid: Dict[int, str] = {}
    commands: List[Tuple[float, int, str]] = []
    inputs: List[Tuple[float, int, str]] = []
    snapshots: List[Snapshot] = []

    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("VERSION:"):
                header.version = int(line.split(":", 1)[1].strip())
            elif line.startswith("SCREEN_WIDTH:"):
                header.screen_width = int(line.split(":", 1)[1].strip())
            elif line.startswith("SCREEN_HEIGHT:"):
                header.screen_height = int(line.split(":", 1)[1].strip())
            elif line.startswith("RECORD_FPS:"):
                header.record_fps = int(line.split(":", 1)[1].strip())
            elif line.startswith("START_TIME:"):
                header.start_time = float(line.split(":", 1)[1].strip())

            elif line.startswith("E:"):
                # E:<eid>,<etype>,<name>
                parts = line[2:].split(",", 2)
                eid = int(parts[0])
                etype = parts[1] if len(parts) > 1 else ETYPE_PLAYER
                name = parts[2] if len(parts) > 2 else ""
                entities.append(EntitySpec(eid, etype, name))
                etype_by_eid[eid] = etype

            elif line.startswith("C:"):
                # C:<time>,<eid>,<cmd>
                parts = line[2:].split(",", 2)
                t = float(parts[0])
                eid = int(parts[1])
                cmd = parts[2] if len(parts) > 2 else ""
                commands.append((t, eid, cmd))

            elif line.startswith("I:"):
                # I:<time>,<eid>,<changes>
                parts = line[2:].split(",", 2)
                t = float(parts[0])
                eid = int(parts[1])
                ch = parts[2] if len(parts) > 2 else ""
                inputs.append((t, eid, ch))

            elif line.startswith("S:"):
                # S:<time>,<eid>,<x>,<y>,<vx>,<vy>,<flags>
                parts = line[2:].split(",", 6)
                if len(parts) < 6:
                    continue
                t = float(parts[0])
                eid = int(parts[1])
                flags_str = parts[6] if len(parts) > 6 else ""
                etype = etype_by_eid.get(eid, ETYPE_PLAYER)
                flags = _parse_flags(etype, flags_str)
                snapshots.append(Snapshot(
                    time=t, eid=eid,
                    pos_x=float(parts[2]), pos_y=float(parts[3]),
                    vel_x=float(parts[4]), vel_y=float(parts[5]),
                    flags=flags,
                ))

    rec = Recording(header, entities, commands, inputs, snapshots)
    print(f"已加载回放 (版本 {header.version}):")
    print(f"  实体: {len(entities)} 个")
    print(f"  高阶指令: {len(commands)} 条")
    print(f"  原始输入: {len(inputs)} 条")
    print(f"  状态快照: {len(snapshots)} 个")
    print(f"  总时长: {rec.total_time:.2f} 秒")
    return rec


# ============ 格式规范（给未来的自己）============
#
# VERSION: <int>                     # 必须为 3
# SCREEN_WIDTH: <int>
# SCREEN_HEIGHT: <int>
# RECORD_FPS: <int>
# START_TIME: <float>                # time.time() 起始时刻
#
# E:<eid>,<etype>,<name>
#   eid   : int, 0 恒为玩家
#   etype : P / F / E / N
#   name  : 人类可读标识, 可空
#
# C:<time>,<eid>,<command_list>
#   command_list 逗号分隔, 例: "W,A,SHIFT"
#
# I:<time>,<eid>,<key:state;...>
#   只有玩家会写; state 为 0/1
#
# S:<time>,<eid>,<x>,<y>,<vx>,<vy>,<flags>
#   flags 形如 "sprint=1;adr=0;gnd=1"
#   schema 见 FLAG_SCHEMA
#
# 演进规则:
#   加字段 → 加到对应 etype 的 flags schema，旧代码自动忽略
#   加实体类型 → 新增 ETYPE_* 和 FLAG_SCHEMA 条目
#   破格式 → 升 VERSION, 旧格式搬到 record_format_legacy.py