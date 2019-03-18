from tkinter import *
from tkinter import messagebox

import urllib.request                   #download file from URL
import requests                         #extract "view-source" from website

from bs4 import BeautifulSoup           #parse HTML code
import re

import threading

import os 

from selenium import webdriver          #a quickfix for getting json data from 9xbuddy.org
from time import sleep

from mutagen.mp3 import EasyMP3         #External lib for adding metadata to audio files--> pip install mutagen

from selenium.webdriver.chrome.options import Options

def loadheadlessly():
    ''' Loads Chrome headlessly with download settings '''
    global browser
    
    #Taken from https://stackoverflow.com/a/47366981/8520798 for chrome download settings

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
#    options.add_argument("download.default_directory=")
    browser = webdriver.Chrome("chromedriver-v73.exe", options=options)
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_path}}
    browser.execute("send_command", params)

threading.Thread(target=loadheadlessly).start()

root = Tk()
root.title("Web Scrapper")
root.geometry("820x480")
root.resizable(0,0)                     #disable resizing of window

v = IntVar()
v.set(1)

v_url = IntVar()
v_url.set(1)

mov_var = IntVar()
mov_var.set(1)

browser = None

selectedchoice = None                                           #get selected option for Music or Video

music_formats = ["mp3","m4a"]
video_formats = ["mp4","mkv"]

headers = {'User-Agent': 'Chrome/39.0.2171.95 Safari/537.36'}   #fake user-agent
download_path = os.path.dirname(os.path.abspath(__file__))

# Music
url_soundCloud = None
dwn_thread = None
mov_thread = None

def on_closing():
    mssge1 = "Do you want to quit?"
    mssge = mssge1
    mssge2 = "Your download is not complete, do you really want to quit?"
    if not dwn_thread is None and dwn_thread.isAlive():
        mssge = mssge2
    if not mov_thread is None and  mov_thread.isAlive():
        mssge = mssge2
    if messagebox.askokcancel("Quit", mssge):
        browser.quit()
        root.destroy()

def set_dwn_path():
    global download_path
    download_path_get = dwn_path_entry.get()
    if not download_path_get:
        download_path = os.path.dirname(os.path.abspath(__file__))
    else:
        if(os.path.isdir(download_path_get)):
            download_path = download_path_get
        else:
            messagebox.showerror("Incorrect Directory","Please check the path")
            download_path = os.path.dirname(os.path.abspath(__file__))
    
def dwnheadlessly(fmovies):
    ''' Get final download links for movies  '''

    browser.get(fmovies)
    sleep(5)                                            # A delay that allows json script to run completely
    html = browser.page_source

    dwn_links = re.findall(r'http:\/\/51.15([^\"<]+)',html)

    if(mov_var.get() == 1):
        downloadit("http://51.15"+dwn_links[0])
    if(mov_var.get() == 2):
        downloadit("http://51.15"+dwn_links[1])
    if(mov_var.get() == 3):
        downloadit("http://51.15"+dwn_links[2])

def sel():
    ''' Select music or movie {choice} '''

    if(v.get() == 1):
        formats = '\n'.join(music_formats)
        label_2.config(text = formats)
        center_label.config(text= "Enter MUSIC name here")
    if(v.get() == 2):
        formats = '\n'.join(video_formats)
        label_2.config(text = formats)
        center_label.config(text= "Enter MOVIE name here")

def downloadit(dwn_url):
    ''' Initiate downloading '''
    try:
        if(selectedchoice == 1):
            nm = file_name_inp.get()+".mp3"
            urllib.request.urlretrieve(dwn_url, download_path+"/"+ nm)
            status_3.configure(text="..download started",foreground="green")
        else:
            browser.get(dwn_url)
            status_3.configure(text="..download started",foreground="green")
    except:
        status_3.configure(text="..download started",foreground="red")
        messagebox.showerror("OOPS","Error initiating download,please try again")

def addmeta():
    ''' Add meta-data to music file after download completes '''

    dwn_thread.join()
    status_4.configure(text="..download complete",foreground="green")

    audio = EasyMP3(download_path+"/"+file_name_inp.get()+".mp3")
    audio["title"] = file_title_inp.get()
    audio["artist"] = file_artist_inp.get()
    audio["album"] = file_album_inp.get()

    audio.save()

    messagebox.showinfo("Success",file_name_inp.get()+".mp3 has been downloaded successfully")

