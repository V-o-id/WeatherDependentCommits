import os
import sys
import subprocess
import requests

weather_api_url = "https://archive-api.open-meteo.com/v1/archive"


def main():
    # TODO: if hosted on web, this error handling is probably unnecessary
    if not sys.argv[1]:
        print("No link to GitHub repository provided, abort.")
        return
    if not sys.argv[2]:
        print("No value for latitude provided, choose fall-back option (48.303056).")
        latitude = 48.303056
    else:
        latitude = sys.argv[2]
    if not sys.argv[3]:
        print("No value for longitude provided, choose fall-back option (14.290556).")
        longitude = 14.290556
    else:
        longitude = sys.argv[3]

    repository_url = sys.argv[1]
    repository_name = repository_url.split('/')[-1].split('.')[0]

    # Check if the repository directory exists
    if not os.path.exists(repository_name):
        # Clone the repository
        subprocess.run(["git", "clone", repository_url])
    else:
        # If the repository already exists, pull the latest changes
        subprocess.run(["git", "reset", "--hard"], cwd=repository_name)
        subprocess.run(["git", "pull"], cwd=repository_name)

    # Navigate to the cloned repository
    os.chdir(repository_name)

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
    # 5 (in mm per square meter) is quite an arbitrary number to determine if it was a rainy day.
    for date in date_count:
        if get_weather_data(date[0:10], latitude, longitude) >= 5:
            commits_on_rainy_days += date_count[date]
        else:
            commits_on_sunny_days += date_count[date]

    print(f"Commits on rainy days: {commits_on_rainy_days}")
    print(f"Commits on sunny days: {commits_on_sunny_days}")
    if commits_on_sunny_days > commits_on_rainy_days:
        print("You are more productive on sunny days.\nBased on reliable data you actually can blame bad weather now!")
    else:
        print("You are more productive on rainy days.\nSeems like you enjoy coding when it rains.")


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

# TODO: error handling (wrong input parameters, more than 10,000 days/requests)
# TODO: host it on website
