from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from wrapper.load_balancer import LoadBalancer
from wrapper.models import Server, SentMessage


class TestLoadBalancer(TestCase):
    def setUp(self):
        start_time = timezone.now()
        s1 = Server(url='server1', weight=0.3)
        s1.save()
        SentMessage(
            number='1112223333', 
            server=s1, 
            start_time=start_time,
            end_time=start_time + timedelta(seconds=1)
        ).save()
        s2 = Server(url='server2', weight=0.3)
        s2.save()
        SentMessage(
            number='1112224444', 
            server=s2, 
            start_time=start_time,
            end_time=start_time + timedelta(seconds=11)
        ).save()
        s3 = Server(url='server3', weight=0.4)
        s3.save()
        SentMessage(
            number='1112225555', 
            server=s3, 
            start_time=start_time,
            end_time=start_time + timedelta(seconds=111)
        ).save()
        self.servers = [s1, s2, s3]

    def test_set_strat_sets_strategy(self):
        lb = LoadBalancer()
        rr = 'round_robin'
        lb.set_strat(rr)
        self.assertEqual(lb.strategy, rr)

    def test_set_strat_rejects_invalid_strategy(self):
        lb = LoadBalancer()
        rr = 'round_rogers'
        lb.set_strat(rr)
        self.assertFalse(lb.strategy == rr)

    @mock.patch('wrapper.load_balancer.LoadBalancer._weighted_random')
    @mock.patch('wrapper.load_balancer.LoadBalancer._rolling_avg')
    @mock.patch('wrapper.load_balancer.requests.post')
    def test_request_uses_selected_strategy(self, m_request, m_avg, m_rand):
        #Assert we have called the LB's default strategy
        lb = LoadBalancer()
        lb.targeted_url = 'server1'
        lb.request('some_data')
        m_rand.assert_called_once()

        #Assert we have called the LB's reassgined strategy
        lb.targeted_url = 'server2'
        lb.set_strat('rolling_avg')
        lb.request('some_other_data')
        m_avg.asser_called_once()

        #Assert our requests were made to the targeted_url each time
        expected = [mock.call('server1', headers={}, json='some_data'), mock.call('server2', headers={}, json='some_other_data')]
        self.assertEqual(m_request.call_args_list, expected)

    def test__weighted_random_selects_random_target_from_list(self):
        lb = LoadBalancer()
        lb._weighted_random()
        self.assertTrue(lb.targeted_url in ['server1', 'server2', 'server3'])

    def test__rolling_avg_selects_target_with_least_latency(self):
        lb = LoadBalancer()
        lb._rolling_avg()
        self.assertEqual(lb.targeted_url, 'server1')

    def test__round_robin_selects_next_in_target_list(self):
        lb = LoadBalancer()
        lb._round_robin()
        self.assertEqual(lb.targeted_url, 'server1')
        lb._round_robin()
        self.assertEqual(lb.targeted_url, 'server2')
        lb._round_robin()
        self.assertEqual(lb.targeted_url, 'server3')
        lb._round_robin()
        self.assertEqual(lb.targeted_url, 'server1')

    def tearDown(self):
        for s in self.servers:
            s.delete()


