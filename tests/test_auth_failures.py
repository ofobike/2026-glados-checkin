import os
import unittest
from unittest import mock

from glados_checkin import app as checkin


COOKIE = 'gld:sess=synthetic-session; gld:sess.sig=synthetic-signature'
USER_AGENT = 'Mozilla/5.0 SyntheticBrowser/1.0'
DENIAL = {
    'code': 4,
    'reason': 'device-mismatch',
    'message': 'Automated check-in detected. Please sign in again to continue.',
}


class OfflineTestCase(unittest.TestCase):
    def setUp(self):
        network = mock.patch(
            'requests.sessions.Session.request',
            side_effect=AssertionError('Live HTTP disabled in regression tests'),
        )
        network.start()
        self.addCleanup(network.stop)


class AuthFailureTests(OfflineTestCase):
    @mock.patch('glados_checkin.app.time.sleep')
    @mock.patch('glados_checkin.app.requests.post')
    @mock.patch('glados_checkin.app.requests.get')
    def test_http_auth_denial_stops_domain_fallback_and_checkin_retries(self, get, post, sleep):
        for status in (401, 403):
            with self.subTest(status=status), mock.patch.dict(os.environ, {}, clear=True):
                post.reset_mock()
                get.reset_mock()
                sleep.reset_mock()
                get.return_value = mock.Mock(status_code=200)
                get.return_value.json.return_value = {'code': 0, 'nonce': 'synthetic-nonce', 'ttl': 300000}
                response = mock.Mock(status_code=status)
                response.json.side_effect = ValueError('synthetic private response body')
                post.return_value = response

                result, success = checkin.checkin_with_retry(checkin.GLaDOS(COOKIE))

                self.assertFalse(success)
                self.assertEqual(result['http_status'], status)
                self.assertEqual(post.call_count, 1)
                self.assertEqual(get.call_count, 1)
                response.json.assert_not_called()
                sleep.assert_called_once_with(2.7)

    def test_explicit_auth_denial_overrides_success_code_or_message(self):
        for result in (
            dict(DENIAL, code=0),
            dict(DENIAL, message="Today's observation logged. Return tomorrow."),
            {'code': 0, 'http_status': 403},
        ):
            with self.subTest(result=result):
                self.assertFalse(checkin.is_normal_checkin_result(result))

    @mock.patch('glados_checkin.app.log')
    def test_retry_auth_log_does_not_echo_response_or_untrusted_fields(self, log):
        response = dict(
            DENIAL,
            reason='untrusted-private-reason',
            message='Automated check-in detected: ' + COOKIE + ' private@example.test',
        )
        client = mock.Mock()
        client.checkin.return_value = response

        result, success = checkin.checkin_with_retry(client)

        self.assertFalse(success)
        self.assertEqual(result, response)
        self.assertEqual(client.checkin.call_count, 1)
        output = str(log.call_args_list)
        self.assertIn('code=4', output)
        for value in ('synthetic-session', 'synthetic-signature', 'private@example.test',
                      'untrusted-private-reason'):
            self.assertNotIn(value, output)

    @mock.patch('glados_checkin.app.requests.get')
    def test_transient_http_error_still_falls_back_to_next_domain(self, get):
        unavailable = mock.Mock(status_code=503)
        ok = mock.Mock(status_code=200)
        ok.json.return_value = {'code': 0, 'data': {'leftDays': 123}}
        get.side_effect = [unavailable, ok]
        with mock.patch.dict(os.environ, {}, clear=True):
            client = checkin.GLaDOS(COOKIE)
            result = client.req('GET', '/api/user/status')

        self.assertEqual(result, ok.json.return_value)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(client.domain, checkin.DOMAINS[1])

    @mock.patch('glados_checkin.app.requests.post')
    @mock.patch('glados_checkin.app.requests.get')
    @mock.patch('glados_checkin.app.time.sleep')
    def test_configured_cookie_and_user_agent_reach_checkin_request(self, sleep, get, post):
        get.return_value = mock.Mock(status_code=200)
        get.return_value.json.return_value = {'code': 0, 'nonce': 'synthetic-nonce', 'ttl': 300000}
        post.return_value = mock.Mock(status_code=200)
        post.return_value.json.return_value = DENIAL
        with mock.patch.dict(os.environ, {'GLADOS_USER_AGENT': USER_AGENT}, clear=True):
            self.assertEqual(checkin.GLaDOS(COOKIE).checkin(), DENIAL)

        headers = post.call_args.kwargs['headers']
        self.assertEqual(headers['Cookie'], COOKIE)
        self.assertEqual(headers['User-Agent'], USER_AGENT)

# AuthMainTests 已按本地架构重写为 tests/test_main_integration.py