def url_sel():
    ''' Fetching Download links from sources '''

    global dwn_thread,selectedchoice,mov_thread

    nxtLink = ""

    if(selectedchoice == 1):
        try:
            main_link = str(url_soundCloud[v_url.get()-1])
            main_link = "https://m.soundcloud.com/" + main_link

            scrap = get_source(main_link)
            soup = BeautifulSoup(scrap,'html.parser')
            main_link_2 = soup.find("meta",  attrs={'name':"twitter:audio:source"})
            main_link_2 = str(main_link_2["content"])
            
            scrap = get_source(main_link_2)
            main_link_3 = str(re.findall(r'https://cf-media.sndcdn.com(.+?)\"', scrap)[0])
            dwn_url = "https://cf-media.sndcdn.com"+main_link_3

            status_2.configure(text="...download link for music fetched",foreground="green")

            dwn_thread = threading.Thread(target=downloadit,args=(dwn_url,))
            dwn_thread.start()

            metadata_thread = threading.Thread(target=addmeta)
            metadata_thread.start()

        except:
            status_2.configure(text="...problem fetching download links",foreground="red")
            messagebox.showerror("Issue!","Please select any other link!")
    
    elif(selectedchoice == 2):
        try:
            main_link = str(movie_list[v_url.get()-1])
            main_link = "https://fmovies.cab" + main_link

            scrap = get_source(main_link)
            soup = BeautifulSoup(scrap,'html.parser')
            main_link_2 = soup.find_all("link",  href=re.compile('https:\/\/fmovies\.cab\/(.*)-watching.html'))
            
            for l in main_link_2:
                nxtLink = l.get("href")

            fmovies = "https://9xbuddy.org/process?url="+nxtLink

            status_2.configure(text="...download link for movie fetched",foreground="green")

            mov_thread = threading.Thread(target=dwnheadlessly,args=(fmovies,))
            mov_thread.start()

        except:
            status_2.configure(text="...problem fetching download links",foreground="red")
            messagebox.showerror("Issue!","Please select any other link!")
        if not mov_thread.isAlive():
            status_4.configure(text="..download completed")
            browser.close()

def get_source(url):
    ''' Get page source from url '''

    scrap = requests.get(url,headers=headers).text
    return scrap

def launch_dwn_thread():
    ''' Launch a seperate download thread for each download '''
    threading.Thread(target=url_sel).start()

    for label in labels:
        label.configure(text="")

    status_1.configure(text="---Download Process Initiated---")

def displayLinks(links=None,l=0):
    ''' Display available file links to user '''

    global selectedchoice

    i=0
    if(v.get() == 1):
        selectedchoice = 1                            #music choice is selected
    elif(v.get() == 2):
        selectedchoice = 2                            #movie choice is selected

    for widget in center_canvas.winfo_children():     #clear all previous radio buttons
        widget.destroy()
    if not links:
        messagebox.showerror("No Links Found","Please check your input name and try again")
    else:
        if(selectedchoice == 2):
            links = [ link.rsplit('/',1)[0] for link in links ]         #list comprehension to cut last word from movie url 
        for name in links[:l]:
            c = Radiobutton(center_canvas,text=name,value=i+1,variable = v_url)
            c.grid(column=0,row=i,stick="w")
            i+=1

def search():
    ''' Searches user input for music/movie over websites '''

    global url_soundCloud,movie_list

    name = center_entry.get()
    name = name.replace(' ','%20')
    
    url_soundCloud = []                                             #store soundcloud links
    url = "https://www.google.com/search?q="

    url_mov = "https://fmovies.cab/search/"                 

    if(v.get() == 1):
        url = url+name+"%20soundcloud"
    
        scrap = get_source(url)

        url_soundCloud = re.findall(r'https://soundcloud.com/([^.\"&+%]+)', scrap)
        
        #re-modify fetched links if{}
        for i in range(len(url_soundCloud)):
            if url_soundCloud[i].endswith("sets"):
                name = url_soundCloud[i]
                url_soundCloud[i] = name[:-4]
            if url_soundCloud[i].endswith("recommended"):
                name = url_soundCloud[i]
                url_soundCloud[i] = name[:-11]

        url_soundCloud = list(set(url_soundCloud))                  #remove duplicates
        
        l = len(url_soundCloud)
        if(l>10):
            displayLinks(url_soundCloud,10)
        else:
            displayLinks(url_soundCloud,l)

    else:
        url_mov = url_mov+name

        scrap = get_source(url_mov)
        soup = BeautifulSoup(scrap,'html.parser')
        movies = soup.find_all("div", {"class":"card-content"})
        
        movie_list = []
        for movie in movies:
            data_href = movie.get("data-href")
            if not data_href is None:
                movie_list.append(data_href)
        displayLinks(movie_list,len(movie_list))


