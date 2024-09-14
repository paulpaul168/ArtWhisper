# Crawler

The crawlers task is two fold, it downloads the metadata artworks to put them
into the database of the backend. It also downloads the images itself, which 
will not be stored in the database but are used to build our custom 
classification system to do artwork detection on mobile devices.

## Caching
The crawler does some aggressive caching, and stores all metatdata in 
`belvedere_data` and the images in `belvedere_images`.

Those folders contents are also pushed into the repo so that you can quickly
fill the db without accessing to much of the belvedere page.

In case you want to invalidate the cache run:

```bash
rm belvedere_data/*.json
rm belvedere_images/*.jpeg
```

## Single Threaded mode
The output of the crawler can be a bit confusing since it runs concurrently by 
default. For debugging purposes you can force it to a single thread with:

```bash
python crawler.py --single-threaded
```
