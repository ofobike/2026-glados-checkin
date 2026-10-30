# -*- coding: utf-8 -*-
"""推送渠道自检（v1.11.0 新增，RUN_MODE=notify_test）。

给每个"已配置凭据"的推送渠道各发一条测试消息，汇总哪些成功、哪些失败。
用途：首次配置或多渠道变更后，一次性验证全部通道，不用等下一次真实签到。

不改动任何签到逻辑；渠道函数全部复用 notifiers/bark 现有实现，
测试结果与真实推送走完全相同的代码路径（含 HTML/降级行为）。
"""

import os

from glados_checkin.bark import bark_event_push
from glados_checkin.notifiers import dingtalk, pushplus_push, serverchan, telegram_push
from glados_checkin.utils import log, now_bjt

TEST_TITLE = "🔔 GLaDOS 推送渠道自检"


def _test_body():
    """测试消息正文：带时间戳，方便确认收到的是哪一次自检。"""
    return (
        f"这是一条渠道自检消息，收到即表示该通道配置正确。\n\n"
        f"时间: {now_bjt().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)\n"
        f"来源: RUN_MODE=notify_test"
    )


def _bark_test(bark_key):
    """Bark 走事件推送通道（与心跳/兑换提醒同一条路径）。"""
    return bark_event_push(
        bark_key,
        TEST_TITLE,
        _test_body(),
        level="active",
        sound="birdsong",
        group_suffix="自检",
    )


def run_notify_test():
    """逐个测试已配置渠道，返回退出码：0=全部成功，1=有失败或未配置。"""
    log("🔔 推送渠道自检开始（只发消息，不签到、不读取 Cookie）...")

    body = _test_body()
    # (渠道名, 是否已配置, 测试函数)：未配置的直接跳过，不计入失败
    channels = [
        (
            "PushPlus",
            bool(os.environ.get("PUSHPLUS_TOKEN")),
            lambda: pushplus_push(os.environ.get("PUSHPLUS_TOKEN"), TEST_TITLE, body),
        ),
        (
            "Server酱",
            bool(os.environ.get("SEND_KEY")),
            lambda: serverchan(os.environ.get("SEND_KEY"), TEST_TITLE, body),
        ),
        (
            "Telegram",
            bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
            lambda: telegram_push(
                os.environ.get("TELEGRAM_BOT_TOKEN"),
                os.environ.get("TELEGRAM_CHAT_ID"),
                TEST_TITLE,
                body,
            ),
        ),
        (
            "钉钉",
            bool(os.environ.get("DINGTALK_TOKEN")),
            lambda: dingtalk(os.environ.get("DINGTALK_TOKEN"), TEST_TITLE, body),
        ),
        (
            "Bark",
            bool(os.environ.get("BARK_KEY")),
            lambda: _bark_test(os.environ.get("BARK_KEY")),
        ),
    ]

    configured = [c for c in channels if c[1]]
    if not configured:
        log("⚠️ 没有配置任何推送渠道（PUSHPLUS_TOKEN/SEND_KEY/TELEGRAM_*/DINGTALK_TOKEN/BARK_KEY）")
        log("❌ 自检失败：至少配置一个渠道后才能自检")
        return 1

    results = []
    failed = 0
    for name, _, test in configured:
        try:
            ok = bool(test())
        except Exception as e:
            # 渠道实现内部已捕获常规异常；这里兜底网络库抛出的意外错误，
            # 只打异常类名，避免异常文本携带 token 等敏感信息
            log(f"❌ {name} 自检异常: {type(e).__name__}")
            ok = False
        results.append((name, ok))
        if not ok:
            failed += 1

    # 汇总报告（与 actions_monitor 的推送状态行风格一致）
    summary = " | ".join(f"{'✅' if ok else '❌'} {name}" for name, ok in results)
    log(f"📱 自检结果: {summary}")

    if failed:
        log(f"⚠️ {failed}/{len(results)} 个渠道失败，请检查对应 Secrets 配置与网络可达性")
        return 1
    log(f"✅ 全部 {len(results)} 个已配置渠道自检通过")
    return 0
