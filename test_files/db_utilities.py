import datetime
from dse.cluster import Cluster
from dse.auth import PlainTextAuthProvider
from numpy import long

session = None


def connect_to_db():
    global session
    cluster = Cluster(['172.17.0.2'])
    auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')
    cluster = Cluster(auth_provider=auth_provider, contact_points=get_ips())
    try:
        session = cluster.connect('competition')
        print('Connected to Cassandra cluster.')
    except:
        print('Cannot connect to Cassandra cluster. Exiting ...')
        exit(1)

def get_ips():
    file = open("ips.txt", "r")
    return file.read().split(",")


def insert_record(positional):
    date_time = unix_time_millis()
    return f'INSERT INTO positional (flight_id, ts, x, y, z, latest_ts, station_id, num_crashes, ' \
           f'name, group, org_college, major, valid) ' \
           f'VALUES (' \
           f'{positional.flight_id}, {date_time}, {positional.x}, {positional.y}, {positional.z}, ' \
           f'{date_time}, {positional.station_id}, {positional.num_crashes}, \'{positional.name}\', ' \
           f'\'{positional.group}\', \'{positional.org_college}\', \'{positional.major}\', {positional.valid}' \
           f');'


def flight_success(flight_id):
    return f'UPDATE positional SET valid = true WHERE flight_id = {flight_id}'


def execute_cql(statement):
    session.execute(statement)


def unix_time_millis():
    dt = datetime.datetime.now()
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    seconds = delta.total_seconds()
    return long(seconds * 1000)
