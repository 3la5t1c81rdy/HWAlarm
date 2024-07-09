

"""
print(t.localtime())
samplet = t.strptime("2023 12 15 12 0 0", "%Y %m %d %H %M %S")
print(t.strftime("%m/%d/%Y %H(/24):%M:%S",samplet))
print(t.mktime(samplet))
print(t.time())
print(t.localtime(t.time() + 3600))
"""
from HWAHelper import *
if __name__ == '__main__':
    HWAlarm = Alarm_window(setup())
    HWAlert = Alert(HWAlarm)
    tstamp = 0
    c = pygame.time.Clock()
    while True:
        HWAlarm.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    HWAlarm.add_task()
                elif event.button == 3:
                    HWAlarm.remove_task()
                elif event.button == 4:
                    #up
                    HWAlarm.scroll_line(True)
                elif event.button == 5:
                    #down
                    HWAlarm.scroll_line(False)
                
        if t.time() - tstamp > 5:
            tstamp = t.time()
            HWAlert.update_alert()
        HWAlarm.update_alarm()
        if HWAlarm.get_num_tasks() == 0:
            HWAlarm.splash_nullscreen()
        
        pygame.display.flip()
        c.tick(20)