#!/usr/bin/env python
import sys
sys.path.append("./dnspython")
sys.path.append("./dnslib")
from dns import message, query, exception
#from dns import rdatatype, resolver
import time
import multiprocessing.pool
#import socket
#import argparse
import datetime
import threading
import traceback
import SocketServer
import dnslib
#from dnslib import *


#Constants
#http://pcsupport.about.com/od/tipstricks/a/free-public-dns-servers.htm
#http://www.tech-faq.com/public-dns-servers.html
#'223.5.5.5'
DNSlist = ['128.2.184.224', '8.8.8.8', '208.67.222.222', '209.244.0.3',\
           '8.26.56.26', '74.82.42.42', '151.197.0.38']
PORT = 53

# the record cache
cache = {}
# the worker threads

def fetch_from_resolver(dns_index_req):
    dns_index = dns_index_req[0]
    domain = dns_index_req[1]
    query_type = dns_index_req[2]
    queue = dns_index_req[3]
    print "Worker thread", dns_index, domain
    q = message.make_query(domain, query_type)
    rcode = q.rcode()
    count = 0
    while True and count < 3:
        try:
            msg = query.udp(q, DNSlist[dns_index], timeout=1)
        except exception.Timeout:
            count += 1
            continue
        break
    if count >= 3:
        print "Worker thread %d too many retries"%dns_index
        return ([], rcode)
    ips = []
    #print msg.answer
    answer = None
    for anss in msg.answer:
        #print "Type", rdatatype.to_text(anss.to_rdataset().rdtype)
        if anss.to_rdataset().rdtype == query_type: #match record type
            answer = anss
    if answer is None:
        print "Worker thread %d empty response"%dns_index
        return 1
    for ans in answer:
        ips.append(ans.to_text())
    print "Worker thread %d got answer"%dns_index
    queue.put((ips, rcode))
    print "Worker thread %d finished"%dns_index
    return 0

def refine(qname_str, qtype, answers):
    pass

def parallel_resolve(request, reply_callback):
    print "Parallel resolver"
    qname_str = str(request.q.qname)
    qtype = request.q.qtype
    manager = multiprocessing.Manager()
    queue = manager.Queue()

    # Fire parallel lookup
    dns_index_req = []
    for i in range(len(DNSlist)):
        dns_index_req.append((i, qname_str, qtype, queue))

    print "ready to lookup"
    waiting = p.map_async(fetch_from_resolver, dns_index_req)

    # get the first response, and reply to client
    print "waiting for first response"
    first_response = queue.get(block=True)
    print "got first response, replying"
    reply_query(first_response, request, reply_callback)

    # wait for the rest answers
    answers = [first_response]
    waiting.get(9999)
    print "all workers are finished"
    while not queue.empty():
        answers.append(queue.get(block=False))

    refine(qname_str, qtype, answers)

def dns_resolve(request, reply_callback):
    print "resolving"
    qname_str = str(request.q.qname)
    qtype = request.q.qtype
    if (qname_str, qtype) in cache:
        # cache hit
        print "cache hit"
        answer = cache[(qname_str, qtype)]
        reply_query(answer, request, reply_callback)
    else:
        # cache miss, query DNS resolvers
        parallel_resolve(request, reply_callback)


def reply_query(answer, request, reply_callback):
    DNS_response = prepare_reply(answer, request)
    reply_callback(DNS_response)


def prepare_reply(answer, request):
    #pack anwsers
    qname = request.q.qname
    qtype = request.q.qtype
    qt = dnslib.QTYPE[qtype]
    rcode = 0

    reply = dnslib.DNSRecord(\
                dnslib.DNSHeader(id=request.header.id, qr=1, aa=1, ra=1),\
                                 q=request.q)
    bad_reply = dnslib.DNSRecord(dnslib.DNSHeader(\
                            id=request.header.id, qr=1, aa=1, ra=1,\
                            rcode=rcode), q=request.q)

    record_class = getattr(dnslib, str(qt))
    empty_ans = True
    if rcode == 0:
        rcode = answer[1]
    for a in answer[0]:
        empty_ans = False
        reply.add_answer(dnslib.RR(rname=qname, rtype=qtype,\
                     rclass=1, ttl=10, rdata=record_class(a)))

    #print "---- Reply:\n", reply
    # if failed, send back error code
    if empty_ans and rcode > 0:
        reply = bad_reply

    return reply.pack()

def process_DNS_query(data, reply_callback):
    print "parsing DNS query"
    # parse the request
    request = dnslib.DNSRecord.parse(data)
    print request
    # lookup the record
    dns_resolve(request, reply_callback)



class BaseRequestHandler(SocketServer.BaseRequestHandler):

    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        print "\n\n%s request %s (%s %s):" % (self.__class__.__name__[:3],\
                     now, self.client_address[0], self.client_address[1])
        try:
            data = self.get_data()
            print len(data), data.encode('hex')
            # repr(data).replace('\\x', '')[1:-1]
            process_DNS_query(data, self.send_data)
            #self.send_data(dns_response(data))
        except Exception:
            traceback.print_exc(file=sys.stderr)


class TCPRequestHandler(BaseRequestHandler):

    def get_data(self):
        data = self.request.recv(8192)
        sz = int(data[:2].encode('hex'), 16)
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send_data(self, data):
        sz = hex(len(data))[2:].zfill(4).decode('hex')
        return self.request.sendall(sz + data)


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0]

    def send_data(self, data):
        return self.request[1].sendto(data, self.client_address)


def start_server():
    print "Starting nameserver..."

    servers = [
        SocketServer.ThreadingUDPServer(('', PORT), UDPRequestHandler),
        SocketServer.ThreadingTCPServer(('', PORT), TCPRequestHandler),
    ]
    for s in servers:
        thread = threading.Thread(target=s.serve_forever)
         # that thread will start one more thread for each request
        thread.daemon = True
        # exit the server thread when the main thread terminates
        thread.start()
        print "%s server loop running in thread: %s" %\
                    (s.RequestHandlerClass.__name__[:3], thread.name)
    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.shutdown()


if __name__ == '__main__':
    p = multiprocessing.Pool(30)
    start_server()
