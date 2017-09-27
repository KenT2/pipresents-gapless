class CounterManager(object):



    # *******************************************************************
    # use these functions to access the value of a counter or counters
    # *******************************************************************
    
    def get_counter(self,name):
        if name not in CounterManager.counters:
            return'error','counter does not exist - '+ name
        return 'normal',str(CounterManager.counters[name])

    def str_counters(self):
        values_string=''
        for key,value in CounterManager.counters.items():
            values_string += key +' '+str(value) + '\n'
        return values_string

    # *******************************************************************
    # use this function to print all counters to the terminal window
    # *******************************************************************
    def print_counters(self):
        print 'Counter Values:'
        for key,value in CounterManager.counters.items():
            print'      ',key,value

            

# **********************************************************************

    # dictionary of counter values
    counters = {}           

    def init(self):
        CounterManager.counters.clear()
    

    def parse_counter_command(self,fields):
        # counter name set    value
        # counter name inc    value
        # counter name dec    value
        # counter name delete

        if len(fields) < 2:
                return'error','too few fields in counter command - ' + ' '.join(fields)            
        name=fields[0]
        command=fields[1]
        
        if command =='set':
            value=fields[2]
            if not value.isdigit():
                return'error','value is not a positive integer - ' + ' '.join(fields)
            CounterManager.counters[name]=int(value)
            # self.print_command(fields)
            # self.print_counters()

            return 'normal',''
        
        elif command in ('inc','dec'):
            if name not in CounterManager.counters:
                return'error','counter does not exist - '+ ' '.join(fields)
            value=fields[2]
            if not value.isdigit():
                return'error','value is not a positive integer - '+ ' '.join(fields)

            if command=='inc':
                CounterManager.counters[name]+=int(value)
            else:
                CounterManager.counters[name]-=int(value)
            # self.print_command(fields)
            # self.print_counters()
            return 'normal','' 
            
        
        elif command =='delete':
            if name not in CounterManager.counters:
                return'error','counter does not exist - '+ ' '.join(fields)
            del CounterManager.counters[name]
            # self.print_command(fields)
            # self.print_counters()
            return 'normal',''
        
        else:
            return'error','illegal counter comand - '+ ' '.join(fields)


            

    def print_command(self,fields):
        print '\nCounter Command: ' + ' '.join(fields)

        

   
