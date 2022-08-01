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

import sys
import click

@click.command()
@click.option('-u', '--user', help='Username of the portal.', required=True)
@click.option('-n', '--name', prompt='Crawler portal name',help='The person to greet.', required=True)
@click.option('-p', '--password', help='Password of the portal.', required=True)
@click.option('-f', '--file', help='Log file name', required=True)
@click.option('-url', '--url', help='URL of the portal.', required=True)
@click.option('-fltr', '--filters', help='Filters.', required=True)

#sys.argv[1] es tota la informacio d'una configuració qualsevol que estigui executant la tasca

def crawl(user, name, password, file, url, filters):
    f = open("/home/somenergia/src/openerp_som_addons/som_crawlers/outputFiles/" + file,'w')
    wc = WebCrawler()
    try:
        spider_instance = anselmo.Anselmo(wc.selenium_crawlers_conf[name])
        portalCreds = dict()
        portalCreds['username'] = user
        portalCreds['password'] = password
        portalCreds['url'] = url
        portalCreds['filters'] = filters
        spider_instance.start_with_timeout(portalCreds, debug=True)
        f.write('Files have been successfully downloaded')
    except Exception as e:
        f.write(str(e))




if __name__ == '__main__':
    crawl()