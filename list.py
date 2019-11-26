import db_utilities


def main():
    db_utilities.connect_to_db()
    flight_list = db_utilities.get_ordered_flights()
    total_flights = flight_list.__len__()
    if total_flights >= 10:
        count = 10
    else:
        count = total_flights

    for i in range(total_flights - count, total_flights, 1):
        result = db_utilities.get_flight(flight_list[i])
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
