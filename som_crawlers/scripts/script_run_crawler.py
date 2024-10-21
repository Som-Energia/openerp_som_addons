# This script runs a crawler

# Imports
import click
import os
import importlib.util

# Arguments passed through the os systemm call


@click.command()
@click.option("-u", "--user", help="Username of the portal.", required=False)
@click.option(
    "-n", "--name", prompt="Crawler portal name", help="The person to greet.", required=False
)
@click.option("-p", "--password", help="Password of the portal.", required=False)
@click.option("-f", "--file", help="Log file name", required=False)
@click.option("-url", "--url", help="URL of the portal.", required=False)
@click.option("-fltr", "--filters", help="Filters URL.", required=False)
@click.option("-c", "--crawler", help="Crawler", required=False)
@click.option("-d", "--days", help="Days of margin", required=False)
@click.option("-nfp", "--pfiles", help="Pending files only", required=False)
@click.option("-b", "--browser", help="Browser", required=False)
@click.option("-pr", "--process", help="Process to download", required=False)
@click.option("-url-upload", "--url-upload", help="Upload URL", required=False)
@click.option("-fp", "--file-path", help="Upload file path.", required=False)
# Function that runs de crawler of the crawler saves the user and the date when
# it was modified and returns the new password.
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
def crawl(
    user,
    name,
    password,
    file,
    url,
    filters,
    crawler,
    days,
    pfiles,
    browser,
    process,
    url_upload,
    file_path=None,
):
    path = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists("/tmp/outputFiles/"):
        os.mkdir("/tmp/outputFiles/")
    f = open(os.path.join("/tmp/outputFiles/", file), "w")
    try:
        crawler_conf = {
            "crawler": crawler,
            "days_of_margin": days,
            "pending_files_only": pfiles,
            "browser": browser,
        }
        portalCreds = buildPortalCreds(
            user,
            password,
            url,
            filters,
            crawler,
            days,
            pfiles,
            browser,
            process,
            url_upload,
            file_path,
        )
        selenium_spiders_path = os.path.join(path, "../spiders/selenium_spiders")
        if process != "None":
            spec = importlib.util.spec_from_file_location(
                name, "".join([selenium_spiders_path, "/", name + "_" + process, ".py"])
            )
        else:
            spec = importlib.util.spec_from_file_location(
                name, "".join([selenium_spiders_path, "/", name, ".py"])
            )
        spider_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spider_module)
        spider_instance = spider_module.instance(crawler_conf)
        spider_instance.start_with_timeout(portalCreds, debug=True)
    except Exception as e:
        f.write(str(e))
        f.close()
        raise e
    else:
        if file_path:
            f.write("Files have been successfully uploaded")
        else:
            f.write("Files have been successfully downloaded")
        f.close()


def buildPortalCreds(
    user, password, url, filters, crawler, days, pfiles, browser, process, url_upload, file_path
):
    portalCreds = dict()
    portalCreds["username"] = user
    portalCreds["password"] = password
    portalCreds["url"] = url
    if filters != "None":
        portalCreds["filters"] = filters
    portalCreds["crawler"] = crawler
    portalCreds["days_of_margin"] = int(days)
    portalCreds["pending_files_only"] = eval(pfiles)
    portalCreds["browser"] = browser
    if process != "None":
        portalCreds["process"] = process
    portalCreds["url_upload"] = url_upload
    if file_path:
        portalCreds["file_path"] = file_path

    return portalCreds


# Main program crawler
if __name__ == "__main__":
    crawl()
