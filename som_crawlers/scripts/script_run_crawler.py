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

wc = WebCrawler()
try:
    spider_instance = anselmo.Anselmo(wc.selenium_crawlers_conf[str(sys.argv[1])])
    spider_instance.start_with_timeout(debug=True)
    print('Files have been successfully downloaded')
except Exception as e:
    print(e)

