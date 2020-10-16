from datetime import timedelta
import logging
import os

from django.db import models
from django.utils import timezone


logger = logging.getLogger(__name__)


class Server(models.Model):
    url = models.CharField(max_length=200)
    weight = models.DecimalField(max_digits=3, decimal_places=2)

    def rolling_latency(self, limit=1, window=5):
        dt = timezone.now() - timedelta(minutes=window)
        sent_messages = self.sentmessage_set.filter(start_time__gte=dt)[:limit]
        latencies = [sent_message.latency() for sent_message in sent_messages if sent_message.latency() != 0]
        if len(latencies) == 0:
            return 0
        return sum(latencies) / len(latencies)


class SentMessage(models.Model):
    uuid = models.CharField(max_length=200, null=True)
    number = models.CharField(max_length=200)
    status = models.CharField(max_length=200, null=True)
    start_time = models.DateTimeField('time started', null=True)
    end_time = models.DateTimeField('time finished', null=True)
    server = models.ForeignKey(Server, on_delete=models.CASCADE, null=True)

    def latency(self):
        """
        Returns in microseconds the duration from the start of a request through 
        the LoadBalancer to the receipt of the Callback from the third party. 
        """
        try:
            delta = self.end_time - self.start_time
            return delta / timedelta(microseconds=1)
        except Exception as e:
            logger.error(f"{e}")
            return 0

class InvalidNumber(models.Model):
    number = models.CharField(max_length=200)

