import sys
import db_utilities


def main():
    num_args = len(sys.argv)
    if num_args > 1:
        flight_to_validate = db_utilities.get_flight(sys.argv[1])
    else:
        flight_to_validate = db_utilities.most_recent_flight_from_station()

    confirm = input(f'Are you sure you want to invalidate the flight {flight_to_validate[0]} by '
                    f'{flight_to_validate[1]} {flight_to_validate[2]} (y/n): ')
    if confirm == 'y':
        db_utilities.invalidate_flight(flight_to_validate[0])
    else:
        print(f'Invalidation cancelled.')


if __name__ == '__main__':
    main()