from obnl.impl.server import Scheduler

if __name__ == "__main__":
    c = Scheduler('localhost', './../data/initobnl.json', './../data/schedule.json')
    c.start()
