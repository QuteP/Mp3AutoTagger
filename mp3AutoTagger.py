import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
from lxml import etree
import urllib.request
from selenium.webdriver.common.keys import Keys
import requests
from mutagen.id3 import ID3, APIC
import mutagen
from mutagen.easyid3 import EasyID3
import eyed3
import langid
from opencc import OpenCC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def WriteToMp3(result, song_name, author, album_name, year, song_num, img):
    # 先不用圖片
    tag = EasyID3(result)
    tag['artist'] = author
    tag['title'] = song_name
    tag['date'] = year
    tag['album'] = album_name
    tag['tracknumber'] = str(song_num)
    tag.save()
    time.sleep(5)
    # 再用圖片
    tag = ID3(result)
    with open(img, 'rb') as cover:
        tag['APIC'] = APIC(encoding=3, mime='image/jpeg',type=3, desc=u'Cover', data=cover.read())
    tag.save()
    time.sleep(5)


def RemoveRedun(strlt):
    ans = strlt.replace("feat. ", " ").replace(
        "ft. ", " ").replace(" x ", " ").replace("out now", " ").replace("free download", " ").replace("w_"," ")
    ans = list(filter(None, re.split(
        r'[\s\(\)\[\]&,，。‧’\.\?!#@\':\*\-\|X\+\{\}_/、"”·“《》]', ans)))
    return ans


def Translate(strlt):
    for i in range(len(strlt)):
        temp = langid.classify(strlt[i])
        if(temp[0] == 'zh'):
            cc = OpenCC('t2s')
            strlt[i] = cc.convert(strlt[i])
        else:
            try:
                strlt[i] = strlt[i].lower()
            except:
                pass
    return strlt


def FullToHalf(str1):
    # str1是還沒切的
    str2 = [None] * len(str1)
    for i in range(len(str1)):
        if(ord(str1[i]) >= 65281 and ord(str1[i]) >= 65374):
            str2[i] = chr(ord(str1[i]) - 65248)
        else:
            str2[i] = str1[i]
    str2 = "".join(str2)
    return str2


