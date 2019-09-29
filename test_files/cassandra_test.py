from cassandra.cluster import Cluster

cluster = Cluster(['172.17.0.2'])
session = cluster.connect('competition')

sql_statement = 'INSERT INTO positional (flight_id, ts, x, y, z, latest_ts, station_id, ' \
                'num_crashes, name, group, org_college, major, valid) VALUES (50554d6e-29bb-11e5-b345-feff819cdc9f, ' \
                'toTimeStamp(now()), 0.01, 0.02, 0.03, toTimeStamp(now()), 274a8e05-cb67-5eb5-8592-6145a580450c, 0, ' \
                '\'John Doe\', \'student\', \'cas\', \'Computer Science\', true);'
session.execute(sql_statement)

rows = session.execute('SELECT * FROM positional')
for record in rows:
    print(record.flight_id, record.name)
