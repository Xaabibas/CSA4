class ExternalDevice:
    DR: int = 0
    SR: int = 0 # младший бит - бит готовности, второй младший бит - запрос прерывания

    def read_data(self):
        self.SR = self.SR & 0xFFFFFFFC
        return self.DR

    def read_status(self):
        return self.SR

    def write_data(self, data: int):
        self.DR = data
        self.SR = self.SR | 0x00000001

    def request_interrupt(self):
        self.SR = self.SR | 0x00000003

class IOController:
    devices: {int: ExternalDevice}
    buffer: int
    IREQ: bool
    IPort: int = 0

    def __init__(self):
        self.devices = {}

    def register(self, port: int, device: ExternalDevice):
        self.devices[port] = device

    def in_(self, port: int, register: int): # if register == 0 then SR else DR
        self.buffer = self.devices[port].read_status() if register == 0 else self.devices[port].read_data()

    def out(self, port: int):
        self.devices[port].write_data(self.buffer)

    def check_interrupts(self):
        self.IREQ = False
        for port, device in self.devices.items():
            if device.SR & 0x2:
                self.IREQ = True
                self.IPort = port
                device.SR &= ~0x2
                break