def SearchItunes(google_url, browser, file, result, mode):
    #新增判斷作者有無在曲名內的判斷，若有，suc值較低，反之較高
    browser.get(google_url)
    locator = (By.XPATH,'//input[@title="Google 搜尋"]')
    WebDriverWait(browser, 10, 0.5).until(EC.presence_of_element_located(locator))
    search_bar = browser.find_elements_by_xpath(
        '//input[@title="Google 搜尋"]')[0]
    if(mode == 0):
        search_bar.send_keys(file + "  site:music.apple.com")
    elif(mode == 1):
        search_bar.send_keys(file + "  itunes")
    search_bar.send_keys(Keys.ENTER)
    time.sleep(10)
    # linklt是要存href的連結
    linklt = browser.find_elements_by_xpath(
        '//a[starts-with(@href, "https://music.apple.com") and contains(@href,"album")]')
    for i in range(len(linklt)):
        linklt[i] = linklt[i].get_attribute("href")
    eswitch = 1
    title = file.split(" - ")
    # 0為作者，1為title
    for link in linklt:
        bswitch = 0
        try:
            browser.get(link)
            time.sleep(10)
            # locator = (By.XPATH,'//h2[@class="product-creator typography-title"]/a')
            # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
            # 先判斷作者，再判斷title
            itunes_author = browser.find_element_by_xpath(
                '//div[@class="product-creator typography-large-title"]/a').text
            author = itunes_author  # 不變的
            itunes_author = Translate(RemoveRedun(FullToHalf(itunes_author)))
            # print(itunes_author)
            local_author = Translate(RemoveRedun(FullToHalf(file)))
            # print(local_author)
            try:
                second_author_lt = browser.find_elements_by_xpath('//div[@class="songs-list-row__by-line"]/span/a')
                suc2 = 0.00
                for sai in second_author_lt:
                    suc2 = 0.00
                    sai = Translate(RemoveRedun(FullToHalf(sai.text)))
                    for la1 in local_author:
                        if(la1 in sai):
                            suc2 += 1
                    if(suc2 / len(local_author) >= 0.5):
                        break
            except:
                pass
            long_author = local_author
            short_author = itunes_author
            if(len(short_author) > len(long_author)):
                long_author, short_author = short_author, long_author
            # 判斷契合度
            suc1 = 0.00
            for sa in short_author:
                if(sa in long_author):
                    suc1 += 1
            if(suc1 / len(short_author) >= 0.5 or suc2 / len(local_author) >= 0.5):
                # find_elements_by_xpath，那個s很重要
                # locator = (By.XPATH,'//div[@class="col-song__wrapper"]')
                # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                title_lt = browser.find_elements_by_xpath(
                    '//div[@class="songs-list-row__song-name"]')
                local_title = Translate(RemoveRedun(FullToHalf(title[1])))
                rmx_switch=0.00
                rmx_index=0.00
                if("rmx" in local_title):
                	rmx_switch=1
                	rmx_index=local_title.index("rmx")-1
                elif("remix" in local_title):
                	rmx_switch=1
                	rmx_index=local_title.index("remix")-1
                # print(local_title)
                # print(f'local_title:{local_title}')
                final_suc=0.00
                alt=[]
                for t in title_lt:
                    song_num = title_lt.index(t) + 1
                    t = list(t.text.split('\n'))
                    # print(t)
                    song_name = t[0]
                    itunes_title = Translate(
                        RemoveRedun(FullToHalf(song_name)))
                    if(rmx_switch==1 and (local_title[rmx_index] not in itunes_title)):
                    	continue
                    long_title = local_title
                    short_title = itunes_title
                    if(len(short_title) > len(long_title)):
                        long_title, short_title = short_title, long_title
                    suc3 = 0.00
                    for st in short_title:
                        if(st in long_title):
                            suc3 += 1
                    # print(suc3/len(short_title))
                    if(suc3/len(short_title)>final_suc):
                        final_suc=suc3/len(short_title)
                        alt=t
                    if(final_suc==1):
                        break
                if(final_suc >= 0.8):
                    if(len(t) == 3):
                        author = alt[1]
                    year = browser.find_element_by_xpath('//div[@class="product-meta typography-callout-emphasized"]').text.split(" · ")[1]
                    year = re.match(r'(^\d+)', year).group()
                    # print(year)
                    # song_num在上面
                    # 抓img
                    # locator = (By.XPATH,'//img[@class="media-artwork-v2__image"]')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    imglt = browser.find_elements_by_xpath('//div[@class="product-lockup__artwork"]/div/picture/source')[1].get_attribute("srcset")
                    # print(imglt)
                    img = re.findall(r'https://.*?-60\.jpg', imglt)[-1]
                    # print(img)
                    img = requests.get(img)
                    time.sleep(10)
                    with open(file + '.jpg', 'wb') as fp:
                        fp.write(img.content)
                    img = file + '.jpg'
                    # locator = (By.XPATH,'//h1[@class="product-name typography-title-emphasized clamp-4"]')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    album_name = browser.find_element_by_xpath('//h1[@class="product-name typography-large-title-semibold clamp-4"]').text.replace(" - Single", "").replace(" - EP", "")
                    WriteToMp3(result, song_name, author,album_name, year, song_num, img)
                    os.remove(img)
                    if(mode == 0):
                        print("Itunes模式0搜尋成功")
                    elif(mode == 1):
                        print("Itunes模式1搜尋成功")
                    return True
        except Exception as e:
            print(e)
            pass
    if(mode == 0):
        print("Itunes模式0搜尋失敗")
    elif(mode == 1):
        print("Itunes模式1搜尋失敗")
    return False

