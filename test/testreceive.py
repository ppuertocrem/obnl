from obnl.client import ClientNode


class ClientTestNode(ClientNode):

    def __init__(self, host, name, input_attributes=None, output_attributes=None, is_first=False):
        super(ClientTestNode, self).__init__(host, name, input_attributes, output_attributes, is_first)

    def step(self, current_time, time_step):
        print('----- '+self.name+' -----')
        print(self.name, time_step)
        print(self.name, current_time)
        print(self.name, self.input_values)
        print(self.name, self.output_attributes)
        print('=============')
        for o in self.output_attributes:
            self.update_attribute(o, 4.2)

if __name__ == "__main__":

    a = ClientTestNode('localhost', 'A', output_attributes=['ta'], input_attributes=['set'], is_first=True)
    b = ClientTestNode('localhost', 'B', output_attributes=['tb'])
    c = ClientTestNode('localhost', 'C', input_attributes=['ta', 'tb'], output_attributes=['set'])

    print('Start A')
    a.start()
    print('Start B')
    b.start()
    print('Start C')
    c.start()
