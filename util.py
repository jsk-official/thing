import requests
import os
import shutil
import logging
import ipaddress
import maxminddb
import tarfile

from datetime import datetime
from pathlib import Path

"""
Lookups in the MaxMind GeoLite2 databases.

A license key is required as per [#GeoLite2_CCPA_GDPR]_:

#. Sign up for a MaxMind account (no purchase required): https://www.maxmind.com/en/geolite2/signup
#. Set your password and create a license key: https://www.maxmind.com/en/accounts/current/license-key
#. Setup your download mechanism by using our GeoIP Update program or creating a direct download script: https://dev.maxmind.com/geoip/geoipupdate/#Direct_Downloads

.. rubric:: Footnotes

.. [#GeoLite2_CCPA_GDPR] https://blog.maxmind.com/2019/12/18/significant-changes-to-accessing-and-using-geolite2-databases/
"""

logger = logging.getLogger(__name__)
directory = os.getcwd() + '/data'
Path(directory).mkdir(parents=True, exist_ok=True)

keylist = [
    'city',
    'subdivisions',
    'country',
] #list of location data keys (city, country, subdivisions)


class MaxMindDB:
    """
    This class provides functions to download, extract and get data from MaxMind DBs
    """

    # Dict to lookup const's, structured like this:
    # name given by MaxMind, name of the extracted DB, directory of the downloaded file from MaxMind
    helpers = {
        "city": ['GeoLite2-City_', 'GeoLite2-City.mmdb',str(Path(directory, ("GeoLite2-City.tar.gz").format(date=datetime.today().strftime('%Y%m%d'))))]
    }


    def __init__(self, url, query):
        self.MASTERURL = url
        self.query = query
        self.path_db = directory
        if MaxMindDB.get_db_path(self) is None:
            MaxMindDB.get_db(self)

    def get_db(self):
        """
        Download the MaxMind database in zip format from the MaxMind website

        """
        logger.debug('Downloading the '+self.helpers[self.query][2]+' DB ... ')
        try:
            response = requests.get(self.MASTERURL, stream=True)
        except Exception as e:
            logger.error('Reraising Exception raised by requests.get ({})'.format(e))
            raise e

        if response.status_code == 200:
            name = self.helpers[self.query][2]

            file = open(name, 'wb')
            file.write(response.content)
            file.close()

            if os.path.isdir('~/maxmindfiles'):
                shutil.rmtree('~/maxmindfiles')

            file = tarfile.open(name)
            file.extractall('~/maxmindfiles')
            file.close()

            dirname = os.listdir('~/maxmindfiles')[0]
            print(os.listdir('~/maxmindfiles/' + dirname))

            filename = '~/maxmindfiles/' + dirname + '/GeoLite2-City.mmdb'

            print(filename)
            print(os.listdir('~/maxmindfiles/' + dirname))
            
            reader = maxminddb.Reader(filename)

            combined = ''

            for ip in ipaddress.IPv4Network('128.116.0.0/17'):
                data = reader.get(ip)

                combined += str(ip) + ','

                for key in keylist:
                    if key in data:
                        values = data[key]
                        if key == 'subdivisions':
                            combined += values[0]['names']['en'] + ','
                        elif key == 'country':
                            combined += values['names']['en'] + '\n'
                        else:
                            combined += values['names']['en'] + ','
                    else:
                        combined += 'Unknown,'

            file = open('~/robloxasn.txt', 'w')
            file.write(combined)
            file.close()
        else:
            msg = (
                'Error while downloading the ASN DB '
                '(Status Code={}): {}'
            ).format(
                response.status_code,
                response.text,
            )
            logger.error(msg)
            raise Exception(msg)

    def get_db_path(self):
        """
        Return the ASN Database path if exists

        """
        filtered_dir = [x for x in os.listdir(
            self.path_db) if x.startswith(self.helpers[self.query][0])]
        sorted_dir = sorted(filtered_dir, reverse=True)
        if sorted_dir:
            return str(Path(
                directory,
                sorted_dir[0],
                self.helpers[self.query][1],
            ))
        else:
            return None
