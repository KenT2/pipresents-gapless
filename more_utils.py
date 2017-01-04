#Author Joe Houng

import sys
import re, datetime, os, shutil

# Filename in the form: filename[_dur][_start][_exp].ext
# Duration (dur) in seconds
# Start and expiration (exp) in ISO date format. If a full date format isn't given
#   missing elements are filled with "00".
# examples:
#   photo_dur5_start2016-12-31_exp2017-01-31.png
#   photo_dur5_start2016-12-31-00-00-00_exp2017-01-31-00-00-00
def ProcessFileName(Filename):
    #Split retrieved filename
    Dur = ""
    Start = ""
    Exp = ""
    SFileName = re.sub(r'\..+', "", Filename) 
    SFileName = SFileName.split("_")
    #Search through split filename for parameters dur, start, exp 
    for each in SFileName:
        if ("dur" in each):
            Dur = each.replace("dur", "")
            if Dur.isdigit() != True:
                Dur = ""
            #print Dur  
        if("start" in each):
            Start = each.replace("start", "")
            Start = completeISO(Start)
            if validate(Start) == -1:
                Start = ""
            #print Start
        if("exp" in each):
            Exp = each.replace("exp", "")
            Exp = completeISO(Exp)
            if validate(Exp) == -1:
                Exp = ""
            #print Exp  
    return [Dur, Start, Exp]

# Complete date string to ISO time standard of YYYY-MM-DD-HH-mm-ss
def completeISO(date):
    dateList = date.split("-")
    while(len(dateList) < 6):
        dateList.append("00")
    dateList = "-".join(dateList)
    return dateList

#varify date string is ISO time standard
def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d-%H-%M-%S')
        return 1
    except ValueError:
        return -1

#send a file to pp_home/pp_livetracks/Archived
def archive_file(file_path, pp_archive_dir):
    cwd = os.getcwd()
    parentDir = os.pardir
    dst = pp_archive_dir
    try:
        shutil.move(file_path, dst)
    except Exception as err:
        print("Error archiving {0}: \n   {1}".format(file_path, err))

