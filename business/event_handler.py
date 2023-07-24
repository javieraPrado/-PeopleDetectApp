from PyQt5.QtCore import QObject, QThread

class EventHandler(QObject):
    signal = pyqtSignal(str, object)
    def __init__(self):
        self.listeners = {}

    def add_listener(self, event_name, callback):
        print("asd")
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def trigger_event(self, event_name, data):
        print("hola")
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(data)

class CustomThread(QThread):
    def __init__(self, event_handler):
        super().__init__()
        self.event_handler = event_handler

    def run(self):
        self.event_handler.trigger_event('custom_event', 'Custom data')