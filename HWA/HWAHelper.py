import win32gui
import win32con
import time as t
import pygame
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HWAlarm v1.1')
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
        return f"\"{self.name}\"\n for {self.course}, due {convert_weekday(self.tasktime[6])}, {self.tasktime[0]}/{self.tasktime[1]}/{self.tasktime[2]} {self.tasktime[3]}:00"
    

class Alert: ## a class for which an instance is dedicated to inherit "close-to-duedate" (and uncleared overdue) tasks (and "flash orange")
    def __init__(self, alarm) -> None:
        self.upcoming = []#(task,*-1,0,1,2,3*)] <- -1: !!!OVERDUE!!!, 0: due in less than 1hr, 1: due in 3 hours, 2: due in 12 hours, 3: due in 1 day, 4: due in 3 days
        self.upcoming_raw = []#only stores task
        self.alarm = alarm
        self.dnd = False
    def update_alert(self) -> None:
        currt = t.time()
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
    def __init__(self, setupTuple: tuple) -> None:
        self.disp = setupTuple[0]
        self.hwnd = setupTuple[1]
        self.screen_top_y = 0 #stores the vertical scroll
        self.max_y = 0
        self.task_list = []
        self.font = pygame.font.Font("HWA_resources/Roboto-Medium.ttf", 20)
        self.lineht = self.font.get_linesize()
        self.alert_ud_time = 0
    def __str__(self) -> str:
        return_str = "{\n"
        ind = 0
        for task in self.task_list:
            return_str += str(task) + "\n ^ at index "+str(ind)+"\n,\n"
            ind += 1
        return return_str[:-2]+"\n}"
    def clear(self) -> None:
        self.disp.fill((240,240,240))
    def add_task(self) -> None:
        a = ""
        try:
            a = self.text_input("Enter the name of the new task (to cancel, type cancel): ")
            assert(a.lower() != "cancel")
            b, c = t.strptime(self.text_input("Enter the due date in this form - YYYY/MM/DD hh (24-hr-format): "), "%Y/%m/%d %H"), self.text_input("Enter the class name: ")
            ind = 0
            for i in range(len(self.task_list)):
                if self.task_list[i].tasktime > b:
                    break
                ind += 1
            self.task_list.insert(ind,Task(a,b,c))
        except:
            if a.lower() != "cancel":
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
            split_i = str(i).split("\n")
            line_broken_i = add_linebreak(self.font, split_i[1], max_x).split('\n')
            line_broken_taskname = add_linebreak(self.font, split_i[0], max_x).split('\n')
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
    
    ##Key component of #5
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
                    quit()
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
                    quit()
                elif event.type == pygame.KEYDOWN:
                    splash = False
            self.alert_splash()
            self.disp.blit(info_window, (window_center_pos[0] - (window_size[0]//2), window_center_pos[1] - (window_size[1]//2)))
            pygame.display.flip()
            c.tick(20)
    
    def exit(self) -> None:
        #To handle the exit sequence, regardless of where it is called (i.e. save alarm state, etc.)
        #TODO
        return None
def setup() -> (pygame.Surface, int):
    pygame.init()
    pygame.display.set_icon(pygame.image.load("HWA_resources/HWA_icon.png"))
    pygame.display.set_caption("HWAlarm v1.1")
    w = pygame.display.set_mode((DISP_WIDTH,DISP_HEIGHT), pygame.RESIZABLE)
    hwnd = pygame.display.get_wm_info()['window']
    return (w, hwnd)
def add_linebreak(font: pygame.font.Font, text: str, disp_width: int) -> str:
    if "\n" in text:
        #Manually handle \n already in the text, since fonts? pygame? assigns horizontal size to \n which
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