def SearchSpotify(google_url, browser, file, result, mode):
    browser.get(google_url)
    locator = (By.XPATH,'//input[@title="Google 搜尋"]')
    WebDriverWait(browser, 10, 0.5).until(EC.presence_of_element_located(locator))
    search_bar = browser.find_elements_by_xpath(
        '//input[@title="Google 搜尋"]')[0]
    if(mode == 0):
        search_bar.send_keys(file + "  site:open.spotify.com/album")
    # elif(mode == 1):
    #     search_bar.send_keys(file + "  spotify")
    search_bar.send_keys(Keys.ENTER)
    time.sleep(10)
    # linklt是要存href的連結
    linklt = browser.find_elements_by_xpath(
        '//a[starts-with(@href, "https://open.spotify.com/album/")]')
    for i in range(len(linklt)):
        linklt[i] = linklt[i].get_attribute("href")
    title = file.split(" - ")
    # print(title)
    # 0為作者，1為title
    for link in linklt:
        bswitch = 0
        try:
            browser.get(link)
            time.sleep(10)
            # locator = (By.XPATH, '//div[@data-testid="tracklist-row"]/div[@aria-colindex="2"]/div/span[contains(@class,"standalone-ellipsis-one-line")]')
            # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
            # 先判斷作者，再判斷title
            spotify_authorlt = browser.find_elements_by_xpath(
                '//div[@aria-colindex="2"]/div/span[contains(@class,"standalone-ellipsis-one-line")]/a')
            # locator = (By.XPATH,'//div[@data-testid="tracklist-row"]/div[@aria-colindex="2"]/div/div')
            # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
            title_lt = browser.find_elements_by_xpath(
                '//div[@aria-colindex="2"]/div/div')
            local_author = Translate(RemoveRedun(FullToHalf(title[0])))
            local_title = Translate(RemoveRedun(FullToHalf(title[1])))
            rmx_switch=0.00
            rmx_index=0.00
            if("rmx" in local_title):
                rmx_switch=1
                rmx_index=local_title.index("rmx")-1
            elif("remix" in local_title):
                rmx_switch=1
                rmx_index=local_title.index("remix")-1
            final_suc=0.00
            for s in range(len(spotify_authorlt)):
                author = spotify_authorlt[s].text
                spotify_author = Translate(RemoveRedun(
                    FullToHalf(spotify_authorlt[s].text)))
                long_author = Translate(RemoveRedun(
                    FullToHalf(file)))
                # print(long_author)
                short_author = spotify_author
                if(len(short_author) > len(long_author)):
                    long_author, short_author = short_author, long_author
                # print(short_author)
                suc = 0.00
                for sha in short_author:
                    if(sha in long_author):
                        suc += 1
                # 判斷契合度
                if(suc / len(short_author) >= 0.8):
                    song_num = s + 1
                    song_name = title_lt[s].text
                    spotify_title = Translate(
                        RemoveRedun(FullToHalf(song_name)))
                    if(rmx_switch==1 and (local_title[rmx_index] not in spotify_title)):
                    	continue
                    long_title = Translate(RemoveRedun(
                    FullToHalf(file)))
                    # print(long_title)
                    short_title = spotify_title
                    if(len(short_title) > len(long_title)):
                        long_title, short_title = short_title, long_atitle
                    # print(short_title)
                    suc1 = 0.00
                    for st in short_title:
                        if(st in long_title):
                            suc1 += 1
                    if(suc1 / len(short_title)>=0.8):
                        year = browser.find_elements_by_xpath(
                            '//section[@data-testid="album-page"]/div[contains(@class,"contentSpacing")]/div/div/span')[0].text
                        year = year[0:5]
                        # song_num在上面
                        # 抓img
                        # locator = (By.XPATH,'//div[@class="main-view-container__scroll-node-child"]//div/img')
                        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                        imglt = browser.find_element_by_xpath(
                            '//section[@data-testid="album-page"]/div[contains(@class,"contentSpacing")]/div/div/img').get_attribute("srcset")
                        img = re.findall(
                            r'https://i\.scdn\.co/image/.*?0w', imglt)[-1]
                        img = img[0:-5]
                        img = requests.get(img)
                        time.sleep(10)
                        with open(file + '.jpg', 'wb') as fp:
                            fp.write(img.content)
                        img = file + '.jpg'
                        # locator = (By.XPATH,'//div[@class="main-view-container__scroll-node-child"]/section/div/div/span')
                        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                        album_name = browser.find_element_by_xpath(
                            '//div[@class="main-view-container__scroll-node-child"]/section/div/div/span').text
                        WriteToMp3(result, song_name, author,album_name, year, song_num, img)
                        os.remove(img)
                        if(mode == 0):
                            print("Spotify模式0搜尋成功")
                            return True
                        elif(mode == 1):
                            print("Spotify模式1搜尋成功")
                            return True
        except Exception as e:
            print(e)
            pass
    if(mode == 0):
        print("Spotify模式0搜尋失敗")
    elif(mode == 1):
        print("Spotify模式1搜尋失敗")
    return False
