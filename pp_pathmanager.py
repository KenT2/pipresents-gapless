import copy


class PathManager(object):

    def __init__(self):
        
        self.debug=False   #shows the path commands and the stack

        # self.debug=True
        
        self.path_stack=[]

        
    # pops back to 'stop_at' 
    # then pops back one further and returns the track-ref of this track for replaying
    # if stop-at is not found returns ''

    def back_to(self,stop_at,):
        if self.debug: print 'pathmanager command - back_to: ',stop_at
        for page in self.path_stack:
            if page[0] ==  stop_at:
                break
        else:
            return ''
        
        # found, so pop until we reach it
        while self.path_stack[len(self.path_stack)-1][0] != stop_at:
            self.path_stack.pop()
        track_to_play = self.path_stack[len(self.path_stack)-1][0]
        self.path_stack.pop()
        return track_to_play


    # pops back 'number' tracks or to 'stop_at' whichever is first
    # then pops back one further and returns the track-ref of this track for replaying
    # if stop-at is not found and everything is popped the stack is left empty and the first track is returned

    def back_by(self,stop_at,back_by_text='1000'):
        if self.debug:  print 'pathmanager command  -   back by: ',back_by_text,' or stop at: ',stop_at
        back_by=int(back_by_text)
        count=0
        while self.path_stack != []:
            top = self.path_stack.pop()
            if top[0] ==  stop_at or count ==  back_by-1:
                break
            count=count+1
        # go back 1 if not empty
        if self.path_stack != []:
            top=self.path_stack.pop()
        track_to_play = top[0]
        if self.debug: 
            print '   removed for playing: ',track_to_play
        return track_to_play
    
    def append(self,page):
        if self.debug:  print 'pathmanager command - append: ',page
        self.path_stack.append([page])


    def empty(self):
        self.path_stack=[]


    # sibling - just pop the media track so sibling is appended and can go back to page track
    def pop_for_sibling(self):
        if self.debug: print 'pathmanger command - pop for sibling: '
        self.path_stack.pop()


        
    def pretty_path(self):
        path= '\nPath now is:'
        for page in self.path_stack:
            path  += "\n      " + page[0]
        print
        return path
 

# *******************   
# Extract links
# ***********************

    def parse_links(self,links_text,allowed_list):
        links=[]
        lines = links_text.split('\n')
        num_lines=0
        for line in lines:
            if line.strip() ==  "":
                continue
            num_lines+=1
            error_text,link=self.parse_link(line,allowed_list)
            if error_text != "":
                return 'error',error_text,links
            links.append(copy.deepcopy(link))
        # print "\nreading"
        # print links
        return 'normal','',links

    def parse_link(self,line,allowed_list):
        fields = line.split()
        if len(fields)<2 or len(fields)>3:
            return "incorrect number of fields in command",['','','']
        symbol=fields[0]
        operation=fields[1]
        if operation in allowed_list or operation[0:4] == 'omx-' or operation[0:6] == 'mplay-'or operation[0:5] == 'uzbl-':
            if len(fields) ==  3:
                arg=fields[2]
            else:
                arg=''                                                                                                                                                                                          
            return '',[symbol,operation,arg]
        else:
            return "unknown operation: "+operation,['','','']


    def merge_links(self,current_links,track_links):
        for track_link in track_links:
            for link in current_links:
                if track_link[0] ==  link[0]:
                    # link exists so overwrite
                    link[1]=track_link[1]
                    link[2]=track_link[2]
                    break
            else:
                # new link so append it
                current_links.append(track_link)
        # print "\n merging"
        # print current_links
                        
    def find_link(self,symbol,links):
        for link in links:
            # print link
            if symbol ==  link[0]:
                return True,link[1],link[2]
        return False,'',''

