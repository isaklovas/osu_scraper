# osu_scraper

more or less a working version of [this script](https://github.com/Anohji/better_osu_scraper)

# usage

`$ python scrape.py [country code] [start page] [end page]`

or pass `global` as the country code to scrape the global rankings

you can also pass the `--detailed` flag to scrape more data from each user

# example

`$ python scrape.py no 1 200 --detailed`
