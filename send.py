from datetime import datetime, date,timedelta
from numpy.core.fromnumeric import shape
from scipy.io import savemat, loadmat
import numpy as np
import os
import sys
import time
import math

def send():
    print('Sender started.')
    clock_of_run = datetime.now()
    message_of_run = 'Sender started in : {} / {} / {} **** {} : {} : {}'.format(
        clock_of_run.year,clock_of_run.month,clock_of_run.day,clock_of_run.hour,clock_of_run.minute,clock_of_run.second)
    with open('logs_of_modules.txt','r+') as file:
        content = file.read()
        num_of_lines = len(content.split('\n'))-1
        #clear content of log file when it is include more than 2000 line of logs
        if num_of_lines > 2000:
            # clear logs file content
            with open('logs_of_modules.txt','w') as f:
                pass
        # write new log
        else:
            with open('logs_of_modules.txt','a') as f:
                f.write(message_of_run+'\n')
    
    init_psych_status_flag = {'init_psych_status_flag': np.array([0,0])}
    savemat('init_psych_status_flag.mat', init_psych_status_flag)
    
    # Handling error matrix
    error_occured_matrix = np.zeros((3,10))
    
    # convert failed
    # --------------------
    # if ~isdeployed()
    #     addpath('ptb');
    #     addpath('ntp');
    #     addpath('send');
    #     addpath('webui');
    #     addpath('common'); % common doa functions
    #     addpath('doa');
    #     addpath('detection');
    # end
    # ---------------------
    
    # Creatind error table and saveing in common folder
    
    errors_table = {'errors_table':np.zeros((50,15))}
    savemat(os.path.join(os.getcwd(),'common','errors_table.mat'),errors_table)
    
    # Initilize java objects
    
    # ***** Load java object and call database access for retreiving point ***** ##
    global gps_dao_java_obj_G
    sys.path.append('jars\gps.jar')
    import gunlocator.gps.dao.*
    
    gps_dao_java_obj_G = LocationTrackDao.getInstance()
    # Load Sender
    sys.path.append('jars\messaging.jar')
    import gunlocator.messaging.send.api.*;
    
    # Shock sender
    global Shock_sender_java_obj_G
    Shock_sender_java_obj_G = ShockEventSender
    
    # Device staus sender
    global Status_sender_java_obj_G
    Status_sender_java_obj_G = DeviceStatusSender
    
    global System_failer_sender_java_obj_G
    System_failer_sender_java_obj_G = SystemFailureSender
    
    # Shock sender
    global Shock_sender_java_obj_G
    Shock_sender_java_obj_G = ShockEventSender
    
    while(1):
        try:
            # Config the error parameters...
            severity = 2 #0: Normal 1: Warning 2: Critical
            # convert failed (who is my ancestor)
            exe_part_number = who_is_my_ancestor() #1: Sender  2: Detector  3: noGUI
            subpart = 11 # 0: for base part_counter: for function index
            error_code = 10 # System Functionality Error
            varargin = [severity, exe_part_number, subpart, error_code]
            # end of error config process
            sending() # Main process ...
            if error_occured_matrix[exe_part_number][0]==1:
                new_varargin = [0, varargin(1), varargin(2), varargin(3)]
                # convert failed (send_status)
                send_status(new_varargin)
                error_occured_matrix[exe_part_number][0] = 0
        except Exception as e:
            # Error Message : System has a critical error in its functionality.
            # convert failed (log_error)
            error_occured_matrix[exe_part_number][0] = log_error(exception ,varargin,0)
            if error_occured_matrix[exe_part_number][0]==1:
                send_status(varargin)

