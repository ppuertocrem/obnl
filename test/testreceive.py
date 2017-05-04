from threading import Thread
from obnl.impl.data import Node

from obnl.impl.message import MetaMessage, SimulatorConnection


class ClientNode(Node):

    def __init__(self, host, name, input_attributes=None, output_attributes=None, is_first=False):
        super(ClientNode, self).__init__(host, name, input_attributes, output_attributes, is_first)

        si = SimulatorConnection()
        si.type = SimulatorConnection.OTHER

        m = MetaMessage()
        m.node_name = self._name
        m.details.Pack(si)
        self._channel.publish(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name,
                              routing_key=Node.SIMULATION_NODE_EXCHANGE + Node.SCHEDULER_NAME,
                              body=m.SerializeToString())

    def step(self):
        print('----- '+self.name+' -----')
        print(self._name, self._input_attributes)
        print(self._name, self._input_values)
        print(self._name, self._output_attributes)
        print('=============')
        for o in self._output_attributes:
            self.update_attribute(o, 4.2)

if __name__ == "__main__":

    a = ClientNode('localhost', 'A', output_attributes=['ta'], input_attributes=['set'], is_first=True)
    b = ClientNode('localhost', 'B', output_attributes=['tb'])
    c = ClientNode('localhost', 'C', input_attributes=['ta', 'tb'], output_attributes=['set'])

    print('Start A')
    Thread(target=a.start).start()
    print('Start B')
    Thread(target=b.start).start()
    print('Start C')
    Thread(target=c.start).start()
