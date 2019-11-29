import random
import sys
import time
import uuid

# custom files
import db_utilities

# data to be stored into the database
db_row = None


class LogEvent:
    class mvo:
        pos_x = 0.0
        pos_y = 0.0
        pos_z = 0.0

    def __init__(self, x, y, z):
        self.mvo = self.mvo()
        self.mvo.pos_x = x
        self.mvo.pos_y = y
        self.mvo.pos_z = z


def main():
    global db_row
    db_row = db_utilities.Positional()
    db_row.name = 'Test User'
    db_row.group = 'Test Group'
    db_row.org_college = 'Test Org'
    db_row.major = 'Test Major'
    initialize()


def initialize():
    db_row.flight_id = uuid.uuid1()
    db_row.station_id = uuid.uuid3(uuid.NAMESPACE_URL, hex(uuid.getnode()))
    try:
        while 1:
            time.sleep(1.0)
            log_generator()
    except KeyboardInterrupt:
        success = input("Was flight successful (y/n)? ")
        if success.upper() == "Y":
            db_utilities.validate_flight(db_row.flight_id)
        print('Goodbye!')
        quit(0)
    except Exception as e:
        print(e)
        quit(0)


def log_data_handler(data):
    print(f'X:{data.mvo.pos_x} Y:{data.mvo.pos_y} Z:{data.mvo.pos_z} {db_row}')
    db_row.x = data.mvo.pos_x
    db_row.y = data.mvo.pos_y
    db_row.z = data.mvo.pos_z
    db_utilities.insert_record(db_row)


def log_generator():
    x = random.random()
    y = random.random()
    z = random.random()
    data = LogEvent(x, y, z)
    log_data_handler(data)


if __name__ == '__main__':
    main()
