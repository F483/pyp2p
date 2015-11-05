from unittest import TestCase
from pyp2p.sock import *
from pyp2p.net import rendezvous_servers
import time
import sys


class test_sock(TestCase):
    def test_blocking_timeout(self):
        s = Sock(rendezvous_servers[0]["addr"], rendezvous_servers[0]["port"], blocking=1)
        t = time.time()
        s.recv_line(timeout=1)
        if time.time() - t >= 4:
            print("Manual timeout failed.")
            assert(0)
        s.close()

    def test_non_blocking_timeout(self):
        s = Sock(rendezvous_servers[0]["addr"], rendezvous_servers[0]["port"], blocking=0)
        assert(s.recv_line() == u"")
        assert(s.recv(1) == u"")
        s.close()

    def test_encoding(self):
        s = Sock(rendezvous_servers[0]["addr"], rendezvous_servers[0]["port"], blocking=1)
        s.send_line("SOURCE TCP 50")
        ret = s.recv(1, encoding="ascii")
        if sys.version_info >= (3,0,0):
            assert(type(ret) == bytes)
        else:
            assert(type(ret) == str)
        assert(ret == b"R")
        ret = s.recv_line()
        assert(u"EMOTE" in ret)
        s.close()

    def test_recv_recvline_switch(self):
        s = Sock(rendezvous_servers[0]["addr"], rendezvous_servers[0]["port"], blocking=1)
        s.send_line("SOURCE TCP 32")
        ret = s.recv(1)
        assert(ret[0] == u"R")
        assert(not len(s.buf))
        s.buf = u"test"
        ret = s.recv(1)
        assert(ret[0] == u"E")
        assert(s.buf == u"test")
        s.buf = junk = u"example\r\nxsfsdf"
        s.send_line("SOURCE TCP 50")
        ret = s.recv_line()
        assert("MOTE" in ret)
        assert(s.buf == junk)
        ret = s.recv_line()
        assert("REMOTE" in ret)
        assert(s.buf == junk)
        s.close()

    def test_0000001_sock(self):
        s = Sock(rendezvous_servers[0]["addr"], rendezvous_servers[0]["port"],
                 blocking=1)
        assert (s.connected)
        s.send_line("SOURCE TCP 323")
        assert (s.connected)
        line = s.recv_line()
        assert ("REMOTE" in line)

        s = Sock("www.example.com", 80, blocking=0)
        data = "GET / HTTP/1.1\r\n"
        data += "Connection: close\r\n"
        data += "Host: www.example.com\r\n\r\n"
        s.send(data)
        time.sleep(1)
        replies = ""
        for reply in s:
            # Output should be unicode.
            if sys.version_info >= (3, 0, 0):
                assert (type(reply) == str)
            else:
                assert (type(reply) == unicode)

            replies += reply
            print(reply)

        assert (s.connected != 1)
        assert (replies != "")

        s.close()
        s.reconnect()
        s.close()

        s = Sock("www.example.com", 80, blocking=1, timeout=5)
        s.send_line("GET / HTTP/1.1")
        s.send_line("Host: www.example.com\r\n")
        line = s.recv_line()
        print(line)
        print(type(line))
        print(s.buf)
        print(type(s.buf))
        assert (line, "HTTP/1.1 200 OK")
        if sys.version_info >= (3, 0, 0):
            assert (type(line) == str)
        else:
            assert (type(line) == unicode)
        s.close()

        s = Sock()
        s.buf = "\r\nx\r\n"
        x = s.parse_buf()
        assert (x[0] == "x")

        s.buf = "\r\n"
        x = s.parse_buf()
        assert (x == [])

        s.buf = "\r\n\r\n"
        x = s.parse_buf()
        assert (x == [])

        s.buf = "\r\r\n\r\n"
        x = s.parse_buf()
        assert (x[0] == "\r")

        s.buf = "\r\n\r\n\r\nx"
        x = s.parse_buf()
        assert (x == [])

        s.buf = "\r\n\r\nx\r\nsdfsdfsdf\r\n"
        x = s.parse_buf()
        assert (x[0] == "x" and x[1] == "sdfsdfsdf")

        s.buf = "sdfsdfsdf\r\n"
        s.parse_buf()
        s.buf += "abc\r\n"
        x = s.parse_buf()
        assert (x[0] == "abc")

        s.buf += "\r\ns\r\n"
        x = s.parse_buf()
        assert (x[0] == "s")

        s.buf = "reply 1\r\nreply 2\r\n"
        s.replies = []
        s.update()
        assert (s.pop_reply(), "reply 1")
        assert (s.replies[0], "reply 2")
