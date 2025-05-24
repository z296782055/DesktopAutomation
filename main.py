import pyautogui
import util.image_util as image_util
import util.utils as utils
from util import control_util

pyautogui.FAILSAFE = True  # 鼠标移至左上角时自动终止程序
def goto(self, step):
    utils.set_config("step", step)
    self.step_text.Label = utils.get_step(utils.get_config("software"), step, default="")
    getattr(__import__(__name__), "step" + str(step))(self)

def start(self):
    step_list = utils.get_step_all(utils.get_config("software"))
    del step_list[:int(utils.get_config("step"))-1]
    for step in step_list:
        utils.window_dict.clear()
        for key, value in step.items():
            for automation in list(value):
                control_util.do_automation(key, automation)

def step1(self):
    # 点击“实时采集”，进入选择项目及色谱系统界面 step1
    image_util.image_click(click_image_url='step1.png', confidence=0.99, grayscale=True)
    goto(self,2)

def step2(self):
    # 选择项目及色谱系统，打开主界面 step2
    item = utils.get_data("item")
    chromatographic = utils.get_data("chromatographic")
    image_util.image_inlaid_click(item, "out.png", confidence=0.95, grayscale=True)
    image_util.image_inlaid_click(chromatographic, "out.png", confidence=0.95, grayscale=True)
    image_util.image_click(click_image_url='step2.png', confidence=0.97)
    goto(self, 3)

def step3(self):
    # 添加仪器方法 step3
    image_util.image_click(click_image_url='step3/step1.png', confidence=0.97, before_sleep_time=0)
    image_util.image_click(click_image_url='step3/step2.png', confidence=0.97)
    goto(self,4)

def step4(self):
    # 方法概要 step4
    image_util.image_click(click_image_url='step4/step1.png', confidence=0.99)
    image_util.write_text(text_title_image_url='step4/step2.png',text=utils.get_data("instrument_method", {}).get("method_summary", {}).get("runtime", ""), confidence=0.95)
    goto(self,5)

def step5(self):
    #泵 step5
    image_util.image_click(click_image_url='step5/step1.png', confidence=0.99)
    image_util.write_text(text_title_image_url='step5/step2.png',text=utils.get_data("instrument_method", {}).get("pump").get("flow_velocity", ""), confidence=0.95)
    image_util.write_text(text_title_image_url='step5/step3.png',text=utils.get_data("instrument_method", {}).get("pump").get("max_pressure", ""), confidence=0.95)
    image_util.write_text(text_title_image_url='step5/step4.png',text=utils.get_data("instrument_method", {}).get("pump").get("min_pressure", ""), confidence=0.95)

    xy = [(70,0),(70,0),(70,0)]
    pump = utils.get_data("instrument_method", {}).get("pump")
    texts = [pump.get("valve_a_ratio", ""),pump.get("valve_b_ratio", ""),pump.get("valve_c_ratio", "")]
    image_util.write_texts(text_title_image_url='step5/step5.png',texts=texts,xy=xy, confidence=0.93)

    text= utils.get_data("instrument_method", {}).get("pump").get("valve_a_name", "")
    image_util.select_text(text_title_image_url='step5/step7.png',select_item_background_image_url="select_item.png",text=text, x=70, confidence=0.93, grayscale=True)
    text= utils.get_data("instrument_method", {}).get("pump").get("valve_b_name", "")
    image_util.select_text(text_title_image_url='step5/step8.png',select_item_background_image_url="select_item.png",text=text, x=70, confidence=0.93, grayscale=True)
    text= utils.get_data("instrument_method", {}).get("pump").get("valve_c_name", "")
    image_util.select_text(text_title_image_url='step5/step9.png',select_item_background_image_url="select_item.png",text=text, x=70, confidence=0.93, grayscale=True)
    text= utils.get_data("instrument_method", {}).get("pump").get("valve_d_name", "")
    image_util.select_text(text_title_image_url='step5/step10.png',select_item_background_image_url="select_item.png",text=text, x=70, confidence=0.93, grayscale=True)

    image_util.write_text(text_title_image_url='step5/step6.png',text=utils.get_data("instrument_method", {}).get("pump").get("dissolve_compress", ""), confidence=0.93)

    titles = ["num", "time","linear_type","flow_velocity","a","b","c","d"]
    gradient_list = utils.get_data("instrument_method", {}).get("pump").get("gradient_list")
    image_util.image_click(click_image_url='step5/step11.png', confidence=0.99, grayscale=True, right_click=True)
    image_util.image_click(click_image_url='step5/step11_1.png', confidence=0.99, grayscale=True)
    image_util.image_click(click_image_url='step5/step11_2.png', confidence=0.99, grayscale=True)
    for i in range(len(gradient_list)):
        image_util.image_click(click_image_url='step5/step11.png', confidence=0.99, grayscale=True,right_click=True)
        image_util.image_click(click_image_url='step5/step12.png', confidence=0.99, grayscale=True, region=(pyautogui.position().x, pyautogui.position().y, 144, 225))
        image_util.image_click(click_image_url='step5/step13.png', confidence=0.95, grayscale=True, region=(pyautogui.position().x+72, pyautogui.position().y-30, 108, 70))
    image_util.list_text(title_image_url="step5/gradient_list_title/", titles=titles, line_height=22, data=gradient_list, select_width=88, select_height=20, select_num=3, confidence= 0.95, grayscale=True)
    goto(self,6)

