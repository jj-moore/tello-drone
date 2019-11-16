import sys
import db_utilities


def main():
    db_utilities.connect_to_db()
    num_args = len(sys.argv)
    if num_args > 1:
        flight_to_delete = get_flight(sys.argv[1])
    else:
        flight_to_delete = last_flight()
    confirm = input(f'Are you sure you want to delete the flight {flight_to_delete[0]} by '
                    f'{flight_to_delete[1]} {flight_to_delete[2]} (y/n): ')
    if confirm == 'y':
        statement = f'DELETE FROM positional WHERE flight_id = {flight_to_delete[0]}'
        try:
            db_utilities.execute_cql(statement)
            print(f'Flight \'{flight_to_delete[0]}\' was deleted.')
        except:
            print(f'An error occurred while attempting to delete flight {flight_to_delete[0]}')
    else:
        print(f'Delete cancelled.')


def last_flight():
    statement = 'SELECT flight_id, name, org_college FROM positional LIMIT 1;'
    try:
        row = db_utilities.execute_cql_return(statement).one()
        return row
    except:
        print('ERROR: No flights found in the database.')
        exit(1)


def get_flight(flight_id):
    statement = f'SELECT flight_id, name, org_college FROM positional WHERE flight_id = {flight_id} LIMIT 1;'
    try:
        row = db_utilities.execute_cql_return(statement).one()
        return row
    except:
        print(f'ERROR: flight \'{flight_id}\' does not exist in the database.')
        exit(1)


if __name__ == '__main__':
    main()