#------------------------------------------------UI------------------------------------------------------

sidePane = Frame(root,height=480,width=200,bg="#e6e6ff",padx=5,pady=15)
centerPane = Frame(root,height=480,width=420,bg="white")
rightPane = Frame(root,height=480,width=200,bg="white")

sidePane.grid(column=0,rowspan=2,sticky="w")
sidePane.grid_propagate(0)                                          #for stopping frame to resize acc. to its components' size
centerPane.grid(column=1,rowspan=2,row=0,sticky="ns")
centerPane.grid_propagate(0)
rightPane.grid(column=2,rowspan=2,row=0,sticky="e")

label_1 = Label(sidePane,text="Select Your Choice")
music = Radiobutton(sidePane, text="Music", value=1,variable=v,command=sel)
video = Radiobutton(sidePane, text="Movie", value=2,variable=v,command=sel)
label_2 = Label(sidePane,text="mp3\nm4a")
dwn_path = Label(sidePane,text="Enter Download path:")
dwn_path_entry = Entry(sidePane)
dwn_path_button = Button(sidePane,text="Set",command=set_dwn_path)

label_1.grid(row=0,pady=10)
music.grid(row=1,pady=10)
video.grid(row=2,pady=10)
label_2.grid(row=1,column=2,rowspan=2,pady=10)
dwn_path.grid(column=0,row=3,columnspan=3)
dwn_path_entry.grid(column=0,row=4)
dwn_path_button.grid(column=0,row=5)

center_label = Label(centerPane,text="Enter MUSIC name here")
center_entry = Entry(centerPane)
center_button = Button(centerPane,text="Search",command=search)

center_canvas = Canvas(centerPane,width=420)
center_dwn_btn = Button(centerPane,text="Download",command=launch_dwn_thread)

center_canvas.grid_propagate(0)

center_label.grid(column=0,row=0)
center_entry.grid(column=1,row=0)
center_button.grid(column=2,row=0)
center_canvas.grid(column=0,row=1,columnspan=3,sticky="we")
center_dwn_btn.grid(column=1,row=2,sticky="n")

file_name = Label(rightPane,text="Name")
file_name_inp = Entry(rightPane)
mus_details = Label(rightPane,text="Music Details")
file_title = Label(rightPane,text="Title")
file_title_inp = Entry(rightPane)
file_artist = Label(rightPane,text="Artist")
file_artist_inp = Entry(rightPane)
file_album = Label(rightPane,text="Album")
file_album_inp = Entry(rightPane)
mov_quality = Label(rightPane,text="Movie Quality")
mov_360 =  Radiobutton(rightPane, text="360p", value=1,variable=mov_var)
mov_720 =  Radiobutton(rightPane, text="720p", value=2,variable=mov_var)
mov_480 =  Radiobutton(rightPane, text="480p", value=3,variable=mov_var)
status = Frame(rightPane,padx=5)
status_label = Label(status,text="Status")
status_1 = Label(status)
status_2 = Label(status)
status_3 = Label(status)
status_4 = Label(status)

file_name.grid(column=0,row=0,pady=5)
file_name_inp.grid(column=1,row=0,pady=5)
mus_details.grid(column=0,row=1,pady=5)
file_title.grid(column=0,row=2,pady=5)
file_title_inp.grid(column=1,row=2,pady=5)
file_artist.grid(column=0,row=3,pady=5)
file_artist_inp.grid(column=1,row=3,pady=5)
file_album.grid(column=0,row=4,pady=5)
file_album_inp.grid(column=1,row=4,pady=5)

mov_quality.grid(column=0,row=5,pady=5)
mov_360.grid(column=0,row=6,pady=5)
mov_720.grid(column=0,row=7,pady=5)
mov_480.grid(column=0,row=8,pady=5)
status.grid(column=0,row=9,pady=10,columnspan=2,sticky="ns")
status_label.grid(column=0,row=0,sticky="ew")
status_1.grid(column=0,row=1,sticky="w")
status_2.grid(column=0,row=2,sticky="w")
status_3.grid(column=0,row=3,sticky="w")
status_4.grid(column=0,row=4,sticky="w")

labels = []
labels.append(status_1)
labels.append(status_2)
labels.append(status_3)
labels.append(status_4)

root.protocol("WM_DELETE_WINDOW",on_closing)

root.mainloop()