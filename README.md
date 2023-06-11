# PacktPub Downloader

Script to download all your PacktPub books inspired by https://github.com/ozzieperez/packtpub-library-downloader

Since PacktPub restructured their website [packtpub-library-downloader](https://github.com/ozzieperez/packtpub-library-downloader) became obsolete because the downloader used webscraping. So I figured out that now PacktPub uses a REST API. Then I found which endpoint to use for downloading books and made a simple script. Feel free to fork and PR to improve. Packtpub's API isn't documented :'(

## Usage:
    pip install -r requirements.txt
	python main.py -e <email> -p <password> [-d <directory> -b <book file types> -s -v -q]

##### Example: Download books in PDF format
	python main.py -e hello@world.com -p p@ssw0rd -d ~/Desktop/packt -b pdf,epub,mobi,code

## Docker integration

You must put your data in the `.env` file. 

```
mv data.env-sample data.env
```

and replace the sample data with your login credentials.

```
docker-compose up
```

After the execution, you can see the content in the `book` directory.


## Commandline Options
- *-e*, *--email* = Your login email
- *-p*, *--password* = Your login password
- *-d*, *--directory* = Directory to download into. Default is "media/" in the current directory
- *-b*, *--books* = Assets to download. Options are: *pdf,mobi,epub,code*
- *-s*, *--separate* = Create a separate directory for each book
- *-v*, *--verbose* = Show more detailed information
- *-q*, *--quiet* = Don't show information or progress bars
- *-a*, *--ask* = interactive download: ask to save each file
- *-l*, *--list* = list all books in account and their product ids
- *-u*, *--usecache* = use cache to reduce api calls
- *-i*, *--productids* = comma separated product ids to download
- *-u*, *--useragent* = string for custom user agent

**Book File Types**

- *pdf*: PDF format
- *mobi*: MOBI format
- *epub*: EPUB format
- *code*: Accompanying source code, saved as a .zip file
- *video*: For videos, this will download all videos and source saved as a .zip file

## Using the cache

The login token is always cached in a file called `mediatokencache.id` in the current working directory. If you get an error logging in, delete this file.

The `-c` argument activates the book list cache. It is stored in a file called `packt_cache_file.json` in the media output directory. To update the file list, just delete this file.

I'm working on Python 3.6.0 
