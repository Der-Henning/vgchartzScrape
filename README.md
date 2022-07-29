# VG Chartz full

vgchartzfull is a python script based on BeautifulSoup.
It creates a dataset based on data from 
http://www.vgchartz.com/gamedb/

The dataset is saved as vgsales.csv.

## Quickstart

### Using Docker

You can build an run the script using docker-compose. The resulting `.csv` file will be placed in the `./csv` folder.

````bash
docker-compose run scraper
````

### Without Docker

Install requirements and run the script. The resulting `.csv` file will be placed in the current working directory.

````bash
pip install -r requirements.txt
python vgchartzfull.py
````
