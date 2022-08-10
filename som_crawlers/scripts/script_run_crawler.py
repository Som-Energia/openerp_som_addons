from nturl2path import url2pathname
from massive_importer.crawlers.run_crawlers import WebCrawler
from massive_importer.crawlers.crawlers.spiders.selenium_spiders import anselmo
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

@click.command()
@click.option('-u', '--user', help='Username of the portal.', required=True)
@click.option('-n', '--name', prompt='Crawler portal name', help ='The person to greet.', required=True)
@click.option('-p', '--password', help='Password of the portal.', required = True)
@click.option('-f', '--file', help='Log file name', required = True)
@click.option('-url', '--url', help='URL of the portal.', required = True)
@click.option('-fltr', '--filters', help='Filters.', required = True)
@click.option('-c', '--crawler', help = 'Crawler', required = False)
@click.option('-d', '--days', help = 'Days of margin', required = True )
@click.option('-nfp', '--pfiles', help = 'Pending files only',required = True)
@click.option('-b', '--browser', help = 'Browser', required = True)

#sys.argv[1] es tota la informacio d'una configuració qualsevol que estigui executant la tasca

def crawl(user, name, password, file, url, filters, crawler, days, pfiles, browser):
    wc = WebCrawler()
    path = os.path.dirname(os.path.abspath(__file__))
    f = open(os.path.join(path,"../outputFiles",file),'w')
    try:
        spider_instance = anselmo.Anselmo(wc.selenium_crawlers_conf[name])
        portalCreds = dict()
        portalCreds['username'] = user
        portalCreds['password'] = password
        portalCreds['url'] = url
        portalCreds['filters'] = filters
        portalCreds['crawler'] = crawler
        portalCreds['days_of_margin'] = int(days)
        portalCreds['pending_files_only'] = eval(pfiles)
        portalCreds['browser'] = browser
        spider_instance.start_with_timeout(portalCreds, debug=True)
        f.write('Files have been successfully downloaded')
    
    except Exception as e:
        f.write(str(e))
if __name__ == '__main__':
    crawl()