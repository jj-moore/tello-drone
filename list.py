import db_utilities


def main():
    db_utilities.connect_to_db()
    statement = 'SELECT DISTINCT flight_id, station_id, name, group, org_college, major FROM Positional LIMIT 10;'
    results = db_utilities.execute_cql_return(statement)
    for result in results:
        print(f'Flight Id:\t{result[0]}\tName:\t{result[2]}')
        print(f'Station Id:\t{result[1]}\tGroup:\t{result[3]}')
        print(f'\t\t\t\t\t\t\tOrg:\t{result[4]}')
        print(f'\t\t\t\t\t\t\tMajor:\t{result[5]}')
        print('')


if __name__ == '__main__':
    main()
