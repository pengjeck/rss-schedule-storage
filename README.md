# RSS Schedule Storage

## What is it?
RSS Schedule Storage is a Python-based application designed to periodically fetch articles from specified RSS feed URLs and store them in a Google Spreadsheet. The application uses Flask for the web framework, APScheduler for scheduling tasks, and gspread for interacting with Google Sheets.

## Main Features of the Project
- **Scheduled RSS Feed Parsing**: The application reads RSS feed URLs from a text file and schedules regular fetching of articles using APScheduler.

- **Google Sheets Integration**: Fetched articles are stored in a Google Spreadsheet, making it easy to access and manage the data.

- **Efficient Article Downloading**: The application uses the `newspaper` library to download articles in batches, optimizing the process and reducing the time taken.

## Deploy to fly.io
This application is configured to be deployed on `fly.io` with the provided `fly.toml` configuration file. To deploy the application, follow these steps:
1. Install the `flyctl` command-line tool from [fly.io](https://fly.io/docs/getting-started/installing-flyctl/).
2. Authenticate with `fly.io` using `flyctl auth login`.
3. Navigate to the project directory and run `flyctl launch` to create and configure the app on `fly.io`.
4. Deploy the application using `flyctl deploy`.

## Contect
- [Twitter](https://twitter.com/pjwhusir)
- [Blog](http://journeypeng.best/)
- email: pjwhusir@gmail.com

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contribution
Contributions to the RSS Schedule Storage project are welcome. Please feel free to submit issues and pull requests through the GitHub repository.

## Support
If you encounter any issues or require assistance, please open an issue on the GitHub repository.

---
## Acknowledgements
Happy Coding!

> Part of the code is generate by [gpt4](https://chat.openai.com/)