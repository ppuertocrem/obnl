
GENERAL_NODE_QUEUE = 'obnl.general.node.'
"""Base of every general queue (followed by the name of the Node)"""
UPDATE_NODE_QUEUE = 'obnl.update.node.'
"""Base of every update queue (followed by the name of the Node)"""
DATA_NODE_QUEUE = 'obnl.data.node.'
"""Base of every data/attr queue (followed by the name of the Node)"""

UPDATE_ROUTING = 'obnl.update.block.'
"""Base of every routing key for block messages (followed by the number/position of the block)"""

UPDATE_EXCHANGE = 'obnl.update.'
"""Base of every update exchange (followed by the name of the Node)"""
DATA_EXCHANGE = 'obnl.attr.'
"""Base of every data/attr exchange (followed by the name of the Node)"""


class Node(object):
    """
    This is the base class for all Nodes of the system
    """

    def __init__(self, channel, name):
        """
        The constructor creates the 3 main queues
        - general: To receive data with everyone
        - update: To receive data for the time management
        - data: To receive attribute update

        :param channel: the connection to AMQP
        :param name: the id of the Node
        """
        self._channel = channel
        self._name = name

        self._general_queue = self._channel.queue_declare(queue=GENERAL_NODE_QUEUE + self._name)
        self._update_queue = self._channel.queue_declare(queue=UPDATE_NODE_QUEUE + self._name)
        self._data_queue = self._channel.queue_declare(queue=DATA_NODE_QUEUE + self._name)

    @property
    def name(self):
        """
        
        :return: the id of the Node 
        """
        return self._name

    def associate_callback(self):
        """
        Creates callbacks for each queue define in the constructor.
        Another function is necessary as the server MUST NOT have callbacks.
        """
        # TODO: Is it really necessary that the server creates the Nodes ???
        self._channel.basic_consume(self.on_general_message,
                                    consumer_tag='obnl_node_' + self._name + '_general',
                                    queue=self._general_queue.method.queue,
                                    no_ack=True)
        self._channel.basic_consume(self.on_update_message,
                                    consumer_tag='obnl_node_' + self._name + '_update',
                                    queue=self._update_queue.method.queue,
                                    no_ack=True)
        self._channel.basic_consume(self.on_data_message,
                                    consumer_tag='obnl_node_' + self._name + '_data',
                                    queue=self._data_queue.method.queue,
                                    no_ack=True)

    def create_update_link(self, scheduler, position):
        """
        Connects the scheduler exchange to the update queue of the Node
                
        :param scheduler: the scheduler to be connected to
        :param position: the position of the containing block
        """
        # TODO: Not part of the API
        self._channel.queue_bind(exchange=UPDATE_EXCHANGE+scheduler,
                                 routing_key=UPDATE_ROUTING + str(position),
                                 queue=UPDATE_NODE_QUEUE + self._name)

    def create_link(self, attr, node_in):
        """
        Creates and connects the attribute communication from Node to Node.
        
        :param attr: the name of the attribute the Node want to communicate
        :param node_in: the Node receiver
        """
        self._channel.exchange_declare(exchange=DATA_EXCHANGE + self._name)

        self._channel.queue_bind(exchange=DATA_EXCHANGE + self._name,
                                 routing_key=DATA_EXCHANGE + attr,
                                 queue=DATA_NODE_QUEUE + node_in.name)

    def reply_to(self, props, message):
        """
        Replies to a message.
        
        :param props: the props of the 'question' 
        :param message: the message (str)
        """
        self._channel.basic_publish(exchange='',
                                    routing_key=props.reply_to,
                                    body=str(message))

    def on_general_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the general queue.
        
        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        pass

    def on_update_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the update queue.

        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        pass

    def on_data_message(self, ch, method, props, body):
        """
        The callback function when a message arrives on the data/attr queue.

        :param ch: the channel 
        :param method: the method
        :param props: the properties
        :param body: the message
        """
        pass

    def update_attribute(self, attr, value):
        """
        Sends the new attribute value to those who want to know.
                
        :param attr: the attribute to communicate 
        :param value: the new value of the attribute
        :return: 
        """
        # FIXME: if the attribute name is not on the init file, the system freezes.
        self._channel.basic_publish(exchange=DATA_EXCHANGE + self._name,
                                    routing_key=DATA_EXCHANGE + attr,
                                    body=value)

