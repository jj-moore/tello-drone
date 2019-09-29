from cassandra.cluster import Cluster
session = None


def connect_to_db():
    global session
    cluster = Cluster(['172.17.0.2'])
    session = cluster.connect('competition')


def insert_record(positional):
    return f'INSERT INTO positional (flight_id, ts, x, y, z, latest_ts, station_id, num_crashes, ' \
           f'name, group, org_college, major, valid) ' \
           f'VALUES (' \
           f'{positional.flight_id}, toTimeStamp(now()), {positional.x}, {positional.y}, {positional.z}, ' \
           f'toTimeStamp(now()), {positional.station_id}, {positional.num_crashes}, {positional.name}, ' \
           f'{positional.group}, {positional.org_college}, {positional.major}, {positional.valid}' \
           f');'


def execute_cql(statement):
    session.execute(statement)
