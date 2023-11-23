import os
import requests
import argparse
import subprocess

weather_api_url = "https://archive-api.open-meteo.com/v1/archive"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "repository",
        type=str,
        help="Link to the GitHub repository"
    )
    parser.add_argument(
        "latitude",
        type=float,
        help="Latitude of your position"
    )
    parser.add_argument(
        "longitude",
        type=float,
        help="Longitude of your position"
    )
    parser.add_argument(
        "--d",
        action="store_true",
        help="Optional flag to take first argument as URL and download the repository."
             "If not set, takes first argument as path."
    )
    args = parser.parse_args()

    repository = args.repository
    if args.d:
        repository_name = repository.split('/')[-1].split('.')[0]
        # Check if the repository directory exists
        if not os.path.exists(repository_name):
            # Clone the repository
            subprocess.run(["git", "clone", repository])
        else:
            # If the repository already exists, pull the latest changes
            subprocess.run(["git", "reset", "--hard"], cwd=repository_name)
            subprocess.run(["git", "pull"], cwd=repository_name)
        os.chdir(repository_name)
    else:
        os.chdir(repository)

    latitude = args.latitude
    longitude = args.longitude

    # Run git log and capture the output
    git_log_result = subprocess.run(["git", "log", "--pretty=%as"], stdout=subprocess.PIPE, text=True)
    date_string = git_log_result.stdout.strip()

    # Create a list of dates and create dictionary
    dates = date_string.split('\n')
    date_count = {}

    # Count the occurrences of each date
    for date in dates:
        date_count[date] = date_count.get(date, 0) + 1

    if len(date_count) > 9999:
        print("Number of days (commits) is too large. API only allows for 10,000 requests per day.")

    commits_on_rainy_days = 0
    commits_on_sunny_days = 0

    # For each day, make API request and check if it rained.
    # 5 (in mm per square meter) is quite an arbitrary number to determine if it was a rainy day. ¯\_(ツ)_/¯
    for date in date_count:
        if get_weather_data(date[0:10], latitude, longitude) >= 5:
            commits_on_rainy_days += date_count[date]
        else:
            commits_on_sunny_days += date_count[date]

    print(f"\nCommits on rainy days: {commits_on_rainy_days}")
    print(f"Commits on sunny days: {commits_on_sunny_days}")
    if commits_on_sunny_days > commits_on_rainy_days:
        print("\nYou are more productive on sunny days.")
        print("Based on reliable data processed by a sophisticated algorithm you CAN blame bad weather now!")
    else:
        print("You are more productive on rainy days.\nSeems like for you, staying at home means getting things done.")


def get_weather_data(date, latitude, longitude):
    rain_value = 0
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date,
        "end_date": date,
        "daily": "rain_sum"
    }

    response = requests.get(weather_api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        rain_value = data["daily"]["rain_sum"][0]
        if rain_value is None:
            rain_value = 0
    else:
        print(f"Error: {response.status_code} - {response.text}")

    return rain_value


if __name__ == '__main__':
    main()
