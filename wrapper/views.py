import json
import logging
import os

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from wrapper.load_balancer import LoadBalancer
from wrapper.models import InvalidNumber, SentMessage, Server


logger = logging.getLogger(__name__)


LB = LoadBalancer()


class SendView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SendView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        request_body = json.loads(request.body)

        if request_body["number"] in InvalidNumber.objects.values_list("number", flat=True):
            return JsonResponse({
                    "status": 400,
                    "message": "The number you have submitted has been marked invalid by our SMS providers."
                }, status=400)

        request_to_forward = {
            "to_number": request_body["number"],
            "message": request_body["message"],
            "callback_url": os.getenv('CALLBACK_URL'),
        }

        sm = SentMessage(
            number = request_body["number"],
            status = "pending",
            start_time = timezone.now(),
        )

        retry_count = 0
        response = None

        while retry_count < int(os.getenv('MAX_RETRY', '2')):
            try: 
                response = LB.request(request_to_forward, headers={"Content-Type": "application/json"})
                if response.status_code != 200:
                    print(response.status_code)
                    raise Exception(response.json()["message"])
                break
            except Exception as e:
                logger.error(f'The following exception occured:\n{e}')
                retry_count += 1

        if retry_count >= int(os.getenv('MAX_RETRY', '2')):
            sm.status = 'failed_to_send'
            return JsonResponse({
                "status": 502,
                "message": "Bad gateway. Failed to forward data. Max retries exceeded."
            }, status=502)

        sm.uuid = response.json()["message_id"]
        sm.server = Server.objects.filter(url=LB.targeted_url).first()


        sm.save()
        return JsonResponse({
            "status": 200,
            "message": "Data successfully forwarded."
        }, status=200)

class LBView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LBView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            request_body = json.loads(request.body)
            LB.set_strat(request_body["strategy"])

            response_body = {
                "status": 200,
                "message": "Load Balancer strategy successfully updated."
            }
            return JsonResponse(response_body, status=200)
        except Exception as e:
            logger.error(f'The following exception occured:\n{e}')
            return JsonResponse({
                "status": 500,
                "message": "An error occurred while handling your request."
            }, status=500)

class CallbackView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        print("dispatching")
        return super(CallbackView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        print("handling post")
        try:
            print(request.body)
            request_body = json.loads(request.body)

            print(request_body)

            sm = SentMessage.objects.filter(uuid=request_body["message_id"])[0]
            end_time = timezone.now()

            if request_body["status"] == "invalid":
                InvalidNumber(number=sm.number).save()

            sm.end_time = end_time
            sm.status = request_body["status"]
            sm.save()
            return JsonResponse({
                "status": 200,
                "message": "Data ingested."
            })
        except Exception as e:
            logger.error(f'The following exception occured:\n{e}')
            raise e



class ListMessageView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ListMessageView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        messages = list(SentMessage.objects.values())
        return JsonResponse({'data': messages})


