# Tips and Tricks

## Octo Reminder - your friendly assistant

Are you tired of keeping track of planned changes or issues you scheduled for the future? Our [Octo Reminder](https://github.com/apps/octo-reminder) is here to safe you from unneeded cognitive load!

The app configuration is stored in our [`.github`](https://github.com/SovereignCloudStack/.github/) repository. Using the bot is fairly simple:

- To schedule a reminder, simply comment with `/remind-me [date] [message]` on an issue or pull request. The bot will answer and mention you in the particular issue/pull request upon reaching the configured date.
- If you don't specify a time for the reminder, the bot will use 9:00 CET as default reminder time.
- The date and time can be anything that [momentjs](https://momentjs.com/docs/#/parsing/) understands, e.g. an ISO 8601 string or a relative string such as `tomorrow` or `next week`.