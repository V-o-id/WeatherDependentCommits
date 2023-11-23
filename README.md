# WeatherDependentCommits
### A nonsensical little script to analyze your commit log with weather data.
Does your back hurt? Does your coffe taste bad? Are you not feeling like making some commits today?
Well, it's probably the weather's fault.
Support your dear weather-blaming with reliable data!

## How to use
* Download the Python script.
* Open your terminal in its location and run it.
* There are two options for running the script:
  * Give the path to your local repository
    ```
    $ python weather.py <absolute-path-to-your-repo> <latitude-of-your-location> <longitude-of-your-location>
    ```
  * Give the URL to a repository on GitHub and clone it to the same folder as the script
    ```
    $ python weather.py <https://github.com/owner/repo.git> <latitude-of-your-location> <longitude-of-your-location> --d
    ```
  If you are too lazy to look up your coordinates, you can use those for Linz, Austria: 48.303056 14.290556

For each day a commit was made, a request to the meteorological API will be made, so the script does not scale well with lots of commits.
Also the limit of requests to the API is 10,000 per day, so if you committed every day for 28 years to your repository, you won't be able to use this tool (but you have my respects).
