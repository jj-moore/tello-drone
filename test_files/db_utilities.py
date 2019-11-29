import datetime
import uuid

from dse.cluster import Cluster
from dse.auth import PlainTextAuthProvider
from numpy import long

session = None
get_flight_prepared = None


# object that will be stored in database
class Positional:
    flight_id = ''
    x = ''
    y = ''
    z = ''
    station_id = ''
    num_crashes = 0
    name = ''
    group = ''
    org_college = ''
    major = ''
    valid = False

    def __str__(self):
        return f'Name: {self.name} Type: {self.group} Org: {self.org_college} Major: {self.major}'


def connect_to_db():
    global session
    global get_flight_prepared

    if session is None:
        contact_points = get_ips('ips.txt')
        auth_provider = PlainTextAuthProvider(username='cassandra', password='eagles29')
        cluster = Cluster(auth_provider=auth_provider, contact_points=contact_points)
        try:
            session = cluster.connect('competition')
            print('Connected to Cassandra cluster.')
            get_flight_prepared = session.prepare(
                f'SELECT flight_id, station_id, name, group, org_college, major, ts, latest_ts, valid '
                f'FROM positional WHERE flight_id = ? ORDER BY ts LIMIT 1;')
        except:
            print('Cannot connect to Cassandra cluster. Exiting ...')
            exit(1)


def get_ips(filename):
    file = open(filename, "r")
    return file.read().split(",")


def insert_record(positional):
    connect_to_db()
    date_time = unix_time_millis()
    statement = f'INSERT INTO positional (flight_id, ts, x, y, z, latest_ts, station_id, num_crashes, ' \
                f'name, group, org_college, major, valid) ' \
                f'VALUES (' \
                f'{positional.flight_id}, {date_time}, {positional.x}, {positional.y}, {positional.z}, ' \
                f'{date_time}, {positional.station_id}, {positional.num_crashes}, \'{positional.name}\', ' \
                f'\'{positional.group}\', \'{positional.org_college}\', \'{positional.major}\', {positional.valid}' \
                f');'
    session.execute(statement)


def validate_flight(flight_id):
    connect_to_db()
    statement = f'UPDATE positional SET valid = true WHERE flight_id = {flight_id}'
    session.execute(statement)


def invalidate_flight(flight_id):
    connect_to_db()
    statement = f'UPDATE positional SET valid = false WHERE flight_id = {flight_id}'
    session.execute(statement)


def get_flight(flight_id):
    connect_to_db()
    try:
        if isinstance(flight_id, str):
            flight_uuid = uuid.UUID(flight_id)
        else:
            flight_uuid = flight_id
        bound_statement = get_flight_prepared.bind([flight_uuid])
        flight = session.execute(bound_statement).one()
        return flight
    except:
        print(f'Flight {flight_id} was not found')
        exit(1)


def get_ordered_flights(station_id=None):
    connect_to_db()

    if station_id is None:
        statement = 'SELECT DISTINCT flight_id, latest_ts FROM positional;'
    else:
        statement = f'SELECT DISTINCT flight_id, latest_ts FROM positional WHERE station_id = {station_id} ALLOW FILTERING;'

    rows = session.execute(statement)
    key_value = {}
    for row in rows:
        key_value.update({row[0]: row[1]})
    keys = sorted(key_value, key=key_value.__getitem__)
    return keys


def most_recent_flight_from_station():
    connect_to_db()
    station_id = uuid.uuid3(uuid.NAMESPACE_URL, hex(uuid.getnode()))
    try:
        rows = get_ordered_flights(station_id)
        last_flight_id = rows[rows.__len__() - 1]
        statement = f'SELECT flight_id, name, org_college FROM positional WHERE flight_id = {last_flight_id} LIMIT 1;'
        row = session.execute(statement).one()
        return row
    except:
        print(f'ERROR: No flights found for station id {station_id}')
        exit(1)


def delete_flight(flight_id):
    connect_to_db()
    statement = f'DELETE FROM positional WHERE flight_id = {flight_id}'
    try:
        session.execute(statement)
        print(f'Flight \'{flight_id}\' was deleted.')
    except:
        print(f'An error occurred while attempting to delete flight {flight_id}')


def update_flight_in_progress(flight_id):
    statement = f'UPDATE positional USING TTL 25 SET valid = false WHERE flight_id = {flight_id}'
    connect_to_db()
    try:
        session.execute(statement)
    except:
        pass


def unix_time_millis():
    dt = datetime.datetime.utcnow()
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    seconds = delta.total_seconds()
    return long(seconds * 1000)
