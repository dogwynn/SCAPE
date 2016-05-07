from __future__ import print_function
import getpass
import json
from time import sleep
import splunklib.client as client
import splunklib.results as results
import scape.registry as reg
import scape.splunk as scunk
import os

class FakeJobs(object):
    def create(self, query, **kwargs):
        return []

class FakeSplunk(object):
    @property
    def jobs(self):
        return FakeJobs()
    pass

reg = reg.Registry({
    'addc': scunk.SplunkDataSource(
        splunk_service=FakeSplunk(),
        metadata=reg.TableMetadata({
            'Source_Network_Address': { 'tags' : [ 'source'], 'dim': 'ip' },
            'Source_Port': { 'tags' : [ 'source'], 'dim': 'port' },
            'host': 'hostname:'
            }),
        index='addc')
    })

addc=reg['addc']
    
def test_select():
    addc.select('*').run()
    addc.select(max_count=40).check()