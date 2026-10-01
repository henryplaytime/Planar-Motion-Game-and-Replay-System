"""
旧版本 (v1 / v2) 录制文件兼容层。

作用:
- 让 GameReplayer 只需要处理一种 Recording 结构
- 旧格式没有 eid 概念 → 全部映射到 eid=0 / etype=P
- 旧格式没有 flags → 位置参数转成 dict

只读，不写。写永远走 record_format.py (3.0)。
"""
from shared.record_format import (
    ETYPE_PLAYER, EntitySpec, Recording, RecordHeader, Snapshot,
)

import data


def load(path) -> Recording:
    header = RecordHeader(
        version=data.RECORD_VERSION,
        screen_width=data.SCREEN_WIDTH,
        screen_height=data.SCREEN_HEIGHT,
        record_fps=data.RECORD_FPS,
        start_time=0.0,
    )
    commands = []
    inputs = []
    snapshots = []
    record_version = 1

    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("VERSION:"):
                record_version = int(line.split(":", 1)[1].strip())
            elif line.startswith("SCREEN_WIDTH:"):
                header.screen_width = int(line.split(":", 1)[1].strip())
            elif line.startswith("SCREEN_HEIGHT:"):
                header.screen_height = int(line.split(":", 1)[1].strip())
            elif line.startswith("RECORD_FPS:"):
                header.record_fps = int(line.split(":", 1)[1].strip())
            elif line.startswith("START_TIME:"):
                header.start_time = float(line.split(":", 1)[1].strip())
            elif "," in line:
                if record_version == 1:
                    # v1: time,x,y,vx,vy,sprinting
                    parts = line.split(",")
                    if len(parts) >= 6:
                        snapshots.append(Snapshot(
                            time=float(parts[0]), eid=0,
                            pos_x=float(parts[1]), pos_y=float(parts[2]),
                            vel_x=float(parts[3]), vel_y=float(parts[4]),
                            flags={
                                "sprint": bool(int(parts[5])),
                                "adr": False,
                                "gnd": True,
                            },
                        ))
                else:
                    # v2: <prefix>:<time>,...
                    prefix, rest = line.split(":", 1)
                    parts = rest.split(",")
                    t = float(parts[0])
                    if prefix == "C":
                        commands.append((t, 0, parts[1] if len(parts) > 1 else ""))
                    elif prefix == "I":
                        inputs.append((t, 0, parts[1] if len(parts) > 1 else ""))
                    elif prefix == "S" and len(parts) >= 6:
                        adrenaline = False
                        if len(parts) >= 7:
                            try:
                                adrenaline = bool(int(parts[6]))
                            except ValueError:
                                adrenaline = False
                        snapshots.append(Snapshot(
                            time=t, eid=0,
                            pos_x=float(parts[1]), pos_y=float(parts[2]),
                            vel_x=float(parts[3]), vel_y=float(parts[4]),
                            flags={
                                "sprint": bool(int(parts[5])),
                                "adr": adrenaline,
                                "gnd": True,
                            },
                        ))

    entities = [EntitySpec(0, ETYPE_PLAYER, "player")]
    rec = Recording(header, entities, commands, inputs, snapshots)
    print(f"[legacy] 已加载旧版回放 (版本 {record_version})，"
          f"快照 {len(snapshots)} 个，总时长 {rec.total_time:.2f}s")
    return rec