# -*- coding: utf-8 -*-
"""main() 集成契约测试（本地架构版）。

由上游 test_auth_failures/test_transient_failures 的 AuthMainTests 改写：
上游 main 是纯返回值小流程，本地 main 带状态库/多渠道推送/生活资讯尾部，
因此这里把网络与文件副作用全部挡在接缝上，只验证决策逻辑与隐私边界。
"""
import contextlib
import os
import types
import unittest
from unittest import mock

from glados_checkin import app as checkin

COOKIE = 'gld:sess=synthetic-session; gld:sess.sig=synthetic-signature'
USER_AGENT = 'SyntheticBrowser/1.0'
SUCCESS = {'code': 0, 'message': 'Checkin! Got 12 Points'}
DENIAL = {'code': -2, 'reason': 'device-mismatch', 'message': 'denied ' + COOKIE}
TRANSIENT = {'request_failed': True, 'reason': 'request-failed', 'http_status': 500}
PRIVATES = ('synthetic-session', 'synthetic-signature', 'private@example.test')

DEFAULT_DATA_KEYS = (
    "points_history", "checkin_streak", "checkin_dates", "achievements",
    "checkin_times", "checkin_runs", "heartbeat_alerts", "exchange_alerts",
    "important_day_alerts", "actions_monitor",
)


def fresh_data():
    return {k: {} for k in DEFAULT_DATA_KEYS}


def make_client(checkin_result, points='100'):
    c = mock.Mock()
    c.checkin.return_value = checkin_result
    c.get_status.return_value = True
    c.get_points.return_value = True
    c.exchange.return_value = {'code': 0, 'message': 'ok'}
    c.email = 'private@example.test'
    c.points = points
    c.left_days = '30'
    c.points_change = '+12'
    c.plans_list = [{'need': 500, 'days': 100, 'diff': 400, 'ready': False}]
    c.checkin_result = checkin_result
    c.earned_points = None
    c.exchange_result = ''
    return c


@contextlib.contextmanager
def offline_main(env=None, clients=()):
    config = {
        'GLADOS_COOKIE': COOKIE,
        'GLADOS_USER_AGENT': USER_AGENT,
        'PUSHPLUS_TOKEN': 'private-push-token',
    }
    config.update(env or {})
    target = 'glados_checkin.app.'
    patches = {
        'time.sleep': {}, 'GLaDOS': {'side_effect': list(clients)},
        'log': {}, 'load_data': {'side_effect': fresh_data},
        'save_data': {}, 'export_checkin_log': {}, 'send_exchange_alerts': {},
        'send_alert': {}, 'format_dingtalk_message': {'return_value': '[account]'},
        'pushplus_push': {'return_value': True}, 'serverchan': {'return_value': True},
        'telegram_push': {'return_value': True}, 'dingtalk': {'return_value': True},
        'bark_push': {'return_value': True},
    }
    for name in ('get_weather', 'get_morning_greeting', 'get_quote', 'get_daily_quote_en',
                 'get_sun_info', 'get_daily_news', 'get_crypto_forex',
                 'get_movie_recommendation', 'get_today_in_history', 'get_server_status'):
        patches[name] = {'return_value': ''}

    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.dict(os.environ, config, clear=True))
        handles = {}
        for name, kwargs in patches.items():
            handles[name] = stack.enter_context(
                mock.patch(target + name, **kwargs))
        yield types.SimpleNamespace(
            client_cls=handles['GLaDOS'], log=handles['log'],
            send_alert=handles['send_alert'], pushplus=handles['pushplus_push'])


def assert_no_leak(test, *chunks):
    """隐私审计：只针对日志与消息正文，通道 token 作首参属正常传参。"""
    joined = ''.join(str(c) for c in chunks)
    for p in PRIVATES:
        test.assertNotIn(p, joined)


