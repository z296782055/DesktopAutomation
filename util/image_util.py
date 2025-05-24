import datetime
import os
import threading
import time
from PIL import Image, ImageDraw, ImageFont
import util.utils as utils
import pyautogui
import pyperclip
import re
from util.logger_util import logger

background_image_dir = './img/background/'
temporary_image_dir = './img/temporary/'
click_image_dir = './img/step/'
default_sleep_time = float(utils.get_config('default_sleep_time', 1))

# 生成嵌入文字的图片
def image_inlaid(background_image_url, text, font, size, background_image=None, x=0, y=0):
    if background_image is None:
        image = Image.open(background_image_dir+background_image_url)
    else:
        image = background_image
    # 创建一个新的图像用于绘制修改后的文本（可选，如果需要的话）
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font=font, size = size)  # 选择一个合适的字体和大小
    draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor="la")  # 在图片上绘制文本，颜色为白色，可根据需要调整位置和颜色
    # 保存或显示修改后的图像
    temporary_image_url = temporary_image_dir+utils.generate_random_string()+'.png'
    image.save(temporary_image_url)
    return temporary_image_url

def image_del(image_url):
    try:
        os.remove(image_url)
    except FileNotFoundError:
        pass

# 点击嵌入图片
def image_inlaid_click(text, background_image_url,background_image=None, image_url=None, font="msyh.ttc", size=12, x=0, y=-2, confidence=0.99, grayscale=False, sleep_time=default_sleep_time, before_sleep_time=0, region = None):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    temporary_image_url = ""
    try:
        if image_url is not None:
            temporary_image_url = image_url
        else:
            temporary_image_url = image_inlaid(background_image_url=background_image_url,background_image=background_image, text=text, font=font, size=size, x=x, y=y)
        position = pyautogui.locateOnScreen(image=temporary_image_url,confidence=confidence, grayscale=grayscale, region=region)
        pyautogui.moveTo(position, duration=float(utils.get_config('scan_frequency', 3)))
        pyautogui.click()
    except pyautogui.ImageNotFoundException as e:
        logger.log("找不到图片：" + temporary_image_url)
        time.sleep(sleep_time)
        image_inlaid_click(text=text, background_image_url=background_image_url,background_image=background_image, font=font, size=size, x=x, y=y, confidence=confidence, grayscale=grayscale, sleep_time=sleep_time, region=region)
    finally:
        image_del(temporary_image_url)

def image_click(click_image_url, confidence=0.99, grayscale=False, sleep_time=default_sleep_time, before_sleep_time=0, region=None, right_click=False):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    try:
        position = pyautogui.locateOnScreen(image=click_image_dir + click_image_url, confidence=confidence, grayscale=grayscale, region=region)
        pyautogui.moveTo(position, duration=float(utils.get_config('scan_frequency', 3)))
        if right_click:
            pyautogui.rightClick()
        else:
            pyautogui.click()
    except pyautogui.ImageNotFoundException as e:
        logger.log("找不到图片：" + click_image_url)
        time.sleep(sleep_time)
        image_click(click_image_url=click_image_url, confidence=confidence, grayscale=grayscale, sleep_time=sleep_time, region=region)

