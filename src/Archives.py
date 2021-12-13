import os, glob, shutil, datetime, gzip

from . import NJTransitAPI as njt

def filepath():
    path = ("data/")
    check = os.path.isdir(path)
    if not check:
        os.makedirs(path)
        print("created folder : ", path)
    else:
        pass
    return path

# future what about compressing and dumping to S3?
def dump_to_file(xml_data, timestamp):
    timestamp_pretty = timestamp.strftime("%Y-%m-%dT_%H:%M:%S.%f")
    raw_buses = njt.parse_xml_getBusesForRouteAll(xml_data)
    dumpfile=(filepath() + 'nj_buses_all_' + timestamp_pretty + '.gz')
    with gzip.open(dumpfile, 'wt', encoding="ascii") as zipfile:
        try:
            zipfile.write(xml_data)
        except:
            pass # if error, dont write and return
    return raw_buses


def rotate_files(): # https://programmersought.com/article/77402568604/
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1) # e.g. 2020-10-04
    # print ('today is {}, yesterday was {}'.format(today,yesterday))
    filepath = './data/'
    outfile = '{}daily-{}.gz'.format(filepath, yesterday)
    # print ('bundling minute grabs from {} into {}'.format(yesterday,outfile))
    all_gz_files = glob.glob("{}*.gz".format(filepath))
    yesterday_gz_files = []
    for file in all_gz_files:
        if file[7:17] == str(yesterday): # bug parse the path using os.path.join?
            yesterday_gz_files.append(file)
    with open(outfile, 'wb') as wfp:
        for fn in yesterday_gz_files:
            with open(fn, 'rb') as rfp:
                shutil.copyfileobj(rfp, wfp)
    for file in yesterday_gz_files:
        os.remove(file) #bug this isnt working?
