import pika

from obnl.impl.message import MetaMessage, AttributeMessage, NextStep


class Node(object):
    """
    This is the base class for all Nodes of the system
    """

    SCHEDULER_NAME = 'scheduler'

    LOCAL_NODE_QUEUE = 'obnl.local.node.'
    """Base of every local queue (followed by the name of the Node)"""
    LOCAL_NODE_EXCHANGE = 'obnl.local.node.'
    """Base of every local exchange (followed by the name of the Node)"""

    SIMULATION_NODE_QUEUE = 'obnl.simulation.node.'
    """Base of every update queue (followed by the name of the Node)"""
    SIMULATION_NODE_EXCHANGE = 'obnl.simulation.node.'
    """Base of every update exchange (followed by the name of the Node)"""

    DATA_NODE_QUEUE = 'obnl.data.node.'
    """Base of every data queue (followed by the name of the Node)"""
    DATA_NODE_EXCHANGE = 'obnl.data.node.'
    """Base of every data/attr exchange (followed by the name of the Node)"""

    UPDATE_ROUTING = 'obnl.update.block.'
    """Base of every routing key for block messages (followed by the number/position of the block)"""

    def __init__(self, host, name, input_attributes=None, output_attributes=None, is_first=False):
        """
        The constructor creates the 3 main queues
        - general: To receive data with everyone
        - update: To receive data for the time management
        - data: To receive attribute update

        :param host: the connection to AMQP
        :param name: the id of the Node
        :param input_attributes: a list of input data
        :param output_attributes: a list of output data
        :param is_first: break the loop
        """
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self._channel = connection.channel()
        self._name = name

        self._local_queue = self._channel.queue_declare(queue=Node.LOCAL_NODE_QUEUE + self._name)
        self._local_exchange = self._channel.exchange_declare(exchange=Node.LOCAL_NODE_EXCHANGE + self._name)
        self._channel.queue_bind(exchange=Node.LOCAL_NODE_EXCHANGE + self._name, queue=Node.LOCAL_NODE_QUEUE + self._name)

        self._simulation_queue = self._channel.queue_declare(queue=Node.SIMULATION_NODE_QUEUE + self._name)
        self._simulation_exchange = self._channel.exchange_declare(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name)

        self._data_queue = self._channel.queue_declare(queue=Node.DATA_NODE_QUEUE + self._name)

        self._channel.basic_consume(self._on_local_message,
                                    consumer_tag='obnl_node_' + self._name + '_local',
                                    queue=self._local_queue.method.queue,
                                    no_ack=True)
        self._channel.basic_consume(self._on_simulation_message,
                                    consumer_tag='obnl_node_' + self._name + '_simulation',
                                    queue=self._simulation_queue.method.queue,
                                    no_ack=True)
        self._channel.basic_consume(self._on_data_message,
                                    consumer_tag='obnl_node_' + self._name + '_data',
                                    queue=self._data_queue.method.queue,
                                    no_ack=True)

        self._next_step = False
        self._reply_to = None
        self._is_first = is_first

        self._input_values = {}
        self._input_attributes = input_attributes
        self._output_attributes = output_attributes

    @property
    def name(self):
        """
        
        :return: the name of the Node 
        """
        return self._name

    def start(self):
        self._channel.start_consuming()

    def create_simulation_links(self, scheduler, position):
        """
        Connects the scheduler exchange to the update queue of the Node
                
        :param scheduler: the scheduler to be connected to
        :param position: the position of the containing block
        """
        self._channel.queue_bind(exchange=Node.SIMULATION_NODE_EXCHANGE + scheduler,
                                 routing_key=Node.UPDATE_ROUTING + str(position),
                                 queue=Node.SIMULATION_NODE_QUEUE + self._name)
        self._channel.queue_bind(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name,
                                 routing_key=Node.SIMULATION_NODE_EXCHANGE + Node.SCHEDULER_NAME,
                                 queue=Node.SIMULATION_NODE_QUEUE + scheduler)

    def reply_to(self, reply_to, message):
        """
        Replies to a message.
        
        :param reply_to: the asker 
        :param message: the message (str)
        """
        print(self.name, 'sends reply', reply_to)
        if reply_to:

            m = MetaMessage()
            m.node_name = self._name
            m.type = MetaMessage.ANSWER

            m.details.Pack(message)

            self._channel.publish(exchange='', routing_key=reply_to, body=m.SerializeToString())

    def step(self):
        raise NotImplementedError('Abstract Node call')

    def _on_local_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the general queue.
        
        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        print(self.name, 'receives local', )
        if self._next_step and (self._is_first or not self._input_attributes or len(self._input_values.keys()) == len(self._input_attributes)):
            self.step()
            self._next_step = False
            self._input_values.clear()
            self.reply_to(self._reply_to, NextStep())

    def _on_simulation_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the update queue.

        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        print(self.name, 'receives simu', props.reply_to)
        mm = MetaMessage()
        mm.ParseFromString(body)

        if mm.details.Is(NextStep.DESCRIPTOR) and mm.node_name == Node.SCHEDULER_NAME:
            self._next_step = True
            self._reply_to = props.reply_to
            # TODO: call updateX or updateY depending on the message content?
            self.send_local(mm.details)

    def _on_data_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the data/attr queue.

        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        print(self.name, 'receives data')
        mm = MetaMessage()
        mm.ParseFromString(body)

        if mm.details.Is(AttributeMessage.DESCRIPTOR):
            am = AttributeMessage()
            mm.details.Unpack(am)
            self._input_values[am.attribute_name] = am.attribute_value

        # TODO: call updateX or updateY depending on the meta content
        self.send_local(mm.details)

    def send_local(self, message):
        """
        Sends the content to local.

        :param message: a protobuf message 
        :param reply_to: the way to reply
        :return: 
        """
        print(self.name, 'sends local')
        self._channel.publish(exchange=Node.LOCAL_NODE_EXCHANGE + self._name,
                              routing_key=Node.LOCAL_NODE_EXCHANGE + self._name,
                              body=message.SerializeToString())

    def send_scheduler(self, message):
        """
        Sends the content to local.

        :param message: a protobuf message 
        :return: 
        """
        m = MetaMessage()
        m.node_name = self._name
        m.details.Pack(message)

        print(self.name, 'sends scheduler')
        self._channel.publish(exchange=Node.SIMULATION_NODE_EXCHANGE + self._name,
                              routing_key=Node.SIMULATION_NODE_EXCHANGE + Node.SCHEDULER_NAME,
                              body=m.SerializeToString())

    def update_attribute(self, attr, value):
        """
        Sends the new attribute value to those who want to know.
                
        :param attr: the attribute to communicate 
        :param value: the new value of the attribute
        :return: 
        """
        am = AttributeMessage()
        am.simulation_time = 0  # FIXME: where is the simulation time ?
        am.attribute_name = attr
        am.attribute_value = float(value)

        m = MetaMessage()
        m.node_name = self._name
        m.type = MetaMessage.ATTRIBUTE
        m.details.Pack(am)

        if self._output_attributes:
            print(self.name, 'sends', attr, 'with value', value)
            self._channel.publish(exchange=Node.DATA_NODE_EXCHANGE + self._name,
                                  routing_key=Node.DATA_NODE_EXCHANGE + attr,
                                  body=m.SerializeToString())