# Sending ...
def sending():
    # sound_source /online=1 sratup =2  offline=3 test=4
    online_mode = 1
    offline_mode = 3
    startup_mode = 2
    testing_mode = 4
    ONLINE = get_setting('online') # whether get data from audiocard (1), or file (0)
    
    # DoA parameters
    
    time_conf.ANALYS_INTERVAL = 1 # for analysis every 1 seconds
    time_conf.save_invl = 10 # save in 10 seconds blocks
    time_conf.maxsecs = get_setting('maxsec')
    freq = get_setting('freq')
    main_save_path = get_setting('save_path')
    
    check_validity(time_conf)
    
    # ----------------- #
    #      Initialize   #
    # ----------------- #
    data = np.array([])
    save_buffer = np.array([])
    folder_start_times = np.array([])
    
    last_written = 0 # Last written to mm file.
    last_saved = 0 # Last interval that has been saved
    last_read = -9 # Just for logging purpose
    newly_read = time_conf.maxsecs # number of intervals recorded since the current folder created
    prev_block_no = 0
    init_send(time_conf, freq, main_save_path)
    
    #------------------------------------#
    #      Initialize Psych tool         #
    #------------------------------------#
    in_start_pro = 1
    
    #convert failed (init_psych,time_conf)
    phandle, _ = init_psych(freq, in_start_pro, time_conf.ANALYS_INTERVAL, ONLINE) 
    
    #-----------------------------------#
    #             Record Loop           #
    #-----------------------------------#
    first_time_flag = 1
    second_source = startup_mode
    main_ONLINE_mode =ONLINE
    global to_read
    time_t1 = datetime.now()
    
    try:
        os.remove(r'C:\AGL\DeviceConfigByUI\test_runner.json')
    except Exception as e:
        pass
    try:
        os.remove(r'C:\AGL\DeviceConfigByUI\inprogress.mat');
    except Exception as e:
        pass
    
    zerodata_for_filter = np.zeros(8,96000)
    while (1):
        # convert failed
        mmf_heartbeat()
        if os.path.isfile(r'C:\AGL\DeviceConfigByUI\test_runner.json'):
            if not os.path.isfile(r'C:\AGL\DeviceConfigByUI\inprogress.mat'):
                ONLINE = 2
                inprogress = 0
                savemat(r'C:\AGL\DeviceConfigByUI\inprogress.mat','inprogress')
                to_read = 1
                last_read = last_read - 8; # Just for logging purpose
        if ONLINE == 2 & to_read > 5:
            try:
                os.remove(r'C:\AGL\DeviceConfigByUI\test_runner.json')
            except Exception as e:
                pass
            try:
                delete(r'C:\AGL\DeviceConfigByUI\inprogress.mat')
            except Exception as e:
                pass
            ONLINE = main_ONLINE_mode
        #---------------------------------------#
        #        Fetch data from audio-card     #
        #---------------------------------------#
        online_mode_waiting_time  = 20
        offline_mode_waiting_time = 1
        startup_mode_waiting_time = 1
        testing_mode_waiting_time = 1
        if ONLINE != 0 and sound_source == online_mode and first_time_flag == 1:
            for wait_counter in range(1,online_mode_waiting_time,1):
                time.sleep(1)
                first_time_flag = 0
                # convert failed (nbuffered)
                new_data, interval_end_time, sound_source = getAudio_(time_conf.ANALYS_INTERVAL, phandle, freq, nbuffered, ONLINE)
                new_data = []
                data = []
            # convert failed (mmf_initialize)
            fh = mmf_initialize('send', freq)

            newly_read = time_conf.maxsecs
            folder_start_times = np.array([])
            last_saved = 0

            last_written = 0
        elif ONLINE != 0 and sound_source == startup_mode:
            time.sleep(startup_mode_waiting_time)
            stillHas = 0
            _, _, _ =  get_audio(time_conf.ANALYS_INTERVAL, phandle, np.array([]), freq, sound_source,stillHas)
        elif ONLINE == 0 and sound_source == offline_mode:
            time.sleep(offline_mode_waiting_time)
        elif ONLINE != 0 and sound_source == testing_mode:
            time.sleep(testing_mode_waiting_time)
            stillHas = 0
            _, _, _ =  get_audio(time_conf.ANALYS_INTERVAL, phandle, np.array([]), freq, sound_source,stillHas)
            first_time_flag = 1
        
        time_t2 = datetime.now()
        time_delta = time_t2 - time_t1
        if(time_delta >= timedelta(seconds=45)):
            send_is_alive = 1
            # convert failed (heartbeat_to_ui)
            heartbeat_to_ui(send_is_alive)
            time_t1 = datetime.now()
            time_t1 = time_t1.minute*60+time_t1.second

        nbuffered = np.shape(data)[0]
        print('*********** Buffer Queue = '+str(nbuffered),'***********')
        new_data, interval_end_time, sound_source = getAudio_(time_conf.ANALYS_INTERVAL, phandle, freq, nbuffered, ONLINE)

        if not np.shape(new_data)[0]==0:

            data = np.append(data, new_data,axis=0)
            last_read = update_last_read(last_read, np.shape(new_data)[0])
            #------------------------------------------#
            # Make a new folder if new data > 120 sec. #
            #------------------------------------------#
            newly_read = newly_read + np.shape(new_data)[0]
            if newly_read >= time_conf.maxsecs:
                # convert failed (make_folder)
                folder_start_times, newly_read = make_folder(newly_read, interval_end_time, folder_start_times,time_conf)
        
        #---------------------------------------#
        #       Write data to shared file       #
        #---------------------------------------#
        if np.shape(data)[0] >= 1:
            # convert failed (filter_data)
            filtered = filter_data(data, freq)
            folder_time = folder_start_times[math.floor(last_written/time_conf.maxsecs),:]
            # convert failed (mmf_write_block)
            block_in_buff = mmf_write_block(fh,data[0,:,:],filtered,last_written+1,prev_block_no,folder_time,sound_source)
            
            if sound_source != online_mode:
                amp_scale = load_scale_factors()
                try:
                    for ch in range(8):
                        new_data_1[ch,:] = data[0,ch,:]*amp_scale[ch]
                    shock-quick_alarm_DF(new_data_1,freq,sound_source)
                except Exception as e:
                    pass
            
            if block_in_buff > 0:
                last_written = last_written+1
                print('interval no = '+ str(last_written))
                data = data[1, :, :]
                prev_block_no = block_in_buff
        
        #---------------------------------------#
        #             Save 10 seconds           #
        #---------------------------------------#
        
        save_buffer = update_save_buffer(new_data, save_buffer)
        save_buffer, last_saved = save_buffer_data(save_buffer, freq, time_conf, last_saved, folder_start_times)
        
        #---------------------------------------#
        #              Drop extra data          #
        #---------------------------------------#
        if sound_source == online_mode:
            main_buffersize = 4
            toDel = 3
        else:
            main_buffersize = 50
            toDel = 30
        # Config the error parameters...
        drop_severity = 0 # 0: Normal 1: Warning 2: Critical
        drop_exe_part_number = who_is_my_ancestor() # 1: Sender  2: Detector  3: noGUI
        drop_subpart = 11  # 0: for base part_counter: for function index
        drop_error_code = 30 # Drop Occured
        drop_varargin = np.array([drop_severity, drop_exe_part_number, drop_subpart, drop_error_code])
        # end of error config process
        if np.shape(data)[0] > main_buffersize:
            data, last_written = drop_old_data(data, last_written, toDel)
            exception = Exception('It has just dropped some data from buffer.')
            # convert failed (log_error)
            error_occured = log_error(exception, drop_varargin, 0)
            if error_occured:
                # convert failed (send_sts)
                send_status(drop_varargin)
            
            if sound_source == online_mode:
                new_data = np.array([])
                data = np.array([])
                fh = mmf_initialize('send',freq)
                newly_read = time_conf.maxsecs
                folder_start_times = np.array([])
                last_saved = 0
                last_written = 0
        else:
            drop_varargin[0] = 0
            send_status(drop_varargin)
    # Stop capture:
    stop_Psych(phandle)
    mmf_close(fh)

##
# If buffer size is larger than 50,
# keep only the latest 20 seconds, drop old ones.
# Important: keeping more than 20 intervals increases insertion/deletion overhead
# which takes more than 1 second for each itnerval! which is dangerous.

def drop_old_data(data, last_written, toDel):
    nbuff = np.shape(data)[0]
    data = data[toDel+1:, :, :]
    last_written = last_written+toDel
    log_fullbuffer(nbuff, toDel)
    
    return data,last_written
##
# This is used for testing synchronization of two systems.
#  Simply detects if the signal contains a high amplitude sound.
def simple_detect(data_block, new_interval_time, freq, offst):
    
    try:
        dat = data_block[0, :, :]
        row, col = np.argwhere(np.abs(dat)>(0.005/3.5))[0]
        if !np.shape()
    
    
                   


        




if __name__ == "__main__":
    send()