class MainDecisionTests(unittest.TestCase):
    def test_auth_denial_stops_followups_alerts_with_safe_text(self):
        c = make_client(DENIAL)
        with offline_main(clients=[c]) as ns:
            checkin.main()
        c.checkin.assert_called_once()          # 认证类失败不重试
        c.get_status.assert_not_called()        # 拒绝后禁止后续读取
        c.get_points.assert_not_called()
        c.exchange.assert_not_called()
        ns.send_alert.assert_called_once()      # Cookie 失效告警
        ns.pushplus.assert_called_once()
        assert_no_leak(self, ns.log.call_args_list, ns.send_alert.call_args_list,
                       ns.pushplus.call_args_list)

    def test_transient_failure_retries_and_skips_followups(self):
        c = make_client(TRANSIENT)
        env = {'CHECKIN_MAX_ATTEMPTS': '2', 'CHECKIN_RETRY_DELAY_SECONDS': '5'}
        with offline_main(env=env, clients=[c]) as ns:
            checkin.main()
        self.assertEqual(c.checkin.call_count, 2)
        c.get_status.assert_not_called()        # 没拿到 API 响应时不再读取
        ns.send_alert.assert_not_called()       # 网络异常不武断告警 Cookie 过期
        ns.pushplus.assert_called_once()
        assert_no_leak(self, ns.log.call_args_list, ns.pushplus.call_args_list)

    def test_denied_account_does_not_block_next_account(self):
        second = make_client(SUCCESS)
        first = make_client(DENIAL)
        env = {'GLADOS_COOKIE': COOKIE + '&gld:sess=s2; gld:sess.sig=s2sig'}
        with offline_main(env=env, clients=[first, second]):
            checkin.main()
        second.get_status.assert_called()       # 坏 Cookie 不影响好 Cookie

    def test_success_reads_status_and_skips_push_when_fail_only(self):
        c = make_client(SUCCESS)
        env = {'PUSH_LEVEL': 'fail_only', 'SEND_KEY': 'SCTprivate-push-token'}
        with offline_main(env=env, clients=[c]) as ns:
            checkin.main()
        c.get_status.assert_called_once()
        c.get_points.assert_called_once()
        ns.pushplus.assert_not_called()
        ns.send_alert.assert_not_called()

    def test_exchange_plan_enabled_exchanges_after_checkin(self):
        c = make_client(SUCCESS, points='600')
        with offline_main(env={'EXCHANGE_PLAN': 'plan500'}, clients=[c]):
            checkin.main()
        c.exchange.assert_called_once_with('plan500')
        self.assertGreaterEqual(c.get_status.call_count, 2)  # 兑换后刷新

    def test_exchange_disabled_by_default_locally(self):
        c = make_client(SUCCESS, points='600')
        with offline_main(clients=[c]):
            checkin.main()
        c.exchange.assert_not_called()          # 本地默认 off（与上游差异）

    def test_ua_error_exits_before_any_client_or_push(self):
        with offline_main(env={'GLADOS_USER_AGENT': USER_AGENT + '\nBroken'}) as ns:
            with self.assertRaises(SystemExit) as ctx:
                checkin.main()
        self.assertEqual(ctx.exception.code, 1)
        ns.client_cls.assert_not_called()
        ns.pushplus.assert_not_called()
        output = str(ns.log.call_args_list) + str(ns.send_alert.call_args_list)
        self.assertIn('User-Agent 配置错误', output)
        self.assertNotIn(USER_AGENT, output)  # UA 原值也绝不回显


class MainDiagnosticTests(unittest.TestCase):
    def test_read_only_mode_exits_without_writes_or_checkin(self):
        c = make_client(DENIAL)
        env = {'CHECKIN_DIAGNOSTIC_ONLY': 'true'}
        with offline_main(env=env, clients=[c]) as ns:
            with self.assertRaises(SystemExit) as ctx:
                checkin.main()
        self.assertEqual(ctx.exception.code, 1)
        c.checkin.assert_not_called()
        ns.pushplus.assert_not_called()


if __name__ == '__main__':
    unittest.main()
