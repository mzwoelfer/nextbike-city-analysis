import argparse
from nextbike_processing.utils import ensure_directory_exists
from nextbike_processing.stations import process_and_save_stations
from nextbike_processing.trips import process_and_save_trips


def main():
    parser = argparse.ArgumentParser(
        description="Nextbike data processing application."
    )
    parser.add_argument(
        "--city-id", type=int, required=True, help="City ID to process."
    )
    parser.add_argument(
        "--export-folder", type=str, required=True, help="Folder to save data."
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date to process data for. (format: YYYY-MM-DD).",
    )
    args = parser.parse_args()

    ensure_directory_exists(args.export_folder)

    date = args.date
    if (
        not isinstance(date, str)
        or not args.date.count("-") == 2
        or len(args.date) != 10
    ):
        raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")
    process_and_save_stations(args.city_id, str(date), args.export_folder)
    process_and_save_trips(args.city_id, str(date), args.export_folder)


if __name__ == "__main__":
    main()