def SearchSoundCloud(browser, file, result):
    soundcloud_url = "https://soundcloud.com/"
    browser.get(soundcloud_url)
    time.sleep(10)
    search_bar = browser.find_elements_by_xpath(
        '//form[@class="headerSearch"]/input[@type="search"]')[1]
    search_bar.send_keys(file)
    search_bar.send_keys(Keys.ENTER)
    time.sleep(10)
    # locator = (By.XPATH, '//div[@class="search"]')
    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
    try:
        # locator = (By.XPATH,'//div/a/span[@class="soundTitle__usernameText"]')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        soundcloud_author_lt = browser.find_elements_by_xpath(
            '//span[@class="soundTitle__usernameText"]')
        # locator = (By.XPATH,'//div/a[@class="soundTitle__title sc-link-dark"]')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        soundcloud_title_lt = browser.find_elements_by_xpath(
            '//div[@class="soundTitle__usernameTitleContainer"]/a')
    except Exception as e:
        print(e)
        print("SoundCloud搜尋失敗")
        return False
    # local_title=Translate(RemoveRedun(FullToHalf(file)))
    local_title = file.split(" - ")
    local_author = Translate(RemoveRedun(FullToHalf(local_title[0])))
    # print(local_title)
    link = "temp"
    final_suc = 0.00
    for i in range(len(soundcloud_author_lt)):
        try:
            soundcloud_author = Translate(RemoveRedun(
                FullToHalf(soundcloud_author_lt[i].text)))
            # print(soundcloud_author)
            suc1 = 0.00
            suc2 = 0.00
            suc3 = 0.00
            # 兩邊格式相同，前面作者後面標題，不用特別抓作者
            if(len(soundcloud_title_lt[i].text.split(' - ')) >= 2):
                temp_title = Translate(RemoveRedun(FullToHalf(file)))
                for a in soundcloud_author:
                    if(a in temp_title):
                        suc1 += 2
                soundcloud_author2=Translate(RemoveRedun(FullToHalf(soundcloud_title_lt[i].text.split(' - ')[0])))
                for a2 in soundcloud_author2:
                    if(a2 in local_author):
                        suc2+=1
                long_title = Translate(RemoveRedun(FullToHalf(local_title[1])))
                short_title = Translate(RemoveRedun(FullToHalf(soundcloud_title_lt[i].text.split(' - ')[1])))
                if(len(short_title) > len(long_title)):
                    long_title, short_title = short_title, long_title
                for t in short_title:
                    if(t in long_title):
                        suc3+=1
                if((suc1/len(soundcloud_author)+suc2/len(soundcloud_author2)+suc3/len(short_title))/3>final_suc):
                    final_suc=(suc1/len(soundcloud_author)+suc2/len(soundcloud_author2)+suc3/len(short_title))/3
                    link=soundcloud_title_lt[i].get_attribute('href')
            # local的前面是作者。他的前面沒作者，後面和st一樣
            elif(len(soundcloud_title_lt[i].text.split(' - '))==1):
                for a in soundcloud_author:
                    if(a in local_author):
                        suc1+=2
                long_title = Translate(RemoveRedun(FullToHalf(local_title[1])))
                short_title = Translate(RemoveRedun(
                FullToHalf(soundcloud_title_lt[i].text)))
                if(len(short_title) > len(long_title)):
                    long_title, short_title = short_title, long_title
                for t in short_title:
                    if(t in long_title):
                        suc2+=1
                if((suc1/len(soundcloud_author)+suc2/len(short_title))/2>final_suc):
                    final_suc=(suc1/len(soundcloud_author)+suc2/len(short_title))/2
                    link=soundcloud_title_lt[i].get_attribute('href')
            if(final_suc==1):
                break
        except Exception as e:
            print(e)
    try:
        browser.get(link)
        time.sleep(10)
        # locator = (By.XPATH, '//div[@class="soundTitle__usernameTitleContainer"]/span')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        soundcloud_title=browser.find_element_by_xpath('//div[@class="soundTitle__titleHeroContainer"]//span').text
        # print(soundcloud_title)
        # locator = (By.XPATH,'//div/time')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        year=browser.find_element_by_xpath('//div/time').get_attribute('title')
        # print(year)
        year=year[-4:]
        # locator = (By.XPATH,'//div//div[@class="listenArtworkWrapper"]//span')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        img = browser.find_element_by_xpath('//div//div[@class="listenArtworkWrapper"]//span').get_attribute("style")
        # print(img)
        img = re.findall(r'https://.*?500x500\..*?g', img)[0]
        img = requests.get(img)
        time.sleep(10)
        with open(file + '.jpg', 'wb') as fp:
            fp.write(img.content)
        img = file + '.jpg'
        soundcloud_title=soundcloud_title.split(' - ')
        if(len(soundcloud_title)>=2):
            # 兩邊格式相同，前面作者後面標題，不用特別抓作者
            song_name=soundcloud_title[1]
            author=soundcloud_title[0]
            WriteToMp3(result, song_name, author,song_name, year, 1, img)
        elif(len(soundcloud_title)==1):
            # local的前面是作者。後面和st一樣
            song_name=soundcloud_title[0]
            author=local_title[0]
            WriteToMp3(result, song_name, author,song_name, year, 1, img)
        os.remove(img)
        print("SoundCloud搜尋成功")
        return True
    except Exception as e:
        print(e)
        print("SoundCloud搜尋失敗")
        return False
