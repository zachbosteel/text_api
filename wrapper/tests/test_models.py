from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from wrapper.models import Server, SentMessage


class TestServer(TestCase):
    def setUp(self):
        start_time = timezone.now()
        self.s1 = Server(url='server1', weight=0.3)
        self.s1.save()
        SentMessage(
            number='1112223333', 
            server=self.s1, 
            start_time=start_time,
            end_time=start_time + timedelta(microseconds=2)
        ).save()
        SentMessage(
            number='1112224444', 
            server=self.s1, 
            start_time=start_time,
            end_time=start_time + timedelta(microseconds=4)
        ).save()
        eight_minutes_ago=start_time - timedelta(minutes=8)
        SentMessage(
            number='1112224444', 
            server=self.s1, 
            start_time=eight_minutes_ago,
            end_time=eight_minutes_ago + timedelta(microseconds=6)
        ).save()
        self.s2 = Server(url='server2', weight=0.3)
        self.s2.save()

    def test_rolling_latency_returns_average_of_recent_messages(self):
        self.assertEqual(self.s1.rolling_latency(limit=5), 3)

    def test_rolling_latency_returns_zero_if_no_recent_messages(self):
        self.assertEqual(self.s1.rolling_latency(limit=5), 3)

    def test_rolilng_latency_limits_appropriately(self):
        self.assertEqual(self.s1.rolling_latency(limit=1), 4)
        self.assertEqual(self.s1.rolling_latency(limit=5), 3)

    def test_rolilng_latency_restricts_by_window_appropriately(self):
        self.assertEqual(self.s1.rolling_latency(limit=5, window=1), 3)
        self.assertEqual(self.s1.rolling_latency(limit=5, window=10), 4)

    def tearDown(self):
        self.s1.delete()
        self.s2.delete()



class TestSentMessage(TestCase):
    def test_latency_returns_microseconds_between_start_and_end(self):
        start = timezone.now()
        end = start + timedelta(microseconds=1)
        sm = SentMessage(
            number="4443332222",
            start_time=start,
            end_time=end
        )
        self.assertEqual(sm.latency(), 1)

    def test_latency_returns_zero_on_error(self):
        start = timezone.now()
        end = start + timedelta(microseconds=1)
        sm = SentMessage(
            number="4443332222",
            start_time=start,
            end_time=end
        )
        self.assertEqual(sm.latency(), 1)
