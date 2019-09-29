import datetime
from cassandra.cluster import Cluster
from numpy import long

session = None


def connect_to_db():
    global session
    cluster = Cluster(['172.17.0.2'])
    session = cluster.connect('competition')


def insert_record(positional):
    date_time = unix_time_millis()
    return f'INSERT INTO positional (flight_id, ts, x, y, z, latest_ts, station_id, num_crashes, ' \
           f'name, group, org_college, major, valid) ' \
           f'VALUES (' \
           f'{positional.flight_id}, {date_time}, {positional.x}, {positional.y}, {positional.z}, ' \
           f'{date_time}, {positional.station_id}, {positional.num_crashes}, \'{positional.name}\', ' \
           f'\'{positional.group}\', \'{positional.org_college}\', \'{positional.major}\', {positional.valid}' \
           f');'


def execute_cql(statement):
    session.execute(statement)


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def unix_time_millis():
    dt = datetime.datetime.now()
    return long(unix_time(dt) * 1000.0)
