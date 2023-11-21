import os
import sys
import subprocess
import requests

weather_api_url = "https://archive-api.open-meteo.com/v1/archive"


def main():
    repository_url = sys.argv[1]
    repository_name = repository_url.split('/')[-1].split('.')[0]
    latitude = sys.argv[2]
    longitude = sys.argv[3]

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

    all_commit_dates = f"../{repository_name}_log_dates.txt"
    with open(all_commit_dates, 'w') as file:
        file.write(date_string)

    # Create a list of dates
    dates = date_string.split('\n')

    # Create a dictionary to store the count of each date
    date_count = {}

    # Count the occurrences of each date
    for date in dates:
        date_count[date] = date_count.get(date, 0) + 1

    # Write the result to the output file
    all_commit_dates_aggregated = f"../{repository_name}_log_dates_aggregated.txt"
    with open(all_commit_dates_aggregated, 'w') as file:
        for date, count in date_count.items():
            file.write(f"{date}: {count}\n")

    # TODO: remove when done
    all_commit_dates_aggregated = f"../dummy_dates.txt"

    commits_on_rainy_days = 0
    commits_on_sunny_days = 0

    line_count = 0
    with open(all_commit_dates_aggregated, 'r') as file:
        while True:
            line_count += 1
            line = file.readline()
            if not line:
                break

            if get_weather_data(line[0:10], latitude, longitude) >= 10:
                commits_on_rainy_days += int(line[12])
            else:
                commits_on_sunny_days += int(line[12])

    print(f"Commits on rainy days: {commits_on_rainy_days}")
    print(f"Commits on sunny days: {commits_on_sunny_days}")


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

# TODO: avoid writing and reading to files. directly use dictionary
# TODO: remove unnecessary comments
# TODO: maybe visualize it somehow?
# TODO: error handling (wrong input parameters, more than 10,000 days/requests)