def SearchMusic163(browser, file, result):
    music163_url='https://music.163.com/'
    browser.get(music163_url)
    time.sleep(10)
    # locator = (By.XPATH,'//span/input')
    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
    search_bar = browser.find_element_by_xpath('//span/input')
    search_bar.send_keys(file)
    search_bar.send_keys(Keys.ENTER)
    time.sleep(5)
    # locator = (By.XPATH, '//iframe[@name="contentFrame"]')
    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
    try:
        browser.switch_to.frame("contentFrame")
        # locator = (By.XPATH, '//div[@class="td w1"]/div[@class="text"]')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        music163_author_lt = browser.find_elements_by_xpath('//div[@class="td w1"]/div[@class="text"]')
        # locator = (By.XPATH, '//div[@class="td w0"]/div[@class="sn"]/div[@class="text"]')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        music163_title_lt = browser.find_elements_by_xpath('//div[@class="td w0"]/div[@class="sn"]/div[@class="text"]')
        # locator = (By.XPATH, '//div[@class="td w2"]/div[@class="text"]/a')
        # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
        music163_album_lt = browser.find_elements_by_xpath('//div[@class="td w2"]/div[@class="text"]/a')
    except Exception as e:
        print(e)
        print("網易雲音樂搜尋失敗")
        return False
    # local_title=Translate(RemoveRedun(FullToHalf(file)))
    local_title = file.split(" - ")
    local_author = Translate(RemoveRedun(FullToHalf(local_title[0])))
    # print(local_title)
    link = "temp"
    final_suc = 0.00
    for i in range(len(music163_album_lt)):
        suc=0.00
        try:
            album_name=music163_album_lt[i].text
            author=music163_author_lt[i].text
            music163_author=Translate(RemoveRedun(FullToHalf(music163_author_lt[i].text)))
            long_author = local_author
            # print(long_author)
            short_author = music163_author
            # print(short_author)
            if(len(short_author) > len(long_author)):
                long_author, short_author = short_author, long_author
            for sa in short_author:
                if sa in long_author:
                    suc+=1
            if(suc/len(short_author)==1.0):
                suc1=0.00
                suc2=0.00
                song_name = music163_title_lt[i].text
                music163_title = Translate(RemoveRedun(FullToHalf(song_name)))
                long_title = Translate(RemoveRedun(FullToHalf(local_title[1])))
                # print(long_title)
                short_title = music163_title
                # print(short_title)
                if(len(short_title) > len(long_title)):
                    long_title, short_title = short_title, long_title
                for st in short_title:
                    if(st in long_title):
                        suc1 += 1
                if(suc1 / len(short_title)== 1.0):
                    browser.get(music163_album_lt[i].get_attribute("href"))
                    time.sleep(10)
                    # locator = (By.XPATH, '//iframe[@name="contentFrame"]')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    browser.switch_to.frame("contentFrame")
                    # locator = (By.XPATH, '//p[@class="intr"]')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    year = browser.find_elements_by_xpath('//p[@class="intr"]')[1].text
                    year=year.replace("发行时间：","")
                    year=re.match(r'(^\d+)', year).group()
                    # print(year);
                    # locator = (By.XPATH, '//div[@class="cover u-cover u-cover-alb"]/img')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    img = browser.find_element_by_xpath('//meta[@property="og:image"]').get_attribute("content")
                    img = requests.get(img)
                    time.sleep(10)
                    with open(file + '.jpg', 'wb') as fp:
                        fp.write(img.content)
                    img = file + '.jpg'
                    song_num=1
                    # locator = (By.XPATH, '//div[@class="ttc"]/span/a/b')
                    # WebDriverWait(browser, 20, 5).until(EC.presence_of_element_located(locator))
                    num_lt=browser.find_elements_by_xpath('//div[@class="ttc"]/span/a/b')
                    final_suc=0.00
                    for i in num_lt:
                        long_title = local_title
                        short_title = i.get_attribute("title")
                        if(len(short_title) > len(long_title)):
                            long_title, short_title = short_title, long_title
                        suc3=0.00
                        for st2 in short_title:
                            if st2 in long_title:
                                suc3+=1
                        if(suc3/len(short_title)>final_suc):
                            final_suc=suc3/len(short_title)
                            song_num=short_title.index(st2) + 1
                        if final_suc==1:
                            break
                    WriteToMp3(result, song_name, author, album_name, year, song_num, img)
                    os.remove(img)
                    print("網易雲音樂搜尋成功")
                    return True
        except Exception as e:
            print(e)
    print("網易雲音樂搜尋失敗")
    return False
