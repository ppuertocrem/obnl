from threading import Thread
from obnl.impl.node import ClientNode as _ClientNodeImpl


class ClientNode(object):

    def __init__(self, host, name, input_attributes=None, output_attributes=None, is_first=False):
        self._node_impl = _ClientNodeImpl(host, name, self, input_attributes, output_attributes, is_first)

    @property
    def name(self):
        return self._node_impl.name

    @property
    def input_values(self):
        return self._node_impl.input_values

    @property
    def input_attributes(self):
        return self._node_impl.input_attributes

    @property
    def output_attributes(self):
        return self._node_impl.output_attributes

    def start(self):
        Thread(target=self._node_impl.start).start()

    def step(self, current_time):
        raise NotImplementedError('abstract function call from '+str(self.__class__))

    def update_attribute(self, attr, value):
        self._node_impl.update_attribute(attr, value)
