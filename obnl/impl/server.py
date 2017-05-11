import json
import pika

from obnl.impl.node import Node
from obnl.impl.loaders import JSONLoader
from obnl.impl.message import SimulatorConnection, NextStep, MetaMessage


class Scheduler(Node):
    """
    The Scheduler is a Node that manage the time flow.
    """

    def __init__(self, host, config_file, schedule_file):
        """
        
        :param host: the AMQP host 
        :param steps: a list of time steps
        :param blocks: a list of schedule blocks
        """
        super(Scheduler, self).__init__(host, Node.SCHEDULER_NAME)
        self._current_step = 0
        self._current_block = 0
        self._quit = False

        self._connected = set()
        self._sent = set()

        self._channel.exchange_declare(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name)

        self._steps, self._blocks = self._load_data(config_file, schedule_file)

        self._current_time = 0

    def _load_data(self, config_file, schedule_file):
        """

        :param host: the host of the AMQP server 
        :param config_file: the file that contains the structure
        :param schedule_file: the file that contains the schedule 
        """

        # Currently only JSON can be loaded
        with open(schedule_file) as jsonfile:
            schedule_data = json.loads(jsonfile.read())
            steps = schedule_data['steps']
            blocks = schedule_data['schedule']

        # Currently only JSON can be loaded
        # Load all the Nodes and creates the associated links
        loader = JSONLoader(self, config_file)
        # Connects the created Nodes to the update exchanger
        # using the schedule definition (blocks)
        # TODO: Should it be in Creator or Scheduler ???
        for node in loader.get_nodes():
            i = 0
            for block in blocks:
                if node in block:
                    self.create_simulation_links(node, i)
                i += 1
        return steps, blocks

    def start(self):
        """
        Sends the first time message.
        """
        self._current_step = 0
        self._current_block = 0
        super(Scheduler, self).start()

    def step(self, current_time, time_step):
        pass

    def create_data_link(self, node_out, attr, node_in):
        """
        Creates and connects the attribute communication from Node to Node.

        :param node_out: the Node sender name
        :param attr: the name of the attribute the Node want to communicate
        :param node_in: the Node receiver name
        """
        self._channel.exchange_declare(exchange=Node.DATA_NODE_EXCHANGE + node_out)
        self._channel.queue_declare(queue=Node.DATA_NODE_QUEUE + node_in)

        self._channel.queue_bind(exchange=Node.DATA_NODE_EXCHANGE + node_out,
                                 routing_key=Node.DATA_NODE_EXCHANGE + attr,
                                 queue=Node.DATA_NODE_QUEUE + node_in)

    def create_simulation_links(self, node, position):
        """
        Connects the scheduler exchange to the update queue of the Node

        :param node: the node to be connected to
        :param position: the position of the containing block
        """
        self._channel.exchange_declare(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name)
        self._channel.queue_declare(queue=Node.SIMULATION_NODE_QUEUE + node)
        self._channel.queue_bind(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name,
                                 routing_key=Node.UPDATE_ROUTING + str(position),
                                 queue=Node.SIMULATION_NODE_QUEUE + node)

        self._channel.exchange_declare(exchange=Node.SIMULATION_NODE_EXCHANGE + node)
        self._channel.queue_declare(queue=Node.SIMULATION_NODE_QUEUE + self._name)
        self._channel.queue_bind(exchange=Node.SIMULATION_NODE_EXCHANGE + node,
                                 routing_key=Node.SIMULATION_NODE_EXCHANGE + self._name,
                                 queue=Node.SIMULATION_NODE_QUEUE + self._name)

    def _update_time(self):
        """
        Sends new time message to the current block. 
        """
        ns = NextStep()
        ns.time_step = self._steps[self._current_step]
        ns.current_time = self._current_time

        mm = MetaMessage()
        mm.node_name = self._name
        mm.details.Pack(ns)

        self._channel.publish(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name,
                              routing_key=Node.UPDATE_ROUTING + str(self._current_block),
                              properties=pika.BasicProperties(reply_to=Node.SIMULATION_NODE_QUEUE + self.name),
                              body=mm.SerializeToString())

    def _on_local_message(self, ch, method, props, body):
        """
        Displays message receive from the general queue.
        """
        pass

    def _on_simulation_message(self, ch, method, props, body):
        """
        Displays message receive from the update queue and send the next time message.
        """
        m = MetaMessage()
        m.ParseFromString(body)

        if m.details.Is(SimulatorConnection.DESCRIPTOR):
            self._connected.add(m.node_name)
            if len(self._connected) == sum([len(b) for b in self._blocks]):
                self._current_time += self._steps[self._current_step]
                self._update_time()

        if m.details.Is(NextStep.DESCRIPTOR):
            if m.node_name in self._blocks[self._current_block]:
                self._sent.add(m.node_name)

        if len(self._connected) == sum([len(b) for b in self._blocks]):
            # block management
            if len(self._sent) == len(self._blocks[self._current_block]):
                self._current_block = (self._current_block + 1) % len(self._blocks)
                if self._current_block == 0:
                    self._current_step += 1
                    self._current_time += self._steps[self._current_step]
                if self._current_step >= len(self._steps):
                    self._quit = True
                if not self._quit:
                    self._update_time()
                    self._sent.clear()

    def _on_data_message(self, ch, method, props, body):
        """
        Displays message receive from the data queue.
        """
        pass
