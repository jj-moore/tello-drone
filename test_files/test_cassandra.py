import random
import sys
import time
import uuid

# custom files
import classes
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
    num_args = len(sys.argv)
    db_row = classes.Positional()
    if num_args <= -1:
        print('\n**You must enter at least one command line argument (your name).')
        print('**Optional arguments (in order): group, organization, major')
        print('**Arguments with spaces must be enclosed in double or single quotes')
        exit(1)
    db_row.name = 'joe'
    db_row.group = 'Test Group'
    db_row.org_college = 'EMU'
    db_row.major = 'Painting'
    initialize()


def initialize():
    db_utilities.connect_to_db()
    db_row.flight_id = uuid.uuid1()
    db_row.station_id = uuid.uuid3(uuid.NAMESPACE_URL, hex(uuid.getnode()))
    try:
        while 1:
            time.sleep(1.0)
            log_generator()
    except KeyboardInterrupt:
        success = input("Was flight successful (y/n)? ")
        if success.upper() == "Y":
            statement = db_utilities.flight_success(db_row.flight_id)
            db_utilities.execute_cql(statement)
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
    statement = db_utilities.insert_record(db_row)
    print(statement)
    db_utilities.execute_cql(statement)


def log_generator():
    x = random.random()
    y = random.random()
    z = random.random()
    data = LogEvent(x, y, z)
    log_data_handler(data)


if __name__ == '__main__':
    main()
