import os
import random
import requests

from wrapper.models import Server

class LoadBalancer:
    strategies = ['weighted_random', 'rolling_avg', 'round_robin']
    index = 0


    def __init__(self, strategy=None):
        strategy = strategy or os.getenv('LB_STRAT', 'weighted_random')
        self.set_strat(strategy)
        self.targeted_url = None

    @property
    def targets(self):
        return Server.objects.all()

    def set_strat(self, strategy=None):
        if strategy and strategy in self.strategies:
            self.strategy = strategy

    def request(self, data, headers=None):
        headers = {} if not headers else headers
        getattr(self, f"_{self.strategy}")()
        return requests.post(self.targeted_url, headers=headers, json=data)

    # private
            
    def _weighted_random(self):
        serv_list = []
        for server in  self.targets:
            weight = int(server.weight * 100)
            weight_as_list = [server.url for i in range(weight)]
            serv_list.extend(weight_as_list)
        self.targeted_url = random.choice(serv_list)

    def _rolling_avg(self):
        servers = self.targets
        sorted(servers, key=lambda x: x.rolling_latency(limit=5))
        self.targeted_url = servers[0].url

    def _round_robin(self):
        try:
            server = self.targets[self.index]
            self.index += 1
        except IndexError:
            self.index = 0
            server = self.targets[self.index]
        self.targeted_url = server.url
