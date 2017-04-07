import json
import asyncio
import pika


from obnl.impl.data import Node, UPDATE_EXCHANGE, UPDATE_NODE_QUEUE, UPDATE_ROUTING
from obnl.impl.loaders import JSONLoader


class Creator(object):
    """
    This class uses two files to generate an AMQP structure.
    """

    def __init__(self, host, config_file, schedule_file):
        """
        
        :param host: the host of the AMQP server 
        :param config_file: the file that contains the structure
        :param schedule_file: the file that contains the schedule 
        """
        # connect the scheduler to the AMQP server
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self._channel = self._connection.channel()

        # Currently only JSON can be loaded
        # Load all the Nodes and creates the associated links
        loader = JSONLoader(self._channel, config_file)

        # Currently only JSON can be loaded
        with open(schedule_file) as jsonfile:
            schedule_data = json.loads(jsonfile.read())
            steps = schedule_data['steps']
            blocks = schedule_data['schedule']

        self._scheduler = Scheduler(self._channel, 'scheduler', steps, blocks)
        # The scheduler needs to have its callback
        self._scheduler.associate_callback()

        # Connects the created Nodes to the update exchanger
        # using the schedule definition (blocks)
        # TODO: Should it be in Creator or Scheduler ???
        for node in loader.get_nodes():
            i = 0
            for block in blocks:
                if node.name in block:
                    node.create_update_link(self._scheduler.name, i)
                i += 1

    def run(self):
        """
        Starts the communication.
        
        WARNING: As start_consuming is a blocking function it SHOULD be the last function
                 called.
        """
        self._scheduler.start()
        self._channel.start_consuming()


class Scheduler(Node):
    """
    The Scheduler is a Node that manage the time flow.
    """

    def __init__(self, channel, name, steps, blocks):
        """
        
        :param channel: the AMQP channel 
        :param name: the name of the scheduler
        :param steps: a list of time steps
        :param blocks: a list of schedule blocks
        """
        super(Scheduler, self).__init__(channel, name)
        self._steps = steps
        self._current_step = 0
        self._blocks = blocks
        self._current_block = 0
        self._loop = asyncio.get_event_loop()

        self._channel.exchange_declare(exchange=UPDATE_EXCHANGE + self._name)

    def start(self):
        """
        Sends the first time message .
        """
        self._current_step = 0
        self._current_block = 0
        self._update_time()

    def _update_time(self):
        """
        Sends new time message to the current block. 
        """
        self._channel.basic_publish(exchange=UPDATE_EXCHANGE+self._name,
                                    routing_key=UPDATE_ROUTING+str(self._current_block),
                                    properties=pika.BasicProperties(reply_to=UPDATE_NODE_QUEUE+self.name),
                                    body=str(self._steps[self._current_step]))

    def on_general_message(self, ch, method, props, body):
        """
        Displays message receive from the general queue.
        """
        self._print_message(ch, method, props, body)

    def on_update_message(self, ch, method, props, body):
        """
        Displays message receive from the update queue and send the next time message.
        """
        self._print_message(ch, method, props, body)

        # block management
        # TODO: Dirty code
        self._current_block += 1
        if self._current_block >= len(self._blocks):
            self._current_block = 0
            if self._current_step + 1 >= len(self._steps):
                print("QUIT")
                self._channel.close()
            else:
                self._current_step += 1
        self._update_time()

    def on_data_message(self, ch, method, props, body):
        """
        Displays message receive from the data queue.
        """
        self._print_message(ch, method, props, body)

    def _print_message(self, ch, method, props, body):
        print('---')
        print(method)
        print('---')
        print(body)
        print('===')


if __name__ == "__main__":
    c = Creator('localhost', '../../data/initobnl.json', '../../data/schedule.json')
    c.run()
