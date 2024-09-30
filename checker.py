import subprocess
import telnetlib
import socket
import time
import shutil
import sys
import os
import errno
from argparse import ArgumentParser

timeout = 0.2
source = ["Makefile", "server.c", "server.h"]
executable = ["read_server", "write_server"]
testpath = "testcases"
parser = ArgumentParser()
parser.add_argument("-t", "--task", choices=["1-1", "1-2", "1-3", "1-4", "2-1", "2-2", "3", "4"], nargs="+")
args = parser.parse_args()

class ResponseChecker():
    def __init__(self):
        self.BANNER = 0
        self.LOCK = 1
        self.EXIT = 2
        self.CANCEL = 3
        self.FULL = 4
        self.BOOKED = 5
        self.NOPAID = 6
        self.SUCCESS = 7
        self.INVALID = 8
        self.CHECK = 9
        self.BOOK = 10
        self.SEAT = 11
        self.CONT = 12
        self.response = [
            [ 
            "======================================",
            " Welcome to CSIE Train Booking System ",
            "======================================"
            ],
            ">>> Locked.",
            ">>> Client exit.",
            ">>> You cancel the seat.",
            ">>> The shift is fully booked.",
            ">>> The seat is booked.",
            ">>> No seat to pay.",
            ">>> Your train booking is successful.",
            ">>> Invalid operation.",
            "Please select the shift you want to check [902001-902005]: ",
            "Please select the shift you want to book [902001-902005]: ",
            "Select the seat [1-40] or type \"pay\" to confirm: ",
            "Type \"seat\" to continue or \"exit\" to quit [seat/exit]: ",    
        ]

    def check_banner(self, res: str, start: int, end: int, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        msg = [s.strip('\n') for s in msg]
        return len(msg) >= 3 and msg[start:end] == self.response[self.BANNER]

    def check_lock(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.LOCK]

    def check_exit(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.EXIT]

    def check_full(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.FULL]

    def check_booked(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.BOOKED]

    def check_nopaid(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.NOPAID]

    def check_success(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.SUCCESS]

    def check_invalid(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.INVALID]

    def check_check(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.CHECK]

    def check_book(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.BOOK]

    def check_seat(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.SEAT]

    def check_cont(self, res: str, idx=0, delimeter='\n'):
        if not res:
            return False
        
        msg = res.split(delimeter)
        return len(msg) > idx and msg[idx].strip('\n') == self.response[self.CONT]
        
class Checker():
    def __init__(self):
        self.score = 0
        self.punishment = 0
        self.fullscore = sum(scores)
        self.io = sys.stderr

    def file_miss(self, files):
        return len(set(files) - set(os.listdir(".")))

    def remove_file(self, files):
        for f in files:
            os.system(f"rm -rf {f}")

    def compile(self):
        ret = os.system("make 1>/dev/null 2>/dev/null")
        if ret != 0 or self.file_miss(executable):
            return False
        return True
        
    def makeclean(self):
        ret = os.system("make clean 1>/dev/null 2>/dev/null")
        if ret != 0 or self.file_miss(executable)!=len(executable):
            self.remove_file(executable)
            return False
        return True

    def run(self):
        print("Checking file format ...", file=self.io)
        if self.file_miss(source):
            print("File not found", file=self.io)
            exit()

        if self.file_miss(executable) != len(executable):
            self.punishment += 0.25
            red("Find executable files", self.io)
            self.remove_file(executable)

        print("Compiling source code ...", file=self.io)
        if not self.compile():
            print("Compiled Error", file=self.io)
            exit()

        print("Testing make clean command ...", file=self.io)
        if not self.makeclean():
            self.punishment += 0.25
            print("Make clean failed", file=self.io)

        self.compile()
        for t in testcases:
            self.score += t(self.io)
        
        self.remove_file(executable)

        self.score = max(0, self.score-self.punishment)
        print(f"Final score: {round(self.score,2)} / {self.fullscore}", file=self.io)

class TelnetClient(telnetlib.Telnet):
    
    def __init__(self, port, server_type = 0):
        self.log = ""
        self.response = ""
        self.server_type = server_type
        self.checker = ResponseChecker()
        self.pos = 0
        self.ret = 0
        super().__init__("127.0.0.1", port)
        time.sleep(timeout)

    def handle_read(self, delimeter=b"\n", timeout=0.5):
        try:
            self.response = super().read_until(delimeter, timeout).decode()
            if self.response:
                self.log += self.response
                if self.response.endswith(delimeter.decode()):
                    return 0
                else:
                    return 4 # timeout
            else:
                return 2    # no message read         
        except EOFError:
            return 2 # EOF (connection closed)
        except Exception as e:
            raise e
    
    def read_all(self, add_to_log=False, timeout=0.5):
        try:
            self.response = super().read_until(b"Please don't bypass", timeout).decode()
            if self.response and add_to_log:
                self.log += self.response
                return 0
            else:
                return 1
        except EOFError:
            return 2 #EOF (connection closed)
        except Exception as e:
            raise e
    
    def handle_write(self, buf):
        try:
            super().write(buf)
            return 0
        except IOError as e:
            if e.errno == errno.EPIPE:
                return 2
            else:
                raise e
        except Exception as e:
            raise e

    def handle_EOF(self, inputs, check):
        
        if (check or self.read_all(add_to_log=True) == 0) and \
           self.check_connection() == 2 and \
           self.checker.check_invalid(self.log, idx=-1, delimeter=": "):
            self.pos = inputs.tell()
            return 1
        else:
            return 2

    def inputfile(self, filename, offset=0, check=True):
        # 0: continue, 1: exit, 2: connection closed, 3: switch, 4: timeout, 5: record
        inputs = open(filename, "r")
        inputs.seek(offset)

        try:
            self.pos = -1
            # read server
            if self.server_type == 0:
                while True:
                    line = inputs.readline()
                    if not check: # try to sleep if no check output
                        time.sleep(0.01)
                    if not line:
                        break
                    elif line.strip() in [f"90200{i}" for i in range(1, 6)]:
                        self.ret = self.trainID(line, check)
                    elif line == "------\n":
                        self.pos = inputs.tell()
                        self.ret = 3
                    elif line == "exit\n":
                        self.pos = inputs.tell()
                        self.ret = self.exit()
                    else:
                        self.ret = self.invalid(line)
                    
                    if self.ret > 0:
                        break
            # write server
            elif self.server_type == 1:
                while True:
                    line = inputs.readline()
                    if not check:
                        time.sleep(0.01)
                    if not line:
                        break
                    elif line.strip() in [f"90200{i}" for i in range(1, 6)]:
                        self.ret = self.trainID(line, check)
                    elif line.strip() in [f"{i}" for i in range(1, 41)]:
                        self.ret = self.seatID(line, check)
                    elif line == "seat\n":
                        self.ret = self.seat(check)
                    elif line == "pay1\n":
                        self.ret = self.pay1(check)
                    elif line == "pay2\n":
                        self.ret = self.pay2(check)
                    elif line == "------\n":
                        self.pos = inputs.tell()
                        self.ret = 3
                    elif line == "file\n":
                        self.pos = inputs.tell()
                        self.ret = 5
                    elif line == "exit\n":
                        self.pos = inputs.tell()
                        self.ret = self.exit()
                    elif line == "======\n":
                        self.ret = self.handle_EOF(inputs, check)
                    else:
                        self.ret = self.invalid(line)

                    if self.ret == 4:
                        if inputs.readline() == "======\n":
                            self.ret = self.handle_EOF(inputs, check)
                        else:
                            self.ret = 2

                    if self.ret > 0:
                        break

            return self.ret
        except Exception as e:
            print(f"Unknown Error: {e}")
            raise e

    def check_banner(self, check=True, timeout=0.5):
        
        if not check:
            return True

        ret = self.handle_read(delimeter=b": ", timeout=timeout)
        if ret == 2 or ret == 1:
            return False
        else:
            if self.server_type == 0:
                return self.checker.check_banner(self.response, 0, 3) and \
                    self.checker.check_check(self.response, 3)
            elif self.server_type == 1:
                return self.checker.check_banner(self.response, 0, 3) and \
                    self.checker.check_book(self.response, 3)
    
    def check_connection(self):
        return self.read_all()

    def trainID(self, buffer, check):
        
        ret = self.handle_write(buffer.encode())
        if ret == 2:
            return ret
        
        if check:
            if self.server_type == 0:
                return self.handle_read(delimeter=b"[902001-902005]: ")
            elif self.server_type == 1:
                ret = self.handle_read(delimeter=b"confirm: ")
                if ret == 4:
                    return 0 if self.checker.check_full(self.response, 0) and self.checker.check_book(self.response, 1) else 2
                else:
                    return ret
        return 0

    def seatID(self, buffer, check):
        ret = self.handle_write(buffer.encode())
        if ret == 2:
            return ret
        
        return 0 if not check else self.handle_read(delimeter=b"confirm: ")

    def seat(self, check):
        ret = self.handle_write(b"seat\n")
        if ret == 2:
            return ret
        return 0 if not check else self.handle_read(delimeter=b"confirm: ")

    def pay1(self, check):
        ret = self.handle_write(b"pay\n")
        if ret == 2:
            return ret
        return 0 if not check else self.handle_read(delimeter=b"[seat/exit]: ")
        
    def pay2(self, check):
        ret = self.handle_write(b"pay\n")
        if ret == 2:
            return ret
        return 0 if not check else self.handle_read(delimeter=b"confirm: ")
        
    def exit(self):
        # This should not happen, it means when sending "exit" or read response,
        # the connection is being closed by server
        if self.handle_write(b"exit\n") == 2 or \
            self.read_all(add_to_log=True, timeout=0.2) == 2:
            return 2
        return 1 if self.check_connection() == 2 else 2

    def invalid(self, buffer):
        return self.handle_write(buffer.encode())
    
    def clean_log(self):
        self.log = ""

class Read_server():
    def __init__(self, port):
        # self.log = ""
        self.p = subprocess.Popen(["./read_server", str(port)], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
        time.sleep(timeout)

    def exit(self):
        try:
            self.p.terminate()
            # self.log = self.p.communicate(timeout=timeout)[0].decode()
            # print(self.log)
            return 
        except Exception as e:
            self.p.kill()
            self.p.wait()
            raise Exception(f"Read server exit {e}")

class Write_server():
    def __init__(self, port):
        # self.log = ""
        self.p = subprocess.Popen(["./write_server", str(port)], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
        time.sleep(timeout)

    def exit(self):
        try:
            self.p.terminate()
            # self.log = self.p.communicate(timeout=timeout)[0].decode()
            # print(self.log)
            return 
        except Exception as e:
            self.p.kill()
            self.p.wait()
            raise Exception(f"Write server exit {e}")
        
def bold(str_, io):
    print("\33[1m" + str_ + "\33[0m", file=io)

def red(str_, io):
    print("\33[31m" + str_ + "\33[0m", file=io)

def green(str_, io):
    print("\33[32m" + str_ + "\33[0m", file=io)

def cyan(str_, io):
    print("\33[36m" + str_ + "\33[0m", file=io)

def yellow(str_, io):
    print("\33[33m" + str_ + "\33[0m", file=io)

def find_empty_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    _, port = s.getsockname()
    s.close()
    return port

def compare(contentA, B):
    with open(B, "r") as record:
        contentB = record.read()
    return contentA == contentB

def get_record(file):

    try:
        with open(file, "r") as f:
            rec = f.read()
            return rec

    except FileNotFoundError:
        print("File not found.")
        return None

def copy_record(testcase:str, id: int):
    shutil.copy2(f"{testpath}/{testcase}/train_{id}", f"./csie_trains/train_{id}")
    

def testcase1_1(io):
    try:
        cyan("===== Testcase 1-1: Basic operations: Shift ID in read server =====", io)
        time.sleep(timeout)
        port = find_empty_port()
        r_server = Read_server(port)
        client = TelnetClient(port, server_type=0)
        
        #---------------------------------------------------------
        if client.inputfile(f"{testpath}/testcase1/1-1-shift.in", check=False) == 2:
            raise Exception("Connection Unexpected Closed")
        if client.read_all() == 2:
            raise Exception("Connection Unexpected Closed")
        if client.inputfile(f"{testpath}/testcase1/exit.in") == 2:
            raise Exception("Connection Unexpected Closed")
        if not ResponseChecker().check_exit(client.log):
            raise Exception("Wrong Answer")
        #---------------------------------------------------------
        
        r_server.exit()
        green("Testcase 1-1: passed", io)

        return 0.1
    except Exception as e:
        red("Testcase 1-1: failed", io)
        return 0

def testcase1_2(io):
    try:
        cyan("===== Testcase 1-2: Basic operations: Seat ID in write server =====", io)
        time.sleep(timeout)
        port = find_empty_port()
        w_server = Write_server(port)
        client = TelnetClient(port, server_type=1)
        
        #---------------------------------------------------------
        if client.inputfile(f"{testpath}/testcase1/1-2-seat.in", check=False) == 2:
            raise Exception("Connection Unexpected Closed")
        if client.read_all() == 2:
            raise Exception("Connection Unexpected Closed")
        if client.inputfile(f"{testpath}/testcase1/exit.in") == 2:
            raise Exception("Connection Unexpected Closed")
        if not ResponseChecker().check_exit(client.log):
            raise Exception("WA")
        #---------------------------------------------------------

        w_server.exit()
        green("Testcase 1-2: passed", io)
        return 0.1
    except Exception as e:
        red("Testcase 1-2: failed", io)
        return 0

def testcase1_3(io):
    try:
        cyan("===== Testcase 1-3: Basic operations: pay/seat in write server =====", io)
        time.sleep(timeout)
        copy_record("testcase1", 902001)
        port = find_empty_port()
        w_server = Write_server(port)
        client = TelnetClient(port, server_type=1)
        
        #---------------------------------------------------------
        if client.inputfile(f"{testpath}/testcase1/1-3-all.in", check=False) == 2:
            raise Exception("Connection Unexpected Closed")
        if client.read_all() == 2:
            raise Exception("Connection Unexpected Closed")
        if client.inputfile(f"{testpath}/testcase1/exit.in") == 2:
            raise Exception("Connection Unexpected Closed")
        if not ResponseChecker().check_exit(client.log):
            raise Exception("WA")
        #---------------------------------------------------------
        
        w_server.exit()
        green("Testcase 1-3: passed", io)
        return 0.1
    except Exception as e:
        red("Testcase 1-3: failed", io)
        return 0

def testcase1_4(io):
    try:
        cyan("===== Testcase 1-4: Basic operations: invalid operation =====", io)
        time.sleep(timeout)
        copy_record("testcase1", 902001)
        port = find_empty_port()
        w_server = Write_server(port)
        #---------------------------------------------------------
        pos = 0
        for i in range(10):
            client = TelnetClient(port, server_type=1)
            if client.inputfile(f"{testpath}/testcase1/1-4-invalid.in", offset=pos, check=False) != 1:
                raise Exception("Not close connection")
            pos = client.pos
        #---------------------------------------------------------
        w_server.exit()
        green("Testcase 1-4: passed", io)
        return 0.2
    except Exception as e:
        red("Testcase 1-4: failed", io)
        return 0

def testcase2_1(io):
    try:
        cyan("===== Testcase 2-1: Read server =====", io)
        time.sleep(timeout)
        for i in range(902001, 902006):
            copy_record("testcase2-1", i)

        port = find_empty_port()
        r_server = Read_server(port)
        client = TelnetClient(port, server_type=0)

        #---------------------------------------------------------
        if not client.check_banner():
            raise 
        client.inputfile(f"{testpath}/testcase2-1/2-1.in")
        # 1 server, serialize, don't need cross-checking
        assert compare(client.log, f"{testpath}/testcase2-1/2-1.out")
        r_server.exit()
        green("Testcase 2-1: passed", io)
        return 0.2
    except Exception as e:
        red("Testcase 2-1: failed", io)
        return 0
    
def testcase2_2(io):
        cyan("===== Testcase 2-2: Write server =====", io)
        time.sleep(timeout)
        port = find_empty_port()
        w_server = Write_server(port)
        # 1 server, serialize, don't need cross-checking
        sub_cases = [
            {"name": "1.simple", "input": f"{testpath}/testcase2-2/1-simple.in", "expected": f"{testpath}/testcase2-2/1-simple.out", "score": 0.05},
            {"name": "2.fullshift", "input": f"{testpath}/testcase2-2/2-full.in", "expected": f"{testpath}/testcase2-2/2-full.out", "score": 0.05},
            {"name": "3.multiseat", "input": f"{testpath}/testcase2-2/3-multiseat.in", "expected": f"{testpath}/testcase2-2/3-multiseat.out", "score": 0.05},
            {"name": "4.cancellation", "input": f"{testpath}/testcase2-2/4-cancel.in", "expected": f"{testpath}/testcase2-2/4-cancel.out", "score": 0.05},
            {"name": "5.chose booked", "input": f"{testpath}/testcase2-2/5-booked.in", "expected": f"{testpath}/testcase2-2/5-booked.out", "score": 0.05},
            {"name": "6.chose & paid & chose", "input": f"{testpath}/testcase2-2/6-continue.in", "expected": f"{testpath}/testcase2-2/6-continue.out", "score": 0.05},
            {"name": "7.hard", "input": f"{testpath}/testcase2-2/7-hard.in", "expected": f"{testpath}/testcase2-2/7-hard.out", "score": 0.1},
            {"name": "8.hard-2", "input": f"{testpath}/testcase2-2/8-hard2.in", "expected": f"{testpath}/testcase2-2/8-hard2.out", "score": 0.1}
        ]

        total_score = 0
        max_score = 0.5
        for s in sub_cases:
            try:
                # 1 server, serialize, don't need cross-checking
                for j in range(902001, 902006):
                    copy_record("testcase2-2", j)
                client = TelnetClient(port, server_type=1)
                if not client.check_banner():
                    raise Exception("Banner Failed")
                if client.inputfile(s["input"]) == 2:
                    raise Exception("Connection Unexpected Closed")
                assert compare(client.log, s["expected"])
                yellow(f'|- Subcase {s["name"]} passed', io)
                total_score += s["score"]
            except Exception as e:
                red(f'|- Subcase {s["name"]}: failed', io)
                
        w_server.exit()
        if total_score == max_score:
            green("Testcase 2-2: passed", io)
        else:
            red(f"Testcase 2-2: failed {round(total_score,2)}/{max_score}", io)
        
        return total_score

def testcase3(io):
        cyan("===== Testcase 3: Write and Read server each have one client =====", io)
        time.sleep(timeout)
        r_port = find_empty_port()
        r_server = Read_server(r_port)
        w_port = find_empty_port()
        w_server = Write_server(w_port)

        sub_cases = [
            {
                "name": "1.cancellation",
                "input": f"{testpath}/testcase3/1-cancel.in",
                "record": [f"{testpath}/testcase3/1-cancel-file.out", f"./csie_trains/train_902001"],
                "expected": [f"{testpath}/testcase3/1-cancel-1.out", f"{testpath}/testcase3/1-cancel-2.out"],
                "score": 0.1
            },
            {
                "name": "2.payment",
                "input": f"{testpath}/testcase3/2-pay.in",
                "record": [f"{testpath}/testcase3/2-pay-file.out", f"./csie_trains/train_902003"],
                "expected": [f"{testpath}/testcase3/2-pay-1.out", f"{testpath}/testcase3/2-pay-2.out"],
                "score": 0.1
            },
            {
                "name": "3.mix",
                "input": f"{testpath}/testcase3/3-mix.in",
                "record": [f"{testpath}/testcase3/3-mix-file.out", f"./csie_trains/train_902004"],
                "expected": [f"{testpath}/testcase3/3-mix-1.out", f"{testpath}/testcase3/3-mix-2.out"],
                "score": 0.2
            }
        ]
        
        total_score = 0
        max_score = 0.4

        for s in sub_cases:
            try:
                # 2 server, we need cross-checking
                for j in range(902001, 902006):
                    copy_record("testcase3", j)
                rec = get_record(s["record"][0]).split('======\n')
                clientR = TelnetClient(r_port, server_type=0)
                clientW = TelnetClient(w_port, server_type=1)
                if not clientW.check_banner() or not clientR.check_banner():
                    raise Exception("Banner Failed")
                
                w = True
                off = 0
                idx = 0                
                while True:
                    if off != -1 and w: 
                        ret1 = clientW.inputfile(s["input"], offset=off)
                        if ret1 == 2:
                            raise Exception("Connection Unexpected Closed")
                        off = clientW.pos
                        
                        if ret1 == 5:
                            assert compare(rec[idx], s["record"][1])
                            idx+=1
                        else:
                            w = False
                    elif off != -1 and not w:
                        ret2 = clientR.inputfile(s["input"], offset=off)
                        if ret2 == 2:
                            raise Exception("Connection Unexpected Closed")
                        off = clientR.pos
                        w = True
                    
                    if ret1 == 1 and ret2 == 1:
                        break
                        
                assert compare(clientW.log, s["expected"][0])
                assert compare(clientR.log, s["expected"][1])
                yellow(f'|- Subcase {s["name"]} passed', io)
                total_score += s["score"]
            except Exception as e:
                red(f'|- Subcase {s["name"]}: failed', io)
                
        w_server.exit()
        r_server.exit()
        if total_score == max_score:
            green("Testcase 3: passed", io)
        else:
            red(f"Testcase 3: failed {round(total_score,2)}/{max_score}", io)
        
        return total_score

def testcase4(io):
        cyan("===== Testcase 4: 2 clients connect to 1 write server =====", io)
        time.sleep(timeout)
        port = find_empty_port()
        w_server = Write_server(port)

        sub_cases = [
            {
                "name" : "1.cancellation",
                "input": f"{testpath}/testcase4/1-cancel.in",
                "record": [f"{testpath}/testcase4/1-cancel-file.out", f"./csie_trains/train_902001"],
                "expected": [f"{testpath}/testcase4/1-cancel-1.out", f"{testpath}/testcase4/1-cancel-2.out"],
                "score": 0.1
            },
            {
                "name" : "2.payment",
                "input": f"{testpath}/testcase4/2-pay.in",
                "record": [f"{testpath}/testcase4/2-pay-file.out", f"./csie_trains/train_902001"],
                "expected": [f"{testpath}/testcase4/2-pay-1.out", f"{testpath}/testcase4/2-pay-2.out"],
                "score": 0.1
            },
            {
                "name" : "3.mix",
                "input": f"{testpath}/testcase4/3-mix.in",
                "record": [f"{testpath}/testcase4/3-mix-file.out", f"./csie_trains/train_902003"],
                "expected": [f"{testpath}/testcase4/3-mix-1.out", f"{testpath}/testcase4/3-mix-2.out", f"{testpath}/testcase4/3-mix-3.out"],
                "score": 0.2
            }
        ]
        
        total_score = 0
        max_score = 0.4

        try:
            for j in range(902001, 902006):
                copy_record("testcase4", j)
            rec = get_record(sub_cases[0]["record"][0]).split("======\n")
            clientW1 = TelnetClient(port, server_type=1)
            clientW2 = TelnetClient(port, server_type=1)
            if not clientW1.check_banner() or not clientW2.check_banner():
                raise Exception("Banner Failed")
            
            idx = 0
            off = 0
            w = 1    
            while True:
                if w == 1:
                    ret1 = clientW1.inputfile(sub_cases[0]["input"], offset=off)
                    if ret1 == 2:
                        raise Exception("Connection Unexpected Closed")
                    off = clientW1.pos
                    if ret1 == 5:
                        assert compare(rec[idx], sub_cases[0]["record"][1])
                        idx+=1
                        continue
                    w = 2
                    if ret1 == 1 and ret2 == 1:
                        break
                else:
                    ret2 = clientW2.inputfile(sub_cases[0]["input"], offset=off)
                    if ret2 == 2:
                        raise Exception("Connection Unexpected Closed")
                    
                    off = clientW2.pos
                    if ret2 == 5:
                        assert compare(rec[idx], sub_cases[0]["record"][1])
                        idx+=1
                        continue
                    w = 1

                    if ret1 == 1 and ret2 == 1:
                        break
            assert compare(clientW1.log, sub_cases[0]["expected"][0])
            assert compare(clientW2.log, sub_cases[0]["expected"][1])

            yellow(f'|- Subcase {sub_cases[0]["name"]} passed', io)
            total_score += sub_cases[0]["score"]
        except Exception as e:
            red(f'|- Subcase {sub_cases[0]["name"]}: failed', io)
        
        try:
            for j in range(902001, 902006):
                copy_record("testcase4", j)
            rec = get_record(sub_cases[1]["record"][0]).split("======\n")
            clientW1 = TelnetClient(port, server_type=1)
            clientW2 = TelnetClient(port, server_type=1)
            if not clientW1.check_banner() or not clientW2.check_banner():
                raise Exception("Banner Failed")

            idx = 0
            off = 0
            w = 1    
            while True:
                if w == 1:
                    ret1 = clientW1.inputfile(sub_cases[1]["input"], offset=off)
                    if ret1 == 2:
                        raise Exception("Connection Unexpected Closed")
                    off = clientW1.pos
                    if ret1 == 5:
                        assert compare(rec[idx], sub_cases[1]["record"][1])
                        idx+=1
                        continue
                    w = 2
                    if ret1 == 1 and ret2 == 1:
                        break
                else:
                    ret2 = clientW2.inputfile(sub_cases[1]["input"], offset=off)
                    if ret2 == 2:
                        raise Exception("Connection Unexpected Closed")
                    
                    off = clientW2.pos
                    if ret2 == 5:
                        assert compare(rec[idx], sub_cases[1]["record"][1])
                        idx+=1
                        continue
                    w = 1

                    if ret1 == 1 and ret2 == 1:
                        break
                
            assert compare(clientW1.log, sub_cases[1]["expected"][0])
            assert compare(clientW2.log, sub_cases[1]["expected"][1])

            yellow(f'|- Subcase {sub_cases[1]["name"]} passed', io)
            total_score += sub_cases[1]["score"]
        except Exception as e:
            red(f'|- Subcase {sub_cases[1]["name"]}: failed', io)

        try:
            for j in range(902001, 902006):
                copy_record("testcase4", j)
            rec = get_record(sub_cases[2]["record"][0]).split("======\n")
            clientW1 = TelnetClient(port, server_type=1)
            clientW2 = TelnetClient(port, server_type=1)
            clientW3 = TelnetClient(port, server_type=1)
            if not clientW1.check_banner() or not clientW2.check_banner() or not clientW3.check_banner():
                raise Exception("Banner Failed")

            idx = 0
            off = 0
            w = 1    
            for _ in range(13):
                if w == 1:
                    ret1 = clientW1.inputfile(sub_cases[2]["input"], offset=off)
                    if ret1 == 2:
                        raise Exception("Connection Unexpected Closed")
                    off = clientW1.pos
                    if ret1 == 5:
                        assert compare(rec[idx], sub_cases[2]["record"][1])
                        idx+=1
                        continue
                    w = 2
                else:
                    ret2 = clientW2.inputfile(sub_cases[2]["input"], offset=off)
                    if ret2 == 2:
                        raise Exception("Connection Unexpected Closed")
                    
                    off = clientW2.pos
                    if ret2 == 5:
                        assert compare(rec[idx], sub_cases[2]["record"][1])
                        idx+=1
                        continue
                    w = 1
            
            ret1 = clientW1.inputfile(sub_cases[2]["input"], offset=off)
            if ret1 == 2:
                raise Exception("Connection Unexpected Closed")
            
            ret3 = clientW3.inputfile(sub_cases[2]["input"], offset=clientW1.pos)
            if ret3 == 2:
                raise Exception("Connection Unexpected Closed")
            if ret2 == 5:
                assert compare(rec[idx], sub_cases[2]["record"][1])
                idx+=1

            ret3 = clientW3.inputfile(sub_cases[2]["input"], offset=clientW3.pos)
            if ret3 == 2:
                raise Exception("Connection Unexpected Closed")

            ret2 = clientW2.inputfile(sub_cases[2]["input"], offset=clientW3.pos)
            if ret2 == 2:
                raise Exception("Connection Unexpected Closed")

            if ret1 != 1 or ret2 != 1 or ret3 != 1:
                raise Exception("Client does not exit")
                
            assert compare(clientW1.log, sub_cases[2]["expected"][0])
            assert compare(clientW2.log, sub_cases[2]["expected"][1])
            assert compare(clientW3.log, sub_cases[2]["expected"][2])

            yellow(f'|- Subcase {sub_cases[2]["name"]} passed', io)
            total_score += sub_cases[2]["score"]
        except Exception as e:
            red(f'|- Subcase {sub_cases[2]["name"]}: failed', io)

        w_server.exit()
        if total_score == max_score:
            green("Testcase 4: passed", io)
        else:
            red(f"Testcase 4: failed {round(total_score,2)}/{max_score}", io)
        
        return total_score

if __name__ == '__main__':
    testcases = [testcase1_1,testcase1_2, testcase1_3, testcase1_4, testcase2_1, testcase2_2, testcase3, testcase4]
    scores = [0.1, 0.1, 0.1, 0.2, 0.2, 0.5, 0.4, 0.4]
    index = {"1-1":0, "1-2": 1, "1-3": 2, "1-4": 3, "2-1": 4, "2-2": 5, "3": 6, "4": 7}
    if args.task is not None:
        task = []
        for t in args.task:
            task.append(index[t])
        task.sort()
        testcases = [testcases[i] for i in task]
        scores = [scores[i] for i in task]
    Checker().run()
