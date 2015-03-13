import os
import ConfigParser
from pp_utils import Monitor


class ResourceReader(object):
    config=None

    def __init__(self):
        self.mon=Monitor()


    def read(self,pp_dir,pp_home,pp_profile):
        if ResourceReader.config is None:
            # try inside profile
            tryfile=pp_profile+os.sep+"resources.cfg"
            # self.mon.log(self,"Trying resources.cfg in profile at: "+ tryfile)
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                # try inside pp_home
                # self.mon.log(self,"resources.cfg not found at "+ tryfile+ " trying pp_home")
                tryfile=pp_home+os.sep+"resources.cfg"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    # try inside pipresents
                    # self.mon.log(self,"resources.cfg not found at "+ tryfile + " trying inside pipresents")
                    tryfile=pp_dir+os.sep+'pp_resources'+os.sep+"resources.cfg"
                    if os.path.exists(tryfile):
                        filename=tryfile
                    else:
                        self.mon.log(self,"resources.cfg not found at "+ tryfile)
                        self.mon.err(self,"resources.cfg not found")
                        return False   
            ResourceReader.config = ConfigParser.ConfigParser()
            ResourceReader.config.read(filename)
            self.mon.log(self,"resources.cfg read from "+ filename)
            return True
        

    def get(self,section,item):
        if ResourceReader.config.has_option(section,item) is False:
            return False
        else:
            return ResourceReader.config.get(section,item)
    

        


