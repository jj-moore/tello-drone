import sys
import db_utilities


def main():
    num_args = len(sys.argv)
    if num_args > 1:
        flight_to_validate = db_utilities.get_flight(sys.argv[1])
    else:
        flight_to_validate = db_utilities.most_recent_flight()

    confirm = input(f'Are you sure you want to validate the flight {flight_to_validate[0]} by '
                    f'{flight_to_validate[1]} {flight_to_validate[2]} (y/n): ')
    if confirm == 'y':
        db_utilities.validate_flight(flight_to_validate[0])
    else:
        print(f'Validation cancelled.')


if __name__ == '__main__':
    main()
