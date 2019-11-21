import db_utilities


def main():
    db_utilities.connect_to_db()
    statement = 'SELECT DISTINCT flight_id FROM positional;'
    flights = db_utilities.execute_cql_return(statement)
    flight_id_array = []
    for flight in flights:
        flight_id_array.append(flight[0])
    flight_id_array.reverse()

    for flight_id in flight_id_array:
        result = db_utilities.get_flight(flight_id)
        flight_time = int((result[7] - result[6]).total_seconds())
        flight_minutes = int(flight_time / 60)
        flight_seconds = flight_time % 60
        print(f'Flight Id:\t{result[0]}\tName:\t\t{result[2]}')
        print(f'Station Id:\t{result[1]}\tGroup:\t\t{result[3]}')
        print(f'\t\t\t\t\t\t\tOrg:\t\t{result[4]}')
        print(f'\t\t\t\t\t\t\tMajor:\t\t{result[5]}')
        print(f'\t\t\t\t\t\t\tFlight Time:\t{flight_minutes}m {flight_seconds}s')
        print('')


if __name__ == '__main__':
    main()
