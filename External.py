class ExternalDevice:
    DR: int = 2
    SR: int = 0 # младший бит - бит готовности, второй младший бит - запрос прерывания
    buffer: []

    schedule: [(int, str)]

    def __init__(self, schedule=None):
        self.buffer = []
        self.schedule = schedule

    def read_data(self):
        self.SR = self.SR & 0xFFFFFFFC
        return self.DR

    def read_status(self):
        return self.SR

    def write_data(self, data: int):
        self.DR = data
        self.buffer.append(chr(data))

    def request_interrupt(self):
        self.SR = self.SR | 0x00000003

    def update(self, now):
        if self.schedule is None or len(self.schedule) == 0:
            return
        if self.SR & 0x2:
            return
        next_time = self.schedule[0][0]

        if now >= next_time:
            next_str = self.schedule.pop(0)[1]
            self.DR = ord(next_str)
            self.request_interrupt()


class IOController:
    devices: {int: ExternalDevice}
    buffer: int
    IREQ: bool = False
    IPort: int = 0

    def __init__(self, input_schedule=None):
        if input_schedule is None:
            input_schedule = [(1, '\n')]
        self.devices = {0: ExternalDevice(schedule=input_schedule),
                        1: ExternalDevice()}

    def in_(self, port: int, register: int): # if register == 0 then SR else DR
        self.buffer = self.devices[port].read_status() if register == 0 else self.devices[port].read_data()

    def out(self, port: int):
        self.devices[port].write_data(self.buffer)

    def check_interrupts(self):
        if self.IREQ:
            return
        self.IREQ = False
        for port, device in self.devices.items():
            if device.SR & 0x2:
                self.IREQ = True
                self.IPort = port
                device.SR &= ~0x2
                break

    def update(self, now):
        for device in self.devices.values():
            device.update(now)