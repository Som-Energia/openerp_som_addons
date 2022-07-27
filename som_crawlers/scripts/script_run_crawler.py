
from massive_importer.crawlers.run_crawlers import WebCrawler
from massive_importer.crawlers.crawlers.spiders.selenium_spiders import anselmo
from massive_importer.crawlers.crawlers.spiders.selenium_spiders import PortalConfig
print('Creant wc')
wc = WebCrawler()
print('cridant crawl')

spider_instance = anselmo.Anselmo(wc.selenium_crawlers_conf['anselmo'])
spider_instance.start_with_timeout(debug=True)


