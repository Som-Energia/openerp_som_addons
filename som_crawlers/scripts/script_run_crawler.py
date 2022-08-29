
 # This script runs a crawler

##Imports
from nturl2path import url2pathname
from massive_importer.crawlers.run_crawlers import WebCrawler
from massive_importer.crawlers.crawlers.spiders.selenium_spiders import *
from massive_importer.crawlers.crawlers.spiders.selenium_spiders import PortalConfig
from massive_importer.lib.exceptions import (
    CrawlingLoginException, CrawlingProcessException,
    FileToBucketException, CrawlingFilteringException,
    CrawlingDownloadingException
)
from massive_importer.lib.erp_utils import ErpManager
from massive_importer.conf import configure_logging, settings
import sys
import click
import os
import importlib

## Arguments passed through the os systemm call
@click.command()
@click.option('-u', '--user', help='Username of the portal.', required=True)
@click.option('-n', '--name', prompt='Crawler portal name', help ='The person to greet.', required=True)
@click.option('-p', '--password', help='Password of the portal.', required = True)
@click.option('-f', '--file', help='Log file name', required = True)
@click.option('-url', '--url', help='URL of the portal.', required = True)
@click.option('-fltr', '--filters', help='Filters.', required = False)
@click.option('-c', '--crawler', help = 'Crawler', required = True)
@click.option('-d', '--days', help = 'Days of margin', required = True)
@click.option('-nfp', '--pfiles', help = 'Pending files only',required = True)
@click.option('-b', '--browser', help = 'Browser', required = True)
@click.option('-pr', '--process', help = 'Process to download', required = False)

## Function that runs de crawler of the crawler saves the user and the date when it was modified and returns the new password.
        # @param user Username of the portal
        # @param name Crawler portal name
        # @param password Password of the portal
        # @param file Log file name
        # @param url URL of the portal
        # @param filters Filters
        # @param crawler Selenium crawler
        # @param days Days of margin
        # @param pfiles Pending files only
        # @param browser Browser
        # @return Exception or string if everything passed successfully
def crawl(user, name, password, file, url, filters, crawler, days, pfiles, browser, process):
    wc = WebCrawler()
    path = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(path,"../outputFiles/",file),'w')
    try:
        portalCreds = dict()
        portalCreds['username'] = user
        portalCreds['password'] = password
        portalCreds['url'] = url
        if filters!='None':
            portalCreds['filters'] = filters
        portalCreds['crawler'] = crawler
        portalCreds['days_of_margin'] = int(days)
        portalCreds['pending_files_only'] = eval(pfiles)
        portalCreds['browser'] = browser
        if process!='None':
            portalCreds['process'] = process
        selenium_spiders_path = os.path.join(
            path, "../spiders/selenium_spiders")
        spec = importlib.util.spec_from_file_location(
            name, "".join([selenium_spiders_path, "/", name, '.py']))
        spider_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spider_module)
        logger.debug("Loaded %s module" % (name))
        logger.debug("Starting %s crawling..." % (name))
        spider_instance = spider_module.instance(wc.selenium_crawlers_conf[name])
        spider_instance.start_with_timeout(portalCreds, debug=True)
        f.write('Files have been successfully downloaded')

    except Exception as e:
        f.write(str(e))

## Main program crawler
if __name__ == '__main__':
    crawl()