path = input("請輸入音樂檔案所在的資料夾絕對路徑：")
result = []
filName = []
# 在這先看有無中文歌
for dirPath, dirNames, fileNames in os.walk(path):
    for f in fileNames:
        result.append(os.path.join(dirPath, f))
        tempName = re.sub(r'.mp3', '', f)
        filName.append(tempName)
# 基本google搜尋url
google_url = 'https://www.google.com'
# 創建chrome對象
options = Options()
options.add_argument('--window-size=1920x1080')
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
driver_path = input("請輸入chromedriver的絕對路徑：")
browser = webdriver.Chrome(executable_path=driver_path, options=options)
# browser.implicitly_wait(5)
browser.get(google_url)
# temp = input("請先確定recapcha已經被解鎖，解鎖後請隨機輸入一值：")
for i in range(len(filName)):
    temptag=False
    file = eyed3.load(result[i])
    file.initTag()
    file.tag.save()
    print(filName[i])
    snd_switch=0;
    if(filName[i].find("bootleg")!=-1 or filName[i].find("Bootleg")!=-1):
        temptag=SearchSoundCloud(browser, filName[i], result[i])
        snd_switch=1;
    else:
        temptag = SearchItunes(google_url, browser, filName[i], result[i], 1)
        if(temptag == False):
            temptag = SearchItunes(google_url, browser, filName[i], result[i], 0)
        # if(temptag == False):
        #     temptag = SearchSpotify(google_url, browser, filName[i], result[i], 1)
        if(temptag == False):
            temptag = SearchSpotify(google_url, browser, filName[i], result[i], 0)
        if(temptag==False and (langid.classify(filName[i])[0]=='zh' or langid.classify(filName[i])[1]=='zh')):
            try:
                temptag=SearchMusic163(browser, filName[i], result[i])
            except:
                pass
        if(temptag==False and snd_switch==0):
            temptag=SearchSoundCloud(browser, filName[i], result[i])
    time.sleep(10)
browser.quit()
