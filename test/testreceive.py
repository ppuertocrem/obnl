from obnl.impl.data import Node


class ClientNode(Node):

    def __init__(self, channel, name):

        super(ClientNode, self).__init__(channel, name)
        self.associate_callback()

    def on_general_message(self, ch, method, props, body):
        self._print_message(ch, method, props, body)

    def on_update_message(self, ch, method, props, body):
        self._print_message(ch, method, props, body)
        if not(self._name == 'C'):
            """condition to avoid freeze"""
            self.update_attribute('t', 'time: '+str(int(body)))
        self.reply_to(props, self._name+' Done!')

    def on_data_message(self, ch, method, props, body):
        print('Data: '+str(body))
        print('From: '+str(method))

    def _print_message(self, ch, method, props, body):
        print('---')
        print(method)
        print(body)
        print('===')

if __name__ == "__main__":
    import pika

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    ClientNode(channel, 'A')
    ClientNode(channel, 'B')
    ClientNode(channel, 'C')

    channel.start_consuming()