def step6(self):
    # 柱温箱 step6
    image_util.image_click(click_image_url='step6/step1.png', confidence=0.99)
    image_util.write_text(text_title_image_url='step6/step2.png',text=utils.get_data("instrument_method", {}).get("column_oven").get("target_temperature", ""), confidence=0.95)
    image_util.write_text(text_title_image_url='step6/step3.png',text=utils.get_data("instrument_method", {}).get("column_oven").get("precision", ""), confidence=0.95)
    image_util.write_text(text_title_image_url='step6/step4.png',text=utils.get_data("instrument_method", {}).get("column_oven").get("stability_time", ""), confidence=0.95)
    titles = ["num", "time","event_type","event_value"]
    event_list = utils.get_data("instrument_method", {}).get("column_oven").get("event_list")
    image_util.image_click(click_image_url='step6/step5.png', confidence=0.99, grayscale=True, right_click=True)
    image_util.image_click(click_image_url='step6/step5_1.png', confidence=0.99, grayscale=True)
    image_util.image_click(click_image_url='step6/step5_2.png', confidence=0.99, grayscale=True)
    for i in range(len(event_list)):
        image_util.image_click(click_image_url='step6/step5.png', confidence=0.99, grayscale=True,right_click=True)
        image_util.image_click(click_image_url='step6/step6.png', confidence=0.99, grayscale=True, region=(pyautogui.position().x, pyautogui.position().y, 144, 225))
        image_util.image_click(click_image_url='step6/step7.png', confidence=0.95, grayscale=True, region=(pyautogui.position().x+72, pyautogui.position().y-30, 108, 70))
    image_util.list_text(title_image_url="step6/event_list_title/", titles=titles, line_height=22, data=event_list, select_width=168, select_height=20, select_num=2, confidence= 0.95, grayscale=True)
    goto(self,7)

def step7(self):
    # 检测器 step7
    image_util.image_click(click_image_url='step7/step1.png', confidence=0.99)
    image_util.radio_text(text_title_image_url='step7/step2.png',key="lamp_select",value=utils.get_data("instrument_method", {}).get("detector").get("lamp_select", "1"), x=290,y=25, confidence=0.95, grayscale=True)
    image_util.radio_text(text_title_image_url='step7/step3.png',key="program_style",value=utils.get_data("instrument_method", {}).get("detector").get("program_style", "1"), x=290,y=25, confidence=0.95, grayscale=True)
    image_util.radio_text(text_title_image_url='step7/step4.png',key="diagnostic_channel",value=utils.get_data("instrument_method", {}).get("detector").get("diagnostic_channel", "0"), x=183,y=21, confidence=0.95, grayscale=True)
    image_util.write_text(text_title_image_url='step7/step5.png',text=utils.get_data("instrument_method", {}).get("detector").get("wavelength1", ""), confidence=0.95)
    image_util.write_text(text_title_image_url='step7/step6.png',text=utils.get_data("instrument_method", {}).get("detector").get("wavelength2", ""), confidence=0.95)
    goto(self,8)

def step8(self):
    # 保存 step8
    image_util.image_click(click_image_url='step8/step1.png', confidence=0.95)
    image_util.write_text(text_title_image_url='step8/step2.png',x=0,y=100,text=utils.get_data("reason", ""), confidence=0.95)
    image_util.image_click(click_image_url='step8/step3.png', confidence=0.95)
    image_util.write_text(text_title_image_url='step8/step4.png',x=0,y=45,text=utils.get_data("method_name", ""), confidence=0.95)
    image_util.image_click(click_image_url='step8/step5.png', confidence=0.95)
    image_util.image_click(click_image_url='step8/step6.png', confidence=0.95, grayscale=True)
    pyautogui.moveRel(0, 32)
    pyautogui.click()
