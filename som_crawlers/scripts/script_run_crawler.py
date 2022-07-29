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


#sys.argv[1] es tota la informacio d'una configuració qualsevol que estigui executant la tasca

def crawl(user, name, password):
    wc = WebCrawler()
    import pudb; pu.db
    try:
        spider_instance = anselmo.Anselmo(wc.selenium_crawlers_conf[name])
        portalCreds = dict()
        portalCreds['username'] = user
        portalCreds['password'] = password
        spider_instance.start_with_timeout(portalCreds, debug=True)
        print('Files have been successfully downloaded')
    except Exception as e:
        print(e)




if __name__ == '__main__':
    crawl()