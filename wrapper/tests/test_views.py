import json
from unittest import mock

from django.http import JsonResponse
from django.test import TestCase
from django.utils import timezone

from wrapper.load_balancer import LoadBalancer
from wrapper.models import InvalidNumber, SentMessage, Server
from wrapper.views import send, update_lb_strategy, callback


class MockRequest:
    def __init__(self, body=None):
        self.body = body

class MockResponse:
    def __init__(self, body=None):
        self.body = body


class TestSend(TestCase):
    def setUp(self):
        InvalidNumber(number="2223334444").save()

    @mock.patch("wrapper.views.JsonResponse")
    def test_send_returns_400_if_given_invalid_number(self, m_jsonresp):
        data = json.dumps({
            "number": "2223334444",
            "message": "The text is coming from inside the internet."
        })
        request = MockRequest(body=data)
        send(request)
        m_jsonresp.assert_called_with({
            "status": 400,
            "message": "The number you have submitted has been marked invalid by our SMS providers."
        }, status=400)

    @mock.patch("wrapper.views.JsonResponse")
    @mock.patch("wrapper.views.LB")
    def test_send_returns_502_if_it_exceeds_retry_count(self, m_LB, m_jsonresp):
        def side_effect(self):
            raise Exception('The bears have really bad news.')
        m_LB.request.side_effect = side_effect
        data = json.dumps({
            "number": "6667778888",
            "message": "You're doing it, Peter."
        })
        request = MockRequest(body=data)
        send(request)
        m_jsonresp.assert_called_with({
            "status": 502,
            "message": "Bad gateway. Failed to forward data. Max retries exceeded."
        }, status=502)

    @mock.patch("wrapper.views.JsonResponse")
    @mock.patch("wrapper.views.LB")
    def test_send_returns_200_on_success(self, m_LB, m_jsonresp):
        m_LB.request.return_value = MockResponse(body=json.dumps({
            "message_id": "1234"
        }))
        data = json.dumps({
            "number": "9994440101",
            "message": "Vote."
        })
        request = MockRequest(body=data)
        send(request)
        m_jsonresp.assert_called_with({
            "status": 200,
            "message": "Data successfully forwarded."
        }, status=200)

    @mock.patch("wrapper.views.LB")
    def test_send_creates_sent_message_in_db(self, m_LB):
        s = Server(url='server1', weight=0.2).save()
        m_LB.request.return_value = MockResponse(body=json.dumps({
            "message_id": "5678"
        }))
        m_LB.target_url = 'server1'
        data = json.dumps({
            "number": "9994440101",
            "message": "Vote."
        })
        request = MockRequest(body=data)
        send(request)
        sm = SentMessage.objects.all()[:1][0]
        self.assertEqual(sm.server, s)
        self.assertEqual(sm.number, "9994440101")
        self.assertEqual(sm.status, "pending")
        
    def tearDown(self):
        Server.objects.all().delete()
        SentMessage.objects.all().delete()
        InvalidNumber.objects.all().delete()

class TestUpdateLBStrategy(TestCase):
    @mock.patch("wrapper.views.LB")
    def test_update_lb_strategy_calls_set_strat_on_LB(self, m_LB):
        data = json.dumps({
            "strategy": "weighted_random"
        })
        request = MockRequest(body=data)
        update_lb_strategy(request)
        m_LB.set_strat.assert_called_with("weighted_random")

    @mock.patch("wrapper.views.JsonResponse")
    @mock.patch("wrapper.views.LB")
    def test_update_lb_strategy_returns_200(self, m_LB, m_jsonresp):
        data = json.dumps({
            "strategy": "weighted_random"
        })
        request = MockRequest(body=data)
        update_lb_strategy(request)
        m_jsonresp.assert_called_with({
            "status": 200,
            "message": "Load Balancer strategy successfully updated."
        }, status=200)

    @mock.patch("wrapper.views.JsonResponse")
    @mock.patch("wrapper.views.LB")
    def test_update_lb_strategy_returns_500_if_error(self, m_LB, m_jsonresp):
        def side_effect(self):
            raise Exception("I'm afraid I can't do that, Dave.")
        m_LB.set_strat.side_effect = side_effect

        data = json.dumps({
            "strategy": "weighted_random"
        })
        request = MockRequest(body=data)
        update_lb_strategy(request)

        m_jsonresp.assert_called_with({
            "status": 500,
            "message": "An error occurred while handling your request."
        }, status=500)



class TestCallback(TestCase):
    def setUp(self):
        s1 = Server(url="server1", weight=0.4)
        s1.save()
        start = timezone.now()
        SentMessage(
            uuid="1234",
            number="4347672121",
            server=s1,
            status="pending",
            start_time=start
        ).save()
        SentMessage(
            uuid="5678",
            number="0192019211",
            server=s1,
            status="pending",
            start_time=start
        ).save()

    def test_callback_updates_sent_message_in_db(self):
        data = json.dumps({
            "message_id": "1234",
            "status": "delivered"
        })
        request = MockRequest(body=data)
        callback(request)

    def test_callback_creates_invalid_number_if_response_status_invalid(self):
        data = json.dumps({
            "message_id": "5678",
            "status": "invalid"
        })
        request = MockRequest(body=data)
        callback(request)
