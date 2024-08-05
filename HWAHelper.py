import win32gui
import win32con
import time as t
import pygame
import ctypes
import os
import sys
#:UPDATE (did you fix the self.saveinfo, if applicable?) Change the version below!
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HWAlarm v0.3')
DISP_WIDTH, DISP_HEIGHT = 500,500

def convert_weekday(wday) -> str:
    if (wday < 0) or (wday > 6):
        return None
    return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][wday]
class Task:
    def __init__(self, name: str, tasktime: t.struct_time, course = None) -> None:
        #Fields of inst. of Task are public
        self.name = name
        self.tasktime = tasktime
        self.course = course
    
    def __str__(self) -> str:
        return f"Task name {self.name}\nfor {self.course}\ndue {convert_weekday(self.tasktime[6])}, {self.tasktime[0]}/{self.tasktime[1]}/{self.tasktime[2]} {self.tasktime[3]}:00"
    def task_due_time(self) -> str:
        return f"{convert_weekday(self.tasktime[6])}, {self.tasktime[0]}/{self.tasktime[1]}/{self.tasktime[2]} {self.tasktime[3]}:00"
class Alert: ## a class for which an instance is dedicated to inherit "close-to-duedate" (and uncleared overdue) tasks (and "flash orange")
    def __init__(self, alarm) -> None:
        self.upcoming = []#(task,*-1,0,1,2,3*)] <- -1: !!!OVERDUE!!!, 0: due in less than 1hr, 1: due in 3 hours, 2: due in 12 hours, 3: due in 1 day, 4: due in 3 days
        self.upcoming_raw = []#only stores task
        self.alarm = alarm
        self.dnd = False
    def update_alert(self) -> None:
        currt = t.time()
        #cleanup
        hold = []
        for x in self.upcoming_raw:
            if x in self.alarm.task_list:
                hold.append(x)
        self.upcoming_raw.clear()
        for x in hold:
            self.upcoming_raw.append(x)
        
        #check all tasks in the task list and see if alert is needed
        for i in self.alarm.task_list:
            if i in self.upcoming_raw:
                continue
            if t.mktime(i.tasktime) < currt:
                self.upcoming.insert(0,(i,-1,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 3600:
                self.upcoming.insert(0,(i,0,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 10800:
                self.upcoming.insert(0,(i,1,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 43200:
                self.upcoming.append((i,2,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 86400:
                self.upcoming.append((i,3,True))
                self.upcoming_raw.append(i)
            elif t.mktime(i.tasktime) - currt <= 259200:
                self.upcoming.append((i,4,True))
                self.upcoming_raw.append(i)
        for _,alertType,unchecked in self.upcoming:
            if unchecked and alertType < 3:
                flash(self.alarm.hwnd)
                break
        self.alarm.alert_updated()
        #print(self.alarm.task_list,self.upcoming)
class Alarm_window:
    def __init__(self, setupTuple: tuple, save_file = None) -> None:
        #save_file is a string (path), if applicable.
        self.disp = setupTuple[0]
        self.hwnd = setupTuple[1]
        self.screen_top_y = 0 #stores the vertical scroll
        self.max_y = 0
        self.task_list = []
        self.sysfonts = pygame.font.get_fonts()
        self.alert_ud_time = 0
        if save_file != None and os.path.isfile(save_file):
            #"load" the file if file is given; "try".
            try:
                with open(save_file, "r") as f:
                    raw = f.read().split("\n")
                f.close()
                trim = raw[match_front_substr(raw, "{")+1:match_front_substr(raw,"}")]
                curr_task_num = 0
                point = 1
                while curr_task_num < int(trim[0]):
                    a = match_front_substr(trim[point:], "[") + point
                    b = match_front_substr(trim[point:], "]") + point
                    assert(match_front_substr(trim[a:b], "Task name ") == 1)
                    assert(match_front_substr(trim[a:b], "for ") == 2)
                    assert(match_front_substr(trim[a:b], "due ") == 3)
                    assert(trim[a+4] == " ^ at index " + str(curr_task_num)) # <= ensures that the tasks are in correct, time-ascending order
                    #check complete
                    self.task_list.append(Task(trim[a+1][10:], t.strptime(trim[a+3][trim[a+3].index(", ")+2:-3], "%Y/%m/%d %H"), trim[a+2][4:]))
                    point = b+1
                    curr_task_num += 1
                
                #comply with the file saveinfo
                self.saveinfo = []
                while (trim[point][0] == ":"):
                    self.saveinfo.append(trim[point][1:])
                    point += 1
                #fix types (:UPDATE)
                self.saveinfo[0] = int(self.saveinfo[0])
                self.saveinfo[2] = int(self.saveinfo[2])
                self.saveinfo[3] = int(self.saveinfo[3])
                self.saveinfo[4] = int(self.saveinfo[4])
                self.saveinfo[5] = int(self.saveinfo[5])
                self.saveinfo[6] = int(self.saveinfo[6])
                self.saveinfo[7] = int(self.saveinfo[7])
                self.saveinfo[8] = int(self.saveinfo[8])
                self.saveinfo[9] = int(self.saveinfo[9])
                if self.saveinfo[0] == 0:
                    self.font = pygame.font.SysFont(self.saveinfo[1], self.saveinfo[2])
                else:
                    self.font = pygame.font.Font(self.saveinfo[1], self.saveinfo[2])
                self.save_location = save_file
                self.lineht = self.font.get_linesize()
                self.text_info("The save was successfully loaded.\nPress any key to continue.", window_size = self.disp.get_size())
            except:
                #oof
                self.task_list = [] #ensure nothing gets changed
                self.saveinfo = [0, self.sysfonts[0], 20, 0, 0, 0, 0, 0, 0, 0]
                self.font = pygame.font.SysFont(self.sysfonts[0], 20)
                self.save_location = None
                self.lineht = self.font.get_linesize()
                self.text_info("Loading the save failed.\nCheck your file and try again.\nPress any key to continue.", window_size = self.disp.get_size())
        else:
            self.font = pygame.font.SysFont(self.sysfonts[0], 20)
            self.lineht = self.font.get_linesize()
            self.saveinfo = [0, self.sysfonts[0], 20, 0, 0, 0, 0, 0, 0, 0]
            self.save_location = None
    def __str__(self) -> str:
        return_str = str(len(self.task_list))+ "\n"
        ind = 0
        for task in self.task_list:
            #return_str += ("\n" if ind > 0 else "") + str(task) + "\n ^ at index "+str(ind)+"\n"
            return_str += "[\n" + str(task) + "\n ^ at index "+str(ind)+"\n]\n"
            ind += 1
        for i in range(len(self.saveinfo)):
            return_str += f":{self.saveinfo[i]}\n"
        return_str += (str("Saved to " + os.path.abspath(self.save_location) + "\n}") if self.save_location != None else "No local save\n}")
        return "{\n" + return_str
    def clear(self) -> None:
        self.disp.fill((240,240,240))
    def add_task(self) -> None:
        a = ""
        try:
            a = self.text_input("Enter the name of the new task (to cancel, enter without typing): ")
            assert(a.lower() != "")
            b, c = t.strptime(self.text_input("Enter the due date in this form - YYYY/MM/DD hh (24-hr-format): "), "%Y/%m/%d %H"), self.text_input("Enter the class name: ")
            ind = 0
            for i in range(len(self.task_list)):
                if self.task_list[i].tasktime > b:
                    break
                ind += 1
            self.task_list.insert(ind,Task(a,b,c))
        except:
            if a.lower() != "":
                if self.text_input("Something went wrong.\n\nPress enter to try again. Type anything to stop/cancel.") == "":
                    self.add_task()
    def remove_task(self) -> None:
        if len(self.task_list) > 0:
            try:
                tsk_index = int(self.text_input(f"Select the index of the task to remove (0 to {len(self.task_list) - 1}): "))
                if self.text_input(f"Are you sure you want to clear:\n\"{self.task_list[tsk_index]}\"\n? If so, type enter. If not, type anything else then press enter.") == "":
                    self.task_list.pop(tsk_index)
            except:
                if self.text_input("Something went wrong.\n\nPress enter to try again. Type anything to stop/cancel.") == "":
                    self.remove_task()
        else:
            self.text_info("Homework list is already cleared!")
    def update_alarm(self) -> None:
        #first draw Alert update state
        self.alert_splash()
        #draw all current "alarmstuff"
        curr_y = 0
        max_x, max_y = pygame.display.get_window_size()
        max_y += self.screen_top_y
        l_count = 0
        
        for i in self.task_list:
            """
            if curr_y < self.screen_top_y:
                curr_y += self.lineht*len(add_linebreak(self.font, str(i), max_x).split("\n"))
                continue
            """
            if curr_y >= max_y:
                break
            line_broken_i = add_linebreak(self.font, "for " + i.course + ", due " + i.task_due_time(), max_x).split('\n')
            line_broken_taskname = add_linebreak(self.font, i.name, max_x).split('\n')
            #blit
            
            for line in range(len(line_broken_taskname)):
                self.disp.blit(self.font.render(line_broken_taskname[line], True, (150,0,0)), (0,curr_y - self.screen_top_y))
                curr_y += self.lineht
                l_count += 1
            for line in range(len(line_broken_i)):
                self.disp.blit(self.font.render(line_broken_i[line], True, (0,0,0)), (0,curr_y - self.screen_top_y))
                curr_y += self.lineht
                l_count += 1
            curr_y += self.lineht
        
        self.max_y = l_count*self.lineht
    def alert_updated(self):
        self.alert_ud_time = t.time()
        
    #vv Add this to *every* display modifications, before doing anything
    def alert_splash(self):
        dt = min(t.time() - self.alert_ud_time,5)
        pygame.draw.rect(self.disp, (int(40*dt),255 - int(11*dt),int(40*dt)), pygame.Rect(self.disp.get_width() - 20, 0, 20, 20))
    def scroll_line(self,up_or_down: bool) -> None:
        if up_or_down:
            #up
            self.screen_top_y = max(0,self.screen_top_y - self.lineht)
        else:
            #down
            self.screen_top_y = max(0, min(self.max_y - pygame.display.get_window_size()[1],self.screen_top_y + self.lineht))
        #test purposes: print(self.screen_top_y, self.max_y)
    def get_num_tasks(self) -> int:
        return len(self.task_list)
    def splash_nullscreen(self) -> None:
        splash = self.font.render("To get started, left click this display.", True, (50,50,50))
        self.disp.blit(splash, ((self.disp.get_width() - splash.get_width())//2,(self.disp.get_height() - splash.get_height())//2))
    
    def text_input(self, prompt: str, window_center_pos = (None, None), window_size = (None, None)) -> str:
        #"None" in any of the window_center_pos, window_size => default:
        if (window_center_pos[0] == None or window_center_pos[1] == None):
            window_center_pos = (self.disp.get_width()//2, self.disp.get_height()//2)
        if (window_size[0] == None or window_size[1] == None):
            window_size = (self.disp.get_width()//2, self.disp.get_height()//2)
        #"window" tl: (wcp[0] - (ws[0]/2), wcp[1] - (ws[1]/2))
        
        prompt_lbreak = add_linebreak(self.font, prompt, window_size[0] - 50).split("\n") ##a list of text broken up into
        text_input_window = pygame.Surface(window_size);text_input_window.fill((255,255,255))
        height_holder = self.lineht
        for line in prompt_lbreak:
            c_render = self.font.render(line, True, (0,0,0), (255,255,255))
            text_input_window.blit(c_render, ((window_size[0] - c_render.get_width())//2, height_holder))
            height_holder += self.lineht
        
        #Text input display, bottom side being 2*lineht px away from the window
        #rectangle with border width 2 px, width is max(104,window_size[0] - 96), height lineht + 4 px
        #this goes to the loop -> pygame.draw.rect(text_input_window, (0,0,0), pygame.Rect((window_size[0] - max(104, window_size[0] - 96))//2, window_size[1] - (3*self.lineht + 2), max(104, window_size[0] - 96), self.lineht + 4), 2)
        #"max text width" is always max(80, window_size[0] - 120) <= always gives 10 px padding on each side
        input_ctn = True
        input_text = ""
        pointer_ind = 0 ##ex. for text "1234", pointer_index = 1 if the pointer is currently in between 1 and 2
        c = pygame.time.Clock()
        while input_ctn:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    text_input_window.fill((255,255,255), pygame.Rect((window_size[0] - max(100, window_size[0] - 100))//2, window_size[1] - (3*self.lineht), max(100, window_size[0] - 100), self.lineht))
                    if event.key == pygame.K_RETURN:
                        input_ctn = False
                    elif event.key == pygame.K_BACKSPACE:
                        if pointer_ind > 0:
                            input_text = input_text[:pointer_ind-1] + input_text[pointer_ind:]
                            pointer_ind -= 1
                    elif event.key == pygame.K_DELETE:
                        if pointer_ind < len(input_text):
                            input_text = input_text[:pointer_ind] + input_text[pointer_ind+1:]
                    elif event.key == pygame.K_LEFT:
                        pointer_ind -= 1
                        pointer_ind = max(0,pointer_ind)
                    elif event.key == pygame.K_RIGHT:
                        pointer_ind += 1
                        pointer_ind = min(len(input_text),pointer_ind)
                    else:
                        input_text = input_text[:pointer_ind] + event.unicode + input_text[pointer_ind:]
                        pointer_ind += 1
            self.alert_splash()
            cutoff = 0
            while (self.font.size(input_text[cutoff:])[0] > max(100, window_size[0] - 100)):
                cutoff += 1
            if (cutoff > pointer_ind):
                text_input_window.blit(self.font.render(input_text[pointer_ind:(pointer_ind - cutoff)], True, (0,0,0), (255,255,255)), ((window_size[0] - max(100, window_size[0] - 100))//2, window_size[1] - (3*self.lineht)))
                pygame.draw.line(text_input_window, (50,50,255), ((window_size[0] - max(100, window_size[0] - 100))//2, window_size[1] - (3*self.lineht)),((window_size[0] - max(100, window_size[0] - 100))//2, window_size[1] - (2*self.lineht)),2)
            else:
                text_input_window.blit(self.font.render(input_text[cutoff:], True, (0,0,0), (255,255,255)), ((window_size[0] - max(100, window_size[0] - 100))//2, window_size[1] - (3*self.lineht)))
                pygame.draw.line(text_input_window, (50,50,255), ((window_size[0] - max(100, window_size[0] - 100))//2 + self.font.size(input_text[cutoff:pointer_ind])[0], window_size[1] - (3*self.lineht)),((window_size[0] - max(100, window_size[0] - 100))//2  + self.font.size(input_text[cutoff:pointer_ind])[0], window_size[1] - (2*self.lineht)),2)
            self.disp.blit(text_input_window, (window_center_pos[0] - (window_size[0]//2), window_center_pos[1] - (window_size[1]//2)))
            pygame.draw.rect(text_input_window, (0,0,0), pygame.Rect((window_size[0] - max(104, window_size[0] - 96))//2, window_size[1] - (3*self.lineht + 2), max(104, window_size[0] - 96), self.lineht + 4), 2)
            pygame.display.flip()
            c.tick(20)
        return input_text
    
    def text_info(self, infotext: str, window_center_pos = (None, None), window_size = (None, None)) -> None:
        ##~
        if (window_center_pos[0] == None or window_center_pos[1] == None):
            window_center_pos = (self.disp.get_width()//2, self.disp.get_height()//2)
        if (window_size[0] == None or window_size[1] == None):
            window_size = (self.disp.get_width()//2, self.disp.get_height()//2)
        ##~ copied from text_input
        
        text_lbreak = add_linebreak(self.font, infotext, window_size[0] - 50).split("\n") ##a list of text broken up into
        info_window = pygame.Surface(window_size);info_window.fill((255,255,255))
        height_holder = self.lineht
        for line in text_lbreak:
            c_render = self.font.render(line, True, (0,0,0), (255,255,255))
            info_window.blit(c_render, ((window_size[0] - c_render.get_width())//2, height_holder))
            height_holder += self.lineht
        
        splash = True
        c = pygame.time.Clock()
        while splash:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    splash = False
            self.alert_splash()
            self.disp.blit(info_window, (window_center_pos[0] - (window_size[0]//2), window_center_pos[1] - (window_size[1]//2)))
            pygame.display.flip()
            c.tick(20)
    
    
    def change_font(self) -> None:
        #pops option to change the font from the "default" font
        def choose_font(inst: Alarm_window, option: str) -> (int, str):
            f = False
            while True:
                if option == "1":
                    #from system fonts
                    if not f:
                        sysfonts = pygame.font.get_fonts()
                        p = ""
                        for sf in sysfonts:
                            p += sf + ", "
                        p = p[:-2]
                        try:
                            i = inst.text_input("Available fonts are:\n" + p + ".\nType the name of the font, or \"cancel\" to quit.").lower()
                            if i == "cancel":
                                return (0, None)
                            pygame.font.SysFont(i, 20)
                            return (1, i)
                        except:
                            f = True
                    else:
                        inst.text_info("Something went wrong.\nPress any key to try again.")
                        f = False
                else:
                    #custom PATH
                    if not f:
                        try:
                            i = inst.text_input("Enter the path to the font, or \"cancel\" to quit.").lower()
                            if i == "cancel":
                                return (0, None)
                            pygame.font.Font(i, 20)
                            return (1, i)
                        except:
                            f = True
                    else:
                        inst.text_info("Something went wrong.\nPress any key to try again.")
                        f = False
        def choose_size(inst: Alarm_window, fontstr: str, option: str) -> (int, pygame.font.Font, int):
            #(1, font, n): normal output
            #(0, None, n): cancel
            #(2, None, n): start over
            f = False
            while True:
                if not f:
                    try:
                        i = inst.text_input("Enter the size of the font in pixels, at least 4 and at most 50.\nEnter \"cancel\" to quit, or \"restart\" to start over.").lower()
                        if i == "cancel":
                            return (0, None)
                        if i == "restart":
                            return (2, None)
                        i = int(float(i))
                        if i < 4 or i > 50:
                            f = True
                            continue
                        if option == "1":
                            return (1, pygame.font.SysFont(fontstr, i), i)
                        else:
                            return (1, pygame.font.Font(fontstr, i), i)
                    except:
                        f = True
                else:
                    inst.text_info("Something went wrong.\nPlease enter a valid number.\nPress any key to try again.")
                    f = False
        while True:
            option = self.text_input("Do you want to choose from system fonts list (1), or to instead type the file path to the font file (2)? Type 1 or 2 (\"cancel\" to cancel)")
            if option == "1" or option == "2":
                fontchoice = choose_font(self, option)
                if fontchoice[0] == 0:
                    break
                font_name = fontchoice[1]
                fontchoice = choose_size(self, font_name, option)
                if fontchoice[0] == 0:
                    break
                if fontchoice[0] == 2:
                    continue
                prev_font = self.font
                self.font = fontchoice[1]
                prev_lineht = self.lineht
                self.lineht = self.font.get_linesize()
                confirm = self.text_input("This text is being displayed with the chosen font.\nIf it looks good, enter \"ok\"; otherwise, the font will return to previous setting.").lower()
                if confirm != "ok":
                    self.font = prev_font
                    self.lineht = prev_lineht
                    self.text_info("The font setting was not changed.")
                    break
                
                #change the saveinfo
                self.saveinfo[0] = int(option)-1
                self.saveinfo[1] = font_name
                self.saveinfo[2] = fontchoice[2]
                self.text_info("The font was successfully changed.")
                break
            elif option.lower() == "cancel":
                break
            else:
                self.text_info("Something went wrong.\nPlease enter 1 or 2.\nPress any key to try again.")
        
    def exit(self) -> None:
        #To handle the exit sequence, regardless of where it is called (i.e. save alarm state, etc.)
        if self.text_input("Exit without saving? (enter \"yes\" if so; otherwise, the save sequence will be initiated)").lower() == "yes":
            sys.exit()
        self.save()
        sys.exit()
    def change_save(self) -> int:
        #save-changing protocol
        #I'm a psycho and use 1 as normal exit instead of 0
        if self.save_location != None:
            if self.text_input(f"Current save location is {os.path.abspath(self.save_location)}.\nType anything to change the save location.").lower() == "":
                return 1
        while True:
            save_path = self.text_input("Enter the path (either absolute or relative to the current directory) to the directory that the new save location will be placed (excluding filename/extension).\nType nothing will select the current directory.\nEnter \"cancel\" to abort.", window_size = self.disp.get_size())
            if save_path == "cancel":
                return 0
            if save_path == "":
                save_path = os.getcwd()
            if not os.path.isdir(save_path):
                self.text_info("The path entered is invalid.\nPress any key to try again")
                continue
            save_name = self.text_input("Enter the name of the save file") + ".hwa"
            self.save_location = os.path.normcase(os.path.normpath(os.path.join(save_path, save_name)))
            break
        self.save()
        return 1
    def save(self) -> int:
        if self.save_location == None:
            #well, save_location should be changed now
            if self.change_save() != 1:
                return 2 #user aborted
            return 1
        save_location = os.path.abspath(self.save_location)
        #path checks
        if not os.path.isdir(os.path.dirname(save_location)):
            #the directory DNE
            return 0
        
        #write to file
        try:
            if os.path.isfile(save_location):
                with open(save_location, "w") as f:
                    print(self, end = "", file = f)
            else:
                with open(save_location, "x") as f:
                    print(self, end = "", file = f)
            f.close()
        except:
            return 0
        return 1
    def open_new(self): # -> Alarm_window
        #ask for the path of the save file, then for saving (of the current alarm), (then save,) then open "a new Alarm window" on the same display.
        #will overwrite all data in the current object after clearing
        
        if self.text_input("Load a HWAlarm from a file without saving the current HWAlarm? (enter \"yes\" if so; otherwise, the save sequence will be initiated)").lower() != "yes":
            if self.save() == 0:
                self.text_info("An error occurred whilst trying to save.\nPress any key to change save path.")
                self.change_save()
        while True:
            load_path = self.text_input("Enter the path to the desired .hwa (HWAlarm) save file.\nEnter \"cancel\" to abort.", window_size = self.disp.get_size())
            if load_path == "cancel":
                return
            if not(("." in load_path) and load_path[-4:] != ".hwa"):
                load_path += ".hwa"
            if (not (os.path.isfile(load_path))):
                self.text_info("The path to the file entered is invalid.\nPress any key to try again")
                continue
            break
        return Alarm_window((self.disp, self.hwnd), load_path)
def setup() -> (pygame.Surface, int):
    pygame.init()
    pygame.display.set_icon(pygame.image.load("HWA_resources/HWA_icon.png"))
    #:UPDATE (look below)
    pygame.display.set_caption("HWAlarm v0.3")
    w = pygame.display.set_mode((DISP_WIDTH,DISP_HEIGHT), pygame.RESIZABLE)
    hwnd = pygame.display.get_wm_info()['window']
    return (w, hwnd)
def add_linebreak(font: pygame.font.Font, text: str, disp_width: int) -> str:
    if "\n" in text:
        #Manually handle \n already in the text, since font? pygame? assigns horizontal size to \n which
        #results in unexpected results
        new_line = text.index("\n")
        return add_linebreak(font, text[:new_line], disp_width) + "\n" + add_linebreak(font, text[new_line + 1:], disp_width)
    size = font.size(text)
    
    if len(text) == 1 or size[0] <= disp_width:
        return text
    else:
        curr_size = 0
        for i in range(len(text)):
            curr_size += font.size(text[i])[0]
            if curr_size > disp_width:
                #"split" at i; [0:i] and [i:]
                return text[:i] + "\n" + add_linebreak(font, text[i:], disp_width)
def flash(hwnd) -> None:
    win32gui.FlashWindowEx(hwnd, win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG, 1, 0)
def match_front_substr(lines: list[str], substr) -> int:
    #returns the index of the first occurrence of the line that starts with the substring substr.
    #otherwise, throw ValueError
    for i in range(len(lines)):
        if (lines[i][0:len(substr)] == substr):
            return i
    raise ValueError("No line matching the criteria was found.")