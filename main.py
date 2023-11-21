import os
import subprocess


def main():
    # Replace these variables with the actual owner and name of the repository
    repository_url = 'https://github.com/freeCodeCamp/freeCodeCamp.git'
    repository_name = repository_url.split('/')[-1].split('.')[0]

    # Check if the repository directory exists
    if not os.path.exists(repository_name):
        # Clone the repository
        subprocess.run(['git', 'clone', repository_url])
    else:
        # If the repository already exists, pull the latest changes
        subprocess.run(['git', 'reset', '--hard'], cwd=repository_name)
        subprocess.run(['git', 'pull'], cwd=repository_name)

    # Navigate to the cloned repository
    os.chdir(repository_name)

    # Specify the absolute path for the output file
    output_file = f'../{repository_name}_logs.txt'

    # Get the commit logs and save to the specified file
    with open(output_file, 'w') as file:
        subprocess.run(['git', 'log', '--pretty="%aD"'], stdout=file)

    print(f'Commit logs saved to {output_file}')


if __name__ == '__main__':
    main()