def write_text(text_title_image_url, text, x=70, y=0,confidence=0.95, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    image_click(click_image_url=text_title_image_url, confidence=confidence, sleep_time=sleep_time)
    pyautogui.moveRel(x, y)
    pyautogui.click()
    pyautogui.hotkey("ctrl","a")
    if isinstance(text, int):
        dictionary = utils.get_dictionary(str(text))
        if len(dictionary) > 0:
            if dictionary[0] == "time":
                if utils.get_config(dictionary[1]) is not None:
                    pyperclip.copy(datetime.datetime.now().strftime(utils.get_config(dictionary[1])))
                    pyautogui.hotkey('ctrl', 'v')
    else:
        pattern = re.compile(r'[\u4e00-\u9fff]')
        if bool(pattern.search(text)):
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.write(text)

def write_texts(text_title_image_url, texts, xy,confidence=0.95, sleep_time=default_sleep_time, before_sleep_time=0):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    image_click(click_image_url=text_title_image_url, confidence=confidence, sleep_time=sleep_time)
    for i,(x,y) in enumerate(xy):
        utils.pause()
        pyautogui.moveRel(x, y)
        pyautogui.doubleClick()
        pyautogui.hotkey("ctrl","a")
        if isinstance(texts[i], int):
            dictionary = utils.get_dictionary(str(texts[i]))
            if len(dictionary) > 0:
                if dictionary[0] == "time":
                    if utils.get_config(dictionary[1]) is not None:
                        pyperclip.copy(datetime.datetime.now().strftime(utils.get_config(dictionary[1])))
                        pyautogui.hotkey('ctrl', 'v')
        else:
            pattern = re.compile(r'[\u4e00-\u9fff]')
            if bool(pattern.search(texts[i])):
                pyperclip.copy(texts[i])
                pyautogui.hotkey('ctrl', 'v')
            else:
                pyautogui.write(texts[i])

def select_text(text_title_image_url,select_item_background_image_url, text, x=70, y=0, confidence=0.95, sleep_time=default_sleep_time, before_sleep_time=0,font = "msyh.ttc", size = 12, grayscale = False):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    image_click(click_image_url=text_title_image_url, confidence=confidence, sleep_time=sleep_time)
    pyautogui.moveRel(x, y)
    pyautogui.click()
    position = pyautogui.position()
    region = (position.x-35, position.y+10, 60, 136)
    image_inlaid_select_click(text=text,select_item_background_image_url=select_item_background_image_url,confidence=0.95,font = font, size = size, grayscale = grayscale,region=region)

# 点击嵌入下拉框图片
def image_inlaid_select_click(text, select_item_background_image_url, font="msyh.ttc", size=12, x=0, y=-2, confidence=0.99, grayscale=False, sleep_time=default_sleep_time, before_sleep_time=0, region = None):
    count = 10
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    utils.pause()
    temporary_image_url = ""
    try:
        temporary_image_url = image_inlaid(background_image_url=select_item_background_image_url, text=text, font=font, size=size, x=x, y=y)
        position = pyautogui.locateOnScreen(image=temporary_image_url, confidence=confidence, grayscale=grayscale, region=region)
        pyautogui.moveTo(position, duration=float(utils.get_config('scan_frequency', 3)))
        pyautogui.click()
    except pyautogui.ImageNotFoundException as e:
        logger.log("找不到图片：" + select_item_background_image_url)
        count=count*-1
        pyautogui.scroll(count)
        time.sleep(sleep_time)
        image_inlaid_select_click(text=text, select_item_background_image_url=select_item_background_image_url, font=font, size=size, x=x, y=y,
                    confidence=confidence, grayscale=grayscale, sleep_time=sleep_time, region=region)
    finally:
        image_del(temporary_image_url)

def list_text(title_image_url, titles, line_height, data, select_width=0, select_height=0, select_num=0, confidence=0.95, grayscale=False):
    for i,data_item in enumerate(data):
        for title in titles:
            image_click(title_image_url+title+".png", confidence=confidence, grayscale=grayscale, sleep_time=0)
            pyautogui.moveRel(0, line_height*(i+1))
            if "_type" in title:
                pyautogui.click()
                time.sleep(0.5)
                pyautogui.click()
                region=(pyautogui.position().x-(select_width//2),pyautogui.position().y+(select_height//2), select_width+10, (select_height*select_num)+10)
                image_click(click_image_url=title_image_url+title+"/"+data_item[title]+".png", confidence=0.95, grayscale=True, region=region)
            else:
                pyautogui.doubleClick()
                pyautogui.hotkey("Ctrl", "A")
                pyautogui.write(data_item[title])

def radio_text(text_title_image_url,key, value, x=0, y=0, confidence=0.95, sleep_time=default_sleep_time, before_sleep_time=0, grayscale = False):
    if before_sleep_time != 0:
        time.sleep(before_sleep_time)
    image_click(click_image_url=text_title_image_url, confidence=confidence, sleep_time=sleep_time)
    position = pyautogui.position()
    region = (position.x+20, position.y-10, x, y)
    relative_path_to_parent = os.path.relpath(os.path.dirname(text_title_image_url), os.getcwd())
    image_click(click_image_url=relative_path_to_parent+"/"+key+"/"+value+".png", confidence=confidence, grayscale=grayscale, sleep_time=sleep_time, region=region)