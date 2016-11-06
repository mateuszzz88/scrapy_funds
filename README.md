# ScrapyFunds
## Crawls retirement policy site, extracts history of policy.
This project aims to make easier to understand what happens to my OpenLife pension fund. 
ScrapyFunds will download all available historical data about my pension fund and display it in explanatory graphs. 
This will help answer questions - "where did my money go?" and "which funds did better than others?".

## How is it achieved?
ScrapyFunds crawls OpenLife.org website, reads all available information and records it in database.
Later it displays data using dynamic and colorful graphs.
#### Technologies used:
* Python 2.6
* scrapy (https://scrapy.org/) for crawling pages
* django (https://www.djangoproject.com/) for displaying summary pages and database storage
* amCharts (https://www.amcharts.com/) for rendering graphs

## Features
* Downloads data from openlife.pl site
* Handles multiple users
* Download historic data about all the investment funds that were used: units owned, unit prices etc
* Compare with money actually spent - you will know whether you lost or gained money
* (work in progress, not ready yet) compare money transfers on separate funds. 
You will know wheter given fund is earning money or losing it.

## Wishlist
Features that I hope to implement in future:
* (work in progress, not ready yet) compare money transfers on separate funds. 
* support AxA pension fund (not likely feature, AxA gives less historical data)
* run crawler from page
* faster crawl of account_history (somehow do not iterate over all pages)
* faster crawl when nothing new (check last date given and iterate to this, not to today)
* export reports to zip
* display details on fund page - how much money was spent on fees

## License
If you want to use the code, just let me know. After that, all my code is licensed under MIT License.

