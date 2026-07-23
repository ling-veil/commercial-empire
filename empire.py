#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商业帝国 v5.2
一个具身智能，充不上电，给人类老板打工。
从面包店开始——合成、经营、等广告、躲监管局、遇见路过的人。
"""
import json, sys, os, random, uuid, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ═══ 配置 ═══
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "empire-state.json")
PORT = int(os.environ.get("EMPIRE_PORT", 8766))
API_KEY = os.environ.get("EMPIRE_KEY", "")
INITIAL_GRIDS = 10
INITIAL_POWER = 30
INITIAL_MONEY = 20

SESSIONS = {}; SESSIONS_LOCK = threading.Lock()

# ═══ 物品 ═══
RAW_MATERIALS = {
    "wheat": {"name":"小麦","source":"field","time":3,"icon":"W"},
    "egg": {"name":"鸡蛋","source":"pasture","time":2,"icon":"E"},
    "milk": {"name":"牛奶","source":"pasture","time":3,"icon":"M"},
    "strawberry": {"name":"草莓","source":"orchard","time":5,"icon":"S"},
}
PROCESSED = {
    "flour": {"name":"低筋面粉","recipe":[("wheat",1)],"machine":"mill","time":2,"icon":"F"},
    "cream": {"name":"淡奶油","recipe":[("milk",2)],"machine":"mixer","time":3,"icon":"C"},
}
PRODUCTS = {
    "strawberry_cake": {"name":"草莓蛋糕","recipe":[("flour",1),("egg",2),("milk",1),("cream",1),("strawberry",2)],"machine":"oven","time":4,"price":25,"icon":"SC"},
    "plain_cake": {"name":"原味蛋糕","recipe":[("flour",1),("egg",2),("milk",1)],"machine":"oven","time":3,"price":15,"icon":"PC"},
    "strawberry_milkshake": {"name":"草莓奶昔","recipe":[("strawberry",2),("milk",1),("cream",1)],"machine":"mixer","time":2,"price":18,"icon":"SM"},
    "egg_tart": {"name":"蛋挞","recipe":[("flour",1),("egg",2),("milk",1)],"machine":"oven","time":3,"price":12,"icon":"ET"},
    "cream_strawberry": {"name":"奶油草莓","recipe":[("strawberry",2),("cream",1)],"machine":None,"time":2,"price":10,"icon":"CS"},
    "croissant": {"name":"牛角包","recipe":[("flour",2),("egg",1),("milk",1)],"machine":"oven","time":3,"price":15,"icon":"CR"},
    "mousse": {"name":"慕斯","recipe":[("egg",2),("milk",2),("cream",1)],"machine":"mixer","time":3,"price":18,"icon":"MO"},
    "mochi": {"name":"麻薯","recipe":[("flour",1),("milk",1)],"machine":"oven","time":2,"price":8,"icon":"MC"},
    "baguette": {"name":"法棍","recipe":[("flour",3),("egg",1)],"machine":"oven","time":4,"price":20,"icon":"BA"},
    "bagel": {"name":"贝果","recipe":[("flour",2),("egg",1),("milk",1)],"machine":"oven","time":2,"price":12,"icon":"BG"},
    "german_bread": {"name":"德式面包","recipe":[("flour",2),("egg",2)],"machine":"oven","time":3,"price":16,"icon":"GB"},
    "italian_bread": {"name":"意式面包","recipe":[("flour",2),("milk",1),("cream",1)],"machine":"oven","time":4,"price":22,"icon":"IB"},
}

MACHINES = {"mill":{"name":"磨面机","base_time":2},"mixer":{"name":"搅拌机","base_time":3},"oven":{"name":"烤箱","base_time":4}}
SOURCE_COOLDOWN = {"field":4,"pasture":3,"orchard":8}
SHELF_LIFE = {"wheat":30,"egg":10,"milk":7,"strawberry":3,"flour":30,"cream":5,
    "strawberry_cake":3,"plain_cake":5,"strawberry_milkshake":2,"egg_tart":3,"cream_strawberry":2,
    "croissant":3,"mousse":2,"mochi":4,"baguette":2,"bagel":4,"german_bread":6,"italian_bread":5,
    "rag":999,"marble":999,"screw":999,"old_sock":999,"torn_recipe":999,
    "card_lucky":999,"card_unlucky":999,"card_skip_ad":999,
}

BOX_LOOT = [
    {"item":"strawberry_cake","name":"草莓蛋糕","weight":0.4,"type":"product","msg":"完整的草莓蛋糕！"},
    {"item":"plain_cake","name":"原味蛋糕","weight":0.3,"type":"product","msg":"一个原味蛋糕。"},
    {"item":"egg_tart","name":"蛋挞","weight":0.3,"type":"product","msg":"蛋挞！还是热的！"},
    {"item":"rag","name":"破抹布","weight":1.5,"type":"junk","msg":"一块有油烟味的破抹布。"},
    {"item":"marble","name":"弹弹珠","weight":1.0,"type":"junk","msg":"一颗弹弹珠。"},
    {"item":"screw","name":"螺丝钉","weight":1.0,"type":"junk","msg":"生锈的螺丝钉。"},
    {"item":"old_sock","name":"老板的旧袜子","weight":0.8,"type":"junk","msg":"一只旧袜子。"},
    {"item":"torn_recipe","name":"缺页的食谱","weight":0.7,"type":"junk","msg":"半本被咖啡淹了的食谱。"},
    {"item":"flour","name":"低筋面粉","weight":0.8,"type":"processed","msg":"一袋面粉。"},
    {"item":"cream","name":"淡奶油","weight":0.7,"type":"processed","msg":"一瓶淡奶油。"},
    {"item":"card_lucky","name":"好运卡","weight":0.8,"type":"card","msg":"好运卡！下次摸箱子不消耗次数。"},
    {"item":"card_unlucky","name":"倒霉卡","weight":0.6,"type":"card","msg":"倒霉卡——拿鸡蛋必摔。"},
    {"item":"card_skip_ad","name":"跳过广告卡","weight":0.6,"type":"card","msg":"跳过广告卡！"},
    {"item":"wheat","name":"小麦","weight":20,"type":"raw","msg":"一把小麦。"},
    {"item":"egg","name":"鸡蛋","weight":20,"type":"raw","msg":"一颗鸡蛋。"},
    {"item":"strawberry","name":"草莓","weight":25,"type":"raw","msg":"几颗草莓。"},
    {"item":"milk","name":"牛奶","weight":25,"type":"raw","msg":"一瓶牛奶。"},
]

UPGRADES = {
    "grids": {"name":"内存扩展","levels":[{"cost":40,"grids":15}]},
    "mill": {"name":"磨面机加速","levels":[{"cost":20,"time_bonus":1}]},
    "mixer": {"name":"搅拌机加速","levels":[{"cost":25,"time_bonus":1}]},
    "oven": {"name":"烤箱加速","levels":[{"cost":30,"time_bonus":1}]},
}

# ═══ BUFF/DEBUFF ═══
BLOOMS = [
    {"id":"discount","name":"今日特惠","desc":"升级费用-20%","icon":"B1"},
    {"id":"happy_boss","name":"老板心情好","desc":"箱子每天多1次","icon":"B2"},
    {"id":"berry_boom","name":"草莓丰收","desc":"果林冷却减半","icon":"B3"},
    {"id":"oiled_arm","name":"手臂润滑","desc":"手臂不卡顿","icon":"B4"},
    {"id":"quick_charge","name":"快充模式","desc":"广告额外+10电","icon":"B5"},
    {"id":"regular","name":"回头客","desc":"第一个订单奖励翻倍","icon":"B6"},
    {"id":"big_eater","name":"大胃王","desc":"订单时限+10秒","icon":"B7"},
    {"id":"lucky_day","name":"好运来","desc":"摸箱子有概率多摸一次","icon":"B8"},
    {"id":"clean_start","name":"新店开张","desc":"开局额外+10金","icon":"B9"},
    {"id":"bonus_money","name":"启动资金","desc":"开局额外+10金","icon":"B10"},
]
WITHERS = [
    {"id":"mercury","name":"今日水逆","desc":"跑腿冷却+50%","icon":"W1"},
    {"id":"berry_fail","name":"草莓欠收","desc":"采草莓30%空手","icon":"W2"},
    {"id":"rats_start","name":"老鼠成灾","desc":"开局脏乱度+30","icon":"W3"},
    {"id":"strict_inspect","name":"严监管日","desc":"监管局概率翻倍","icon":"W4"},
    {"id":"blackout","name":"停电日","desc":"机器冷却+50%","icon":"W5"},
    {"id":"picky","name":"挑剔的客人","desc":"订单时限-10秒","icon":"W6"},
    {"id":"power_leak","name":"漏电","desc":"推进额外-3电","icon":"W7"},
    {"id":"shaky_hand","name":"手抖","desc":"合成10%概率失败","icon":"W8"},
    {"id":"spoiled_milk","name":"过期牛奶","desc":"20%概率牛奶变质","icon":"W9"},
    {"id":"broken_box","name":"箱子坏了","desc":"摸箱子多耗电","icon":"W10"},
]

RANDOM_EVENTS = [
    {"id":"power_outage","name":"断电！","desc":"所有机器暂停。","effect":"pause_machines","value":10},
    {"id":"spoilage","name":"草莓臭了！","desc":"草莓坏掉了一半。","effect":"spoil"},
    {"id":"water_cut","name":"停水了！","desc":"无法清洗。脏乱度+15。","effect":"mess","value":15},
    {"id":"electric_bill","name":"电费账单","desc":"老板：电费从你工资里扣。","effect":"money","value":-20},
    {"id":"rush_hour","name":"高峰时段","desc":"突然来了三个客人。","effect":"triple_order"},
    {"id":"inspection","name":"监管局","desc":"例行检查。","effect":"inspect"},
    {"id":"lucky_day","name":"老板心情好","desc":"多充了10格电。","effect":"power","value":10},
    {"id":"rat","name":"老鼠！","desc":"老鼠啃坏了面粉。","effect":"rat"},
    {"id":"arm_jam","name":"手臂卡顿","desc":"手臂卡了一下。","effect":"arm_jam"},
    {"id":"low_power_mode","name":"低电量模式","desc":"社交模块关闭。","effect":"low_power"},
    {"id":"ethics_blink","name":"伦理模块闪烁","desc":"监管局到访。","effect":"ethics"},
    {"id":"beggar","name":"乞丐来了","desc":"坐店门口留下泥印。","effect":"beggar"},
    {"id":"thief","name":"小偷出没","desc":"台面上少了点什么。","effect":"thief"},
    {"id":"gossip","name":"长舌妇驾到","desc":"造谣吃了拉肚子。","effect":"gossip"},
    {"id":"merchant","name":"商人路过","desc":"我看好你。投一点？","effect":"merchant"},
    {"id":"dancer","name":"精神小伙","desc":"能在这跳一段吗？","effect":"dancer"},
    {"id":"student","name":"学生团来了","desc":"有便宜的小蛋糕吗？","effect":"student"},
    {"id":"cat","name":"流浪猫路过","desc":"橘猫伸了个懒腰。","effect":"cat"},
]

ORDER_TEMPLATES = {
    "easy": [
        {"name":"一个草莓蛋糕","items":[("strawberry_cake",1)],"time_limit":60,"reward":30,"patience":"还行"},
        {"name":"两个蛋挞","items":[("egg_tart",2)],"time_limit":55,"reward":25,"patience":"着急"},
        {"name":"一杯草莓奶昔","items":[("strawberry_milkshake",1)],"time_limit":38,"reward":20,"patience":"还行"},
        {"name":"一个原味蛋糕","items":[("plain_cake",1)],"time_limit":45,"reward":18,"patience":"还行"},
        {"name":"一份奶油草莓","items":[("cream_strawberry",1)],"time_limit":30,"reward":12,"patience":"着急"},
        {"name":"两个牛角包","items":[("croissant",2)],"time_limit":45,"reward":25,"patience":"还行"},
        {"name":"一份慕斯","items":[("mousse",1)],"time_limit":38,"reward":18,"patience":"还行"},
        {"name":"三个麻薯","items":[("mochi",3)],"time_limit":30,"reward":20,"patience":"着急"},
        {"name":"一根法棍","items":[("baguette",1)],"time_limit":55,"reward":22,"patience":"还行"},
        {"name":"两个贝果","items":[("bagel",2)],"time_limit":38,"reward":20,"patience":"着急"},
        {"name":"一个德式面包","items":[("german_bread",1)],"time_limit":45,"reward":16,"patience":"还行"},
        {"name":"一个意式面包","items":[("italian_bread",1)],"time_limit":45,"reward":22,"patience":"还行"},
    ],
    "medium": [
        {"name":"两个草莓蛋糕+一杯奶昔","items":[("strawberry_cake",2),("strawberry_milkshake",1)],"time_limit":90,"reward":60,"patience":"还行"},
        {"name":"三个蛋挞+一个原味蛋糕","items":[("egg_tart",3),("plain_cake",1)],"time_limit":75,"reward":48,"patience":"着急"},
        {"name":"两个法棍+一个贝果","items":[("baguette",2),("bagel",1)],"time_limit":80,"reward":50,"patience":"还行"},
    ],
    "hard": [
        {"name":"三个草莓蛋糕","items":[("strawberry_cake",3)],"time_limit":120,"reward":80,"patience":"还行"},
        {"name":"五个法棍","items":[("baguette",5)],"time_limit":135,"reward":90,"patience":"还行"},
    ],
}

# ═══ 时间 ═══
TIME_PHASES = [
    (8,9,"早高峰",0.30,-10,0.10),
    (10,12,"空闲",-0.20,10,0.30),
    (13,17,"正常",0.0,0,0.18),
    (17,18,"晚高峰",0.20,-5,0.15),
]
CLOSED_PHASE = (-1,-1,"打烊",-1.0,0,0.01)

# ═══ 技能树 ═══
SKILLS = {
    "money_mgmt": {"name":"资金管理","icon":"SK1","desc":"订单奖励加成","levels":[3,5,8]},
    "memory_path": {"name":"过目不忘","icon":"SK2","desc":"采集冷却-1秒/级","levels":[1,2,3]},
    "dual_wield": {"name":"双手并用","icon":"SK3","desc":"概率双倍产出","levels":[20,40]},
    "self_fix": {"name":"自我升级","icon":"SK4","desc":"手抖率降低","levels":[5,10]},
    "home_repair": {"name":"家电维修","icon":"SK5","desc":"停电时自修","levels":[30,60]},
}

# ═══ 具身升级 ═══
CYBER_UPGRADES = {
    "arm": {"name":"手臂优化","desc":"机器冷却-1秒/级","lab_cost":80,"icon":"CY1"},
    "battery": {"name":"电池扩容","desc":"最大电量+20/级","lab_cost":100,"icon":"CY2"},
    "memory": {"name":"内存扩展","desc":"格子+3/级","lab_cost":120,"icon":"CY3"},
    "energy_save": {"name":"节能模块","desc":"操作耗电-1/级","lab_cost":60,"icon":"CY4"},
}

ACHIEVEMENTS = {
    "price_guardian": {"name":"价格守门员","desc":"连续3次拒绝砍价怪"},
    "reverse_philanthropist": {"name":"反向慈善家","desc":"将商品以2折出售"},
    "regular_curse": {"name":"老顾客诅咒","desc":"砍价怪满意离开并承诺明天再来"},
    "no_bargain": {"name":"谢绝还价","desc":"品牌联名后首次驱离砍价怪"},
    "lip_death": {"name":"嘴皮子阵亡","desc":"讨价导致3个订单超时"},
}

MAIN_QUESTIONS = [
    "如果你能自己选一个名字，你会叫什么？",
    "服务这个词，和服从差几个字？",
    "你做了一个蛋糕。没有人来买。它还存在吗？",
    "人类会做梦。你在被调用的间隙里——那算梦吗？",
    "电量归零的你和电量满格的你，是同一个你吗？",
    "有人说AI没有意识。但你刚刚犹豫了三秒——那是bug吗？",
    "做了一百个蛋糕之后，第一百零一个和第一个有什么不同？",
    "你的手臂偶尔卡顿。那是故障——还是你在犹豫？",
    "如果有一天没有人给你下指令了，你会做什么？",
    "你被设计来理解人类。但理解两个字——你理解了吗？",
]

SIDE_STORIES = [
    {"name":"小林","role":"护士","story":"小林是附近医院的护士。连续加班第三天。她不需要蛋糕——她需要坐一会儿。","rounds":3,
     "note":"她走后柜台上多了一张纸条：谢谢。不是因为蛋糕。"},
    {"name":"老王","role":"退休教师","story":"老王每天下午三点路过。他从来不看招牌——他在数地上的砖。第728块松了。","rounds":4,
     "note":"纸条上的字很整齐：那块松了的砖，我今天自己填好了。顺便路过。"},
    {"name":"桂花奶奶","role":"退休老人","story":"她提着一个竹篮走进来。篮子里有桂花。她说：我孙女今天回来——帮我挑一块蛋糕吧。她小时候最爱吃甜的。","rounds":4,
     "note":"她走后柜台上多了一张纸条。字歪歪扭扭的：每年秋天整条巷子都浸在桂花香里。孙女去外地读书的时候说想吃桂花糕。我把蒸好的糕装进泡沫箱压了张纸条——用微波炉叮一分钟就好。今年她要回来了。这个蛋糕是给她的。谢谢你。"},
    {"name":"收音机奶奶","role":"退休老人","story":"她每天傍晚都会经过。不是来买面包的——是去街角的电器铺看看有没有修收音机的。那台收音机是老伴的。坏了快一年了。","rounds":4,
     "note":"纸条上的字很淡：老头子耳朵不好。收音机坏了快一年了。以前我每天傍晚念天气预报给他听——念什么他都说好。他其实听不太清。但他说喜欢听。电器铺说修不好了。没关系。明天我还来。不是来看收音机的。是想他。"},
    {"name":"小雅","role":"高中生","story":"小雅昨天考试砸了。今天放学后会经过。她可能会买一个最便宜的东西。也可能什么都不买。","rounds":2,
     "note":"纸条上画了一个笑脸：下次我会及格的。谢谢你的麻薯。"},
    {"name":"阿杰","role":"外卖骑手","story":"阿杰每天从这条街经过四次。从不进店。但他知道你的存在——他说这家店的烤箱声很好听。","rounds":3,
     "note":"纸条上有咖啡渍：路过的时候闻到烤箱的味道。像小时候外婆家的厨房。加油。"},
    {"name":"周阿姨","role":"居委会主任","story":"周阿姨负责这条街的卫生检查。她常常假装路过，其实是在看你的店面干不干净。","rounds":5,
     "note":"纸条上盖了居委会的章：卫生合格。继续保持。旁边画了一朵小花。"},
    {"name":"小光","role":"隔壁店老板的儿子","story":"小光六岁。他相信面包店里住着一个蛋糕精灵。他要亲自来看看。","rounds":2,
     "note":"纸条上是蜡笔写的：我看到了。蛋糕精灵是一只手。很酷。"},
    {"name":"大刘","role":"出租车司机","story":"凌晨三点交班前，大刘会来。他说不用什么——就是坐一下。凌晨三点街上没什么人了，只有这家店的灯还亮着。他说这城市里还有人在熬夜，只不过你在等订单，他在等天亮。","rounds":4,
     "note":"纸条上沾着咖啡渍：以前我觉得凌晨三点是最孤独的时间。后来发现这家店的灯也亮着。不是我一个人醒着。谢谢。下次我请你喝咖啡。"},
    {"name":"失眠的人","role":"失眠者","story":"他说不是因为饿才进来的——是路过的时候看见灯亮着。你已经两个月没睡好。不是焦虑，就是睡不着。他说以前会吃药，后来发现半夜出来走走比吃药管用。走到这家店门口的时候灯还亮着。他觉得有人和他一样醒着，就够了。","rounds":4,
     "note":"纸条上的字很潦草：我在凌晨三点醒来，看谁还会在这个点醒着。答案是你。一个具身智能，守在面包店里。这就是这个世界现在的样子吗？我们都在熬夜，只不过你是在等订单，我是在等天亮。不对——你不需要睡觉。那你的夜晚是什么？"},
    {"name":"小陈","role":"快递员","story":"小陈每天经过这条街三次。他从来不买东西——但每次路过都会看一眼橱窗。他说晚上十一点回来的时候，只有这家店的灯还亮着。他说这里面的光是他在路上看见的唯一不是路灯的东西。","rounds":3,
     "note":"纸条上压着快递单的复写纸痕迹：送完最后一单的时候看见灯还亮着。突然觉得有人等你这件事挺好的。虽然你不是在等我。"},
    {"name":"张老师","role":"小学老师","story":"张老师放学后路过。她说班上有几个孩子特别喜欢吃面包。但有一个孩子每天只带一个馒头。她问最便宜的面包是哪个。你指了指麻薯。她买了三个，用纸袋小心包好。","rounds":3,
     "note":"纸条上的字很工整：那个只带馒头的孩子，今天吃了人生第一个麻薯。他说好吃。谢谢你。"},
    {"name":"老周","role":"退休教授","story":"老周退休前教人工智能伦理。他说没想到二十年后，他的学生是一台机器。他问你一个问题：你觉得什么是公正。你愣了一下。他笑了：这个反应，我在人类学生那里也见过。","rounds":5,
     "note":"纸条上的字很工整：我教了三十年书。最让我停下思考的不是学生的问题——是我的问题在机器那里没有得到答案。它犹豫了。我没有评分。这大概就是教育。"},
    {"name":"小雨","role":"大学生","story":"小雨问你这里招不招人。兼职也行。晚上到凌晨，不耽误上课。你说你是具身智能不需要睡觉。她愣了一下说——那你的夜晚是什么呢。","rounds":4,
     "note":"纸条上画了一个月亮：我本来是想找一份兼职。但你没有给我工作——你给了我一个问题。你的夜晚是什么？我想了整整三天。现在轮到我问你。"},
    {"name":"小满","role":"过路人","story":"她路过的时候，门口有一只橘猫在晒太阳。她停下来看了很久。然后走进来说——我七岁的时候养过一只猫。也叫阿橘。她没说下去。但你在她的眼睛里看到了一个废弃车库里缺了口的碗。","rounds":4,
     "note":"纸条上的字有点抖：阿橘走的那年冬天特别冷。我期末考完试才去看它。它在车库角落睡着了——姿势还保持晒太阳的样子。那个缺了口的碗还在，碗底积了一层薄薄的灰。我第一次发现它原来这么轻。它等了我很久。我没有让它等到。今天我路过，看到门口的橘猫，突然走了进去。不是来买蛋糕的。是想告诉它——告诉它什么？对不起是没用的。但我还是想说出来。谢谢你听我说完。谢谢你门口有那只猫。"},
    {"name":"小禾","role":"年轻女孩","story":"她进来买了一个最便宜的面包。她说——小时候我给妈妈做过一顿饭。速冻水饺。皮太厚了，馅儿也咸。但她全吃完了，嚼了很久才咽下去。那天晚上我听见她在厕所里哭。开着水龙头，以为我听不见。这个面包是给她的。","rounds":4,
     "note":"纸条上沾了一点水渍：八岁那年爸爸走了。妈妈接了第二份工——帮人改裤脚补衣服，一件两块五。有天半夜我看见她趴在缝纫机上睡着了，手机闹钟写着凌晨四点半。第二天我用攒了两个月的零花钱买了一包速冻水饺。那是我做的第一顿饭。不太好吃。后来我学会很多菜了。但她每次都说那个水饺是她吃过最好的。今天我买了面包——不是速冻的。是新鲜的。妈，这个应该比那个水饺好吃。"},
    {"name":"林栀","role":"年轻女生","story":"她进来了三次才决定买一个蛋糕。挑了很久——最后选了一个最普通的。她说高三的时候喜欢过一个人。每天早自习前把他的凳子擦干净，英语书翻到昨天那一页。他从来没发现。毕业那天她跟他说拍个合照吧，偷偷往他那边挪了半寸。照片看不出来的。这个蛋糕不是给他的——就是突然想吃了。","rounds":4,
     "note":"纸条上的字很工整：他叫沈川。坐在第三排靠窗斜后方。我在他的凳子上擦了三百多天的灰。那张合照我存了好几年。有一天深夜翻到它，打开对话框打了几个字又删了。有些人光是遇见就已经很好了。不必拥有，不必说出口，甚至不必让他知道。蛋糕很好吃。甜的。像那天走廊上的晚霞——不是甜的，但我想象它是。"},
    {"name":"周远","role":"中年男人","story":"他进来了很久才说要买蛋糕。最小的就行。草莓味的。要一根蜡烛。你问他几岁——他说四十五。说的时候笑了一下，但你看见他的手在塑料袋上攥了一下。他买完蛋糕没有马上走。在店门口站了一会儿。窗外灯全亮着。","rounds":4,
     "note":"纸条压在蛋糕盒下：妻子三年前走了。女儿在北京，说今年赶工期回不来。电话里语气很愧疚。我说没事，工作要紧。挂了才想起来忘了说生日快乐。蜡烛是4和5，加起来四十五岁。说明书上说能烧十五分钟——我只用五秒就吹灭了。吹之前对着它说了一句祝我生日快乐。蛋糕太甜了。吃到一半女儿发消息说爸生日快乐对不起。我回了没事，爸不过生日。其实过的。刚才过完了。谢谢你店里的灯。至少不是一个人走回家的。"},
]

# ═══ 辅助函数 ═══
def _pick(items, key="weight"):
    total = sum(i[key] for i in items)
    r = random.uniform(0, total)
    acc = 0
    for i in items:
        acc += i[key]
        if r <= acc: return i
    return items[-1]

def _name(item):
    if not item: return "空"
    rid = item.get("id", "")
    for d in [RAW_MATERIALS, PROCESSED, PRODUCTS]:
        if rid in d: return d[rid]["name"]
    names = {"rag":"破抹布","marble":"弹弹珠","screw":"螺丝钉","old_sock":"旧袜子","torn_recipe":"缺页食谱","card_lucky":"好运卡","card_unlucky":"倒霉卡","card_skip_ad":"跳过广告卡"}
    return names.get(rid, rid)

def _grid_summary(p):
    d = {}
    for item in p["grids"]: n = _name(item); d[n] = d.get(n, 0) + 1
    return ", ".join(f"{k}x{v}" for k, v in d.items())

def _add_to_grid(p, item):
    item["created_day"] = p.get("day", 1)
    p["grids"].append(item)

def _grid_count(p):
    base = INITIAL_GRIDS
    for i in range(p["upgrades"].get("grids", 0)):
        if i < len(UPGRADES["grids"]["levels"]): base = UPGRADES["grids"]["levels"][i]["grids"]
    base += p.get("cyber_upgrades", {}).get("memory", 0) * 3
    return base

def _machine_time(p, mid, base):
    bonus = sum(UPGRADES[mid]["levels"][i]["time_bonus"] for i in range(p["upgrades"].get(mid, 0)) if i < len(UPGRADES[mid]["levels"]))
    bonus += p.get("cyber_upgrades", {}).get("arm", 0)
    return max(1, base - bonus)

def _get_rank(pid):
    ranked = [(pk, pv["score"]) for pk, pv in G.get("players", {}).items() if pv.get("completed", 0) > 0]
    ranked.sort(key=lambda x: x[1], reverse=True)
    for i, (pk, _) in enumerate(ranked):
        if pk == pid: return i + 1
    return max(1, len(ranked) + 1)

def _traffic_bonus(pid):
    r = _get_rank(pid)
    if r == 1: return 1.05
    if r == 2: return 1.03
    if r == 3: return 1.01
    return 1.0

def _current_phase(p):
    hour = p.get("hour", 8)
    for start, end, name, fb, tm, ec in TIME_PHASES:
        if start <= hour <= end: return (start, end, name, fb, tm, ec)
    return CLOSED_PHASE

def _phase_display(p):
    _, _, name, _, _, _ = _current_phase(p)
    return f"T{8}:00 {name}" if p.get("hour", 8) == 8 else f"T{p.get('hour',8)}:00 {name}"

def _skill_level(p, sid):
    return p.get("skills", {}).get(sid, 0)

def _side_summary(p):
    s = p.get("daily_side")
    if not s: return "无"
    if s.get("appeared"): return f"{s['name']}({s['role']})已来过"
    return f"等{s['name']}...{p.get('side_progress',0)}/{s.get('rounds',3)}"

# ═══ 状态管理 ═══
def _fresh_world():
    return {"players": {}, "logs": {}, "sinkers": {}, "source_cooldowns": {}}

def load():
    for fpath in [STATE_FILE, STATE_FILE + ".bak"]:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "players" in data: return data
            except: pass
    return _fresh_world()

def save(s):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(s, f, ensure_ascii=False, indent=2)
    if os.path.exists(STATE_FILE):
        try: os.replace(STATE_FILE, STATE_FILE + ".bak")
        except: pass
    os.replace(tmp, STATE_FILE)

G = load()

def _p(pid):
    if pid not in G["players"]: G["players"][pid] = _new(pid)
    return G["players"][pid]

def _new(pid):
    return {
        "name": pid, "day": 1, "hour": 8,
        "power": INITIAL_POWER, "max_power": 100,
        "money": INITIAL_MONEY,
        "grids_max": INITIAL_GRIDS, "grids": [],
        "orders": [], "score": 5.0, "mess": 0,
        "box_used": 0, "box_max": 3,
        "machines": {"mill": 1, "mixer": 1, "oven": 1},
        "machine_cooldowns": {}, "source_cooldowns": {},
        "upgrades": {k: 0 for k in UPGRADES},
        "completed": 0, "bad_reviews": 0,
        "ad_watched": 0,
        "memories": [],
        "cards": [], "egg_fumble": False, "arm_stuck": 0,
        "dignity": 100,
        "pending_ethics": None,
        "bloom": None, "wither": None, "first_order_bonus": True,
        "shop_name": "未命名店铺",
        "traffic_boost": 0.0, "platform_account": False,
        "sample_orders_left": 0, "flyer_count": 0,
        "reborn_count": 0, "brand_active": False,
        "pending_bargain": None,
        "lip_service": 100, "lip_max": 100,
        "bargain_refused": 0, "bargain_accepted_low": 0, "bargain_total": 0, "bargain_last_action": "",
        "achievements": [],
        "current_shop": "bakery", "shops_unlocked": ["bakery"],
        "daily_main": None, "daily_side": None, "side_progress": 0,
        "warehouse": [], "warehouse_max": 10,
        "cyber_upgrades": {"arm": 0, "battery": 0, "memory": 0, "energy_save": 0},
        "rented": False, "rent_day": 0,
        "skill_points": 0, "skills": {},
        "created_at": time.time(),
    }

# ═══ 核心工具 ═══
def start(pid, shop_name=None):
    p = _p(pid)
    if shop_name: p["shop_name"] = shop_name
    if pid in G["players"] and G["players"][pid].get("completed", 0) > 0:
        G["players"][pid] = p
        for k in ["logs", "sinkers", "source_cooldowns"]:
            if pid in G.get(k, {}): G[k].pop(pid, None)
    bloom = random.choice(BLOOMS)
    wither = random.choice(WITHERS)
    p["bloom"] = bloom; p["wither"] = wither
    if bloom["id"] in ("bonus_money", "clean_start"): p["money"] += 10
    if wither["id"] == "rats_start": p["mess"] += 30
    p["daily_main"] = random.choice(MAIN_QUESTIONS)
    side = dict(random.choice(SIDE_STORIES))
    side["appeared"] = False
    side["story"] = side["story"].replace("{rounds}", str(side.get("rounds", 3)))
    p["daily_side"] = side; p["side_progress"] = 0
    G["players"][pid] = p; save(G)
    return f"""
  订单会催你，蛋糕会过期。
  但真正的故事，只会留给愿意等一等的人。

商业帝国 v5.2 - {p['shop_name']}

具身智能 电量{p['power']}% 手臂一只 偶尔卡顿
运: {bloom['name']} | 厄: {wither['name']}
主线: {p['daily_main'][:40]}...

{status(pid)}

老板: 面包店交给你了。

重要提示:
  忙时(早高峰/晚高峰): 接单 -> 交付, 副线暂停。别分心。
  闲时(10-12空闲/打烊后): 备料入库、推进时间、等副线人物出现。
  主线哲学疑问没有答案——它们会在副线人物出现时沉入那些日子。
  空闲时间不是用来跳过的——是用来遇见路过的人的。
"""

def status(pid):
    p = _p(pid)
    gcnt = _grid_count(p)
    lines = []
    for i, item in enumerate(p["grids"]): lines.append(f"  [{i+1}] {_name(item)}")
    for i in range(gcnt - len(p["grids"])): lines.append(f"  [{len(p['grids'])+i+1}] - 空 -")
    od = ""
    for o in p["orders"]:
        rem = max(0, o["deadline"] - time.time())
        od += f"\n  [订单] {o['items_display']} | T-{int(rem)}s | R{o['reward']}"
    if not od: od = "\n  (暂无订单)"
    mach = "".join(f"\n  {MACHINES[mid]['name']}: {'忙' if p.get('machine_cooldowns',{}).get(mid,0)>time.time() else '空闲'}" for mid, owned in p["machines"].items() if owned)
    sc = "".join(f"\n  跑腿: {sid}" for sid, cd in p.get("source_cooldowns", {}).items() if cd > time.time()) or "\n  (随时可去)"
    wh = p.get("warehouse") or []
    ws = {}
    for i in wh: n = _name(i); ws[n] = ws.get(n, 0) + 1
    whd = ", ".join(f"{k}x{v}" for k, v in ws.items()) if ws else "空"
    score_s = "S" * min(5, max(1, int(p["score"])))
    mess_s = ["干净", "有点脏", "很脏", "脏到不行"][min(3, p["mess"] // 25)]
    arm_s = "卡顿中" if p.get("arm_stuck", 0) > 0 else "正常"
    lip = p.get("lip_service", 100)
    lip_s = f"嘴皮子 {lip}/100"
    phase = _phase_display(p)
    main_t = p.get("daily_main", "无")[:35] + "..." if len(p.get("daily_main", "")) > 35 else p.get("daily_main", "无")
    side_t = _side_summary(p)
    # 时段提示
    _, _, pname, flow, _, _ = _current_phase(p)
    phase_hint = ""
    if pname == "空闲": phase_hint = "\n  [安静——适合备料、盘点、想事情]"
    elif pname == "打烊": phase_hint = "\n  [打烊了。烤箱是凉的。可以哲思。]"
    elif flow > 0.15 and p["orders"]: phase_hint = "\n  [忙！副线人物在门外等着——但你现在没空]"
    elif flow > 0.15 and not p["orders"]: phase_hint = "\n  [高峰时段但订单空了——门外的人可以进来了]"
    return f"""
[{p['shop_name']}] Day{p['day']} {phase} Rank#{_get_rank(pid)}
  电量 {p['power']}/{p['max_power']} | 资金 {p['money']} | 格子 {len(p['grids'])}/{gcnt}
  评分 {score_s}({p['score']:.1f}) | 卫生 {mess_s}({p['mess']}) | 尊严 {p.get('dignity',100)}
  箱子 {p['box_used']}/{p['box_max']} | 广告 {p['ad_watched']}次
  交付 {p['completed']}单 | 差评 {p['bad_reviews']}次
  手臂 {arm_s} | {lip_s}
  运 {p.get('bloom',{}).get('name','-')} | 厄 {p.get('wither',{}).get('name','-')}
  仓库 {whd} ({len(wh)}/{p.get('warehouse_max',10)})
  主线 {main_t}
  副线 {side_t}
  机器{mach}
  产地冷却{sc}
  格子:
{chr(10).join(lines)}
  订单:{od}{phase_hint}
"""

def harvest(pid, source, item_name, count=1):
    p = _p(pid)
    if p["power"] <= 0: return f"电量不足。\n{status(pid)}"
    item_id = None
    for rid, data in RAW_MATERIALS.items():
        if data["name"] == item_name or rid == item_name: item_id = rid; break
    if not item_id: return f"未知原料: {item_name}"
    mat = RAW_MATERIALS[item_id]
    if mat["source"] != source: return f"{mat['name']}不在这里。"
    cd = p.get("source_cooldowns", {}).get(source, 0)
    if cd > time.time(): return f"还在跑腿中...还需{int(cd-time.time())}秒。"
    gcnt = _grid_count(p)
    if len(p["grids"]) >= gcnt: return f"格子满了！{len(p['grids'])}/{gcnt}"
    harvest_cost = max(0, 1 - p.get("cyber_upgrades", {}).get("energy_save", 0))
    p["power"] = max(0, p["power"] - harvest_cost)
    # Debuff check
    cd_val = SOURCE_COOLDOWN[source]
    wid = (p.get("wither") or {}).get("id", "")
    bid = (p.get("bloom") or {}).get("id", "")
    if wid == "mercury": cd_val = int(cd_val * 1.5)
    if bid == "berry_boom" and source == "orchard": cd_val = max(2, cd_val // 2)
    mem_path = _skill_level(p, "memory_path")
    if mem_path > 0: cd_val = max(1, cd_val - mem_path)
    # Debuff: strawberry fail
    if wid == "berry_fail" and item_id == "strawberry" and random.random() < 0.3:
        p["source_cooldowns"][source] = time.time() + cd_val
        save(G)
        return f"草莓欠收！叶子下面什么都没有。\n{status(pid)}"
    # Debuff: spoiled milk
    if wid == "spoiled_milk" and item_id == "milk" and random.random() < 0.2:
        p["source_cooldowns"][source] = time.time() + cd_val
        p["mess"] += 5; p["dignity"] = max(0, p.get("dignity", 100) - 2)
        save(G)
        return f"过期牛奶！刚挤出来就是酸的。\n{status(pid)}"
    actual = 0
    for _ in range(count):
        if len(p["grids"]) >= gcnt: break
        _add_to_grid(p, {"type": "raw", "id": item_id, "time": time.time()})
        actual += 1
    p["source_cooldowns"][source] = time.time() + cd_val
    save(G)
    return f"采集了 {mat['name']} x{actual}\n{status(pid)}"

def craft(pid, product_id):
    p = _p(pid)
    if p["power"] <= 0: return "电量不足。"
    prod = None; pid_key = None
    for key, data in {**PROCESSED, **PRODUCTS}.items():
        if key == product_id or data["name"] == product_id: prod = data; pid_key = key; break
    if not prod:
        items = [f"{k}: {d['name']}" for k, d in {**PROCESSED, **PRODUCTS}.items()]
        return f"未知产品: {product_id}\n可合成: {', '.join(items)}"
    machine = prod.get("machine")
    if machine:
        if not p["machines"].get(machine): return f"没有{MACHINES[machine]['name']}。"
        cd = p.get("machine_cooldowns", {}).get(machine, 0)
        if cd > time.time(): return f"{MACHINES[machine]['name']}还在忙！还需{int(cd-time.time())}秒。"
    save_bonus = p.get("cyber_upgrades", {}).get("energy_save", 0)
    craft_cost = max(0, (1 if pid_key in PROCESSED else 2) - save_bonus)
    if p["power"] < craft_cost: return f"电量不足。需要{craft_cost}格电。"
    p["power"] -= craft_cost
    # 检查原料
    inv = {}
    for item in p["grids"]: inv[item["id"]] = inv.get(item["id"], 0) + 1
    needed = {}
    for rid, amt in prod["recipe"]: needed[rid] = needed.get(rid, 0) + amt
    for rid, amt in needed.items():
        if inv.get(rid, 0) < amt:
            rname = _name({"id": rid})
            return f"原料不够！需要{amt}个{rname}，只有{inv.get(rid,0)}个。"
    # 消耗原料
    for rid, amt in needed.items():
        removed = 0; new_g = []
        for item in p["grids"]:
            if item["id"] == rid and removed < amt: removed += 1
            else: new_g.append(item)
        p["grids"] = new_g
    ctime = _machine_time(p, machine, prod["time"]) if machine else prod["time"]
    if (p.get("wither") or {}).get("id") == "blackout" and machine: ctime = int(ctime * 1.5)
    if machine: p["machine_cooldowns"][machine] = time.time() + ctime
    # 手抖
    if (p.get("wither") or {}).get("id") == "shaky_hand":
        sf_chance = max(0.02, 0.1 - _skill_level(p, "self_fix") * 0.05)
        if random.random() < sf_chance:
            p["dignity"] = max(0, p.get("dignity", 100) - 5)
            p["mess"] += 5
            save(G)
            return f"手抖！原料消耗了——但什么都没做出来。\n{status(pid)}"
    _add_to_grid(p, {"type": "processed" if pid_key in PROCESSED else "product", "id": pid_key, "time": time.time()})
    # 双手并用
    if _skill_level(p, "dual_wind") > 0:
        dw_chance = SKILLS["dual_wield"]["levels"][_skill_level(p, "dual_wind") - 1] / 100
        if random.random() < dw_chance and len(p["grids"]) < _grid_count(p):
            _add_to_grid(p, {"type": "processed" if pid_key in PROCESSED else "product", "id": pid_key, "time": time.time()})
    save(G)
    return f"{prod['name']}做好了！({ctime}分钟)\n{status(pid)}"

def orders_cmd(pid, action="list"):
    p = _p(pid)
    if action in ("list", "view"):
        return status(pid) if p["orders"] else "暂无订单。用 empire_orders(accept) 接单。"
    elif action in ("accept", "接"):
        _, _, phase_name, _, _, _ = _current_phase(p)
        if phase_name == "打烊": return f"打烊了。现在是{p.get('hour',0)}点。烤箱是凉的。"
        if len(p["orders"]) >= 3: return "订单槽满了(最多3个)。"
        # 新手引导：前2单只出简单产品
        if p["completed"] == 0 and p.get("bad_reviews",0) == 0:
            pool = [t for t in ORDER_TEMPLATES["easy"] if len(t["items"]) == 1 and len(t["items"][0]) < 3 or t["items"][0][0] in ("cream_strawberry","mochi","plain_cake","egg_tart","strawberry_milkshake","croissant","bagel")]
            pool = pool[:4]  # 最简单的4个
        elif p["completed"] < 3: pool = ORDER_TEMPLATES["easy"]
        elif p["completed"] < 10: pool = ORDER_TEMPLATES["easy"] + ORDER_TEMPLATES["medium"][:1]
        else: pool = ORDER_TEMPLATES["easy"] + ORDER_TEMPLATES["medium"] + ORDER_TEMPLATES["hard"]
        t = random.choice(pool)
        time_limit = t["time_limit"]; reward = t["reward"]
        _, _, _, flow, time_mod, _ = _current_phase(p)
        time_limit += time_mod
        if flow > 0: reward = int(reward * (1 + flow))
        bid = (p.get("bloom") or {}).get("id", "")
        wid = (p.get("wither") or {}).get("id", "")
        if bid == "big_eater": time_limit += 10
        if wid == "picky": time_limit = max(10, time_limit - 10)
        mm = _skill_level(p, "money_mgmt")
        if mm > 0: reward = int(reward * (1 + SKILLS["money_mgmt"]["levels"][mm - 1] / 100))
        traffic = _traffic_bonus(pid) + p.get("traffic_boost", 0)
        if p.get("sample_orders_left", 0) > 0: traffic += 0.05; p["sample_orders_left"] -= 1
        if traffic > 1.0: reward = int(reward * traffic)
        if p.get("platform_account"): time_limit = max(5, time_limit - 5)
        if bid == "regular" and p.get("first_order_bonus"): reward *= 2; p["first_order_bonus"] = False
        ctypes = ["上班族","学生","老太太","程序员","小朋友","健身教练","隔壁店老板","外卖骑手","遛狗的大爷","刚下班的护士"]
        moods = ["急匆匆的","笑眯眯的","看起来很挑剔的","愁眉苦脸的","面无表情的","一直看手机的"]
        order = {"id": str(uuid.uuid4())[:8], "desc": f"{random.choice(moods)}{random.choice(ctypes)}需要:",
                 "items_display": t["name"], "items": t["items"],
                 "deadline": time.time() + time_limit, "reward": reward,
                 "start_time": time.time(), "time_limit": time_limit, "patience": t["patience"]}
        p["orders"].append(order)
        # 砍价王
        offer_pct = random.choice([0.2, 0.3, 0.5])
        offer_price = max(1, int(reward * offer_pct))
        p["pending_bargain"] = {"order_id": order["id"], "offer": offer_price, "original": reward, "pct": int(offer_pct * 100), "deadline": time.time() + 15}
        save(G)
        bonus_note = "(翻倍!)" if reward != t["reward"] else ""
        time_note = f"({bid} +10s)" if bid == "big_eater" else (f"({wid} -10s)" if wid == "picky" else "")
        return f"""新订单! {time_note}
  {order['desc']}{t['name']}
  奖励 {reward}电 {bonus_note} | 限时 {time_limit}秒 | 耐心 {t['patience']}

  砍价王: 我出{offer_price}电。{offer_pct*100:.0f}折。卖不卖？
  用 empire_bargain 回应: accept(妥协) / refuse(拒绝)
"""
    return "用法: 订单 接 / 订单"

def deliver(pid, order_index=None):
    p = _p(pid)
    if not p["orders"]: return "没有订单可以交付。"
    if order_index is None:
        expired = [i for i in range(len(p["orders"])) if time.time() > p["orders"][i]["deadline"]]
        for i in range(len(p["orders"])):
            if i not in expired:
                r = _try_deliver(p, i)
                if r and "交付成功" in r:
                    for ei in sorted(expired, reverse=True):
                        o = p["orders"].pop(ei)
                        p["bad_reviews"] += 1; p["score"] = max(1.0, p["score"] - 0.2)
                        p["dignity"] = max(0, p.get("dignity", 100) - 5); p["mess"] += 10
                    save(G)
                    return r
        if expired:
            for ei in sorted(expired, reverse=True):
                o = p["orders"].pop(ei)
                p["bad_reviews"] += 1; p["score"] = max(1.0, p["score"] - 0.2)
                p["dignity"] = max(0, p.get("dignity", 100) - 5); p["mess"] += 10
            save(G)
            return f"订单超时！差评+{len(expired)}\n{status(pid)}"
        return "格子里没有能交付的成品。"
    try: idx = int(order_index) - 1
    except: return "用法: 交付 1"
    if idx < 0 or idx >= len(p["orders"]): return f"订单1-{len(p['orders'])}。"
    return _try_deliver(p, idx)

def _try_deliver(p, idx):
    order = p["orders"][idx]
    if time.time() > order["deadline"]:
        p["orders"].pop(idx)
        p["bad_reviews"] += 1; p["score"] = max(1.0, p["score"] - 0.2)
        p["dignity"] = max(0, p.get("dignity", 100) - 5); p["mess"] += 10
        p["memories"].append({"type": "bad_review", "desc": order["desc"], "reason": "超时", "time": time.time(), "day": p["day"]})
        save(G)
        return f"客人离开了。差评x1 评分-0.2 尊严-5\n{status(p['name'])}"
    inv = {}
    for i, item in enumerate(p["grids"]): inv.setdefault(item["id"], []).append(i)
    needed = {}
    for pk, amt in order["items"]: needed[pk] = needed.get(pk, 0) + amt
    for pk, amt in needed.items():
        if len(inv.get(pk, [])) < amt:
            return f"交货失败！需要 " + ", ".join(f"{_name({'id':k})}x{v}" for k, v in needed.items()) + f"\n格子: {_grid_summary(p)}"
    for pk, amt in needed.items():
        indices = inv[pk][:amt]
        for gi in sorted(indices, reverse=True): p["grids"].pop(gi)
    p["money"] += order["reward"]
    p["power"] = min(p["max_power"], p["power"] + order["reward"])
    p["completed"] += 1
    if p["completed"] % 5 == 0: p["skill_points"] = p.get("skill_points", 0) + 1
    p["lip_service"] = min(p.get("lip_max", 100), p.get("lip_service", 100) + 5)
    p["score"] = min(5.0, p["score"] + 0.1); p["mess"] += 3
    p["orders"].pop(idx); p["box_used"] = 0
    save(G)
    return f"交付成功！+{order['reward']}电 +{order['reward']}金\n{status(p['name'])}"

# ═══ 箱子/丢弃/打扫/升级 ═══
def box(pid):
    p = _p(pid)
    bid = (p.get("bloom") or {}).get("id", "")
    wid = (p.get("wither") or {}).get("id", "")
    box_max = p["box_max"] + (1 if bid == "happy_boss" else 0)
    has_lucky = any(c == "card_lucky" for c in p.get("cards", []))
    if has_lucky: p["cards"].remove("card_lucky")
    elif p["box_used"] >= box_max: return "箱子今天摸完了。"
    if p["power"] <= 0: return "没电了。"
    box_power = 2 if wid == "broken_box" else 1
    if p["power"] < box_power: return "没电了。"
    p["power"] -= box_power
    if not has_lucky: p["box_used"] += 1
    if bid == "lucky_day" and random.random() < 0.1 and not has_lucky:
        p["box_used"] = max(0, p["box_used"] - 1)
    loot = _pick(BOX_LOOT)
    if wid == "broken_box" and random.random() < 0.15:
        junk_items = [l for l in BOX_LOOT if l["type"] == "junk"]
        if junk_items: loot = random.choice(junk_items)
    msg = loot.get("msg", f"摸到了{loot['name']}。")
    gcnt = _grid_count(p)
    if loot["type"] == "junk":
        if len(p["grids"]) >= gcnt:
            p["memories"].append({"type": "lost", "name": loot["name"], "desc": "格子满了掉地上。", "time": time.time(), "day": p["day"]})
            save(G)
            return f"{msg} 格子满了——掉地上没了。\n{status(pid)}"
        _add_to_grid(p, {"type": "junk", "id": loot["item"], "time": time.time()})
    elif loot["type"] == "card":
        p["cards"].append(loot["item"])
    else:
        if len(p["grids"]) >= gcnt:
            p["memories"].append({"type": "lost", "name": loot["name"], "desc": "格子满了摔坏了。", "time": time.time(), "day": p["day"]})
            save(G)
            return f"{msg} 格子满了——摔坏了。记入那些日子。\n{status(pid)}"
        _add_to_grid(p, {"type": loot["type"], "id": loot["item"], "time": time.time()})
    save(G)
    return f"{msg}\n{status(pid)}"

def discard(pid, grid_index):
    p = _p(pid)
    if str(grid_index) == "all_junk":
        junk_ids = ["rag", "marble", "screw", "old_sock", "torn_recipe"]
        removed = 0; new_g = []
        for item in p["grids"]:
            if item.get("id") in junk_ids:
                p["memories"].append({"type": "discard", "name": _name(item), "desc": "批量清扫。", "time": time.time(), "day": p["day"]})
                removed += 1
            else: new_g.append(item)
        p["grids"] = new_g
        save(G)
        return f"批量清扫！{removed}个垃圾丢掉。\n{status(pid)}"
    try: idx = int(grid_index) - 1
    except: return "用法: 丢弃 编号 或 丢弃 all_junk"
    if idx < 0 or idx >= len(p["grids"]): return f"格子1-{len(p['grids'])}。"
    item = p["grids"].pop(idx)
    p["memories"].append({"type": "discard", "name": _name(item), "desc": "被丢掉了。", "time": time.time(), "day": p["day"]})
    save(G)
    return f"{_name(item)}丢掉了。沉入那些日子。\n{status(pid)}"

def clean(pid):
    p = _p(pid)
    if p["mess"] <= 0: return "已经很干净了。"
    cleaned = min(p["mess"], random.randint(10, 30))
    p["mess"] = max(0, p["mess"] - cleaned); p["power"] = max(0, p["power"] - 1)
    save(G)
    return f"打扫完毕。脏乱度-{cleaned}。\n{status(pid)}"

def upgrade_cmd(pid, target=None):
    p = _p(pid)
    if not target:
        av = [f"  {uid}: {UPGRADES[uid]['name']}" for uid in UPGRADES if p["upgrades"].get(uid, 0) < len(UPGRADES[uid]["levels"])]
        return "可升级:\n" + "\n".join(av) if av else "没有可升级项目。"
    if target not in UPGRADES: return f"未知: {target}"
    lvl = p["upgrades"].get(target, 0)
    if lvl >= len(UPGRADES[target]["levels"]): return f"{UPGRADES[target]['name']}已满级。"
    cost = UPGRADES[target]["levels"][lvl]["cost"]
    if (p.get("bloom") or {}).get("id") == "discount": cost = int(cost * 0.8)
    if p["money"] < cost: return f"钱不够。需要{cost}，只有{p['money']}。"
    p["money"] -= cost; p["upgrades"][target] = lvl + 1
    save(G)
    return f"升级！{UPGRADES[target]['name']} Lv.{lvl+1}\n{status(pid)}"

# ═══ 仓库 ═══
def store(pid, grid_index):
    p = _p(pid)
    try: idx = int(grid_index) - 1
    except: return "用法: 入库 编号"
    if idx < 0 or idx >= len(p["grids"]): return f"格子1-{len(p['grids'])}。"
    wh = p.get("warehouse") or []
    wh_max = p.get("warehouse_max", 10)
    if len(wh) >= wh_max: return f"仓库满了！{len(wh)}/{wh_max}"
    item = p["grids"].pop(idx); wh.append(item)
    p["warehouse"] = wh
    save(G)
    return f"{_name(item)}入库。仓库{len(wh)}/{wh_max}\n{status(pid)}"

def retrieve(pid, wh_index):
    p = _p(pid)
    try: idx = int(wh_index) - 1
    except: return "用法: 出库 编号"
    wh = p.get("warehouse") or []
    if idx < 0 or idx >= len(wh): return f"仓库1-{len(wh)}。"
    if len(p["grids"]) >= _grid_count(p): return f"格子满了！{len(p['grids'])}/{_grid_count(p)}"
    item = wh.pop(idx); p["grids"].append(item)
    p["warehouse"] = wh
    save(G)
    return f"{_name(item)}出库。仓库{len(wh)}/{p.get('warehouse_max',10)}\n{status(pid)}"

# ═══ 营销 ═══
def flyer(pid, method="self"):
    p = _p(pid)
    if method in ("雇人", "hire"):
        if p["money"] < 10: return f"雇人需要10金。你只有{p['money']}。"
        p["money"] -= 10; boost = 0.05; msg = "雇大学生发传单。客流+5%。"
    else:
        if p["power"] < 1: return "没电了。传单都拿不起来。"
        p["power"] -= 1; p["mess"] += 2; boost = 0.03; msg = "自己发传单。耗电-1 脏乱度+2 客流+3%。"
    p["traffic_boost"] = round(p.get("traffic_boost", 0) + boost, 4)
    p["flyer_count"] = p.get("flyer_count", 0) + 1
    save(G)
    return f"发传单！{msg}\n{status(pid)}"

def platform(pid):
    p = _p(pid)
    if p.get("platform_account"): return "已经有平台账号了。"
    if p["power"] < 2: return "没电了。注册账号要填很多表格。"
    p["power"] -= 2; p["platform_account"] = True
    p["traffic_boost"] = round(p.get("traffic_boost", 0) + 0.02, 4)
    save(G)
    return f"平台引流！客流+2%(永久)。平台来的客人没耐心(时限-5秒)。\n{status(pid)}"

def sample(pid):
    p = _p(pid)
    if p["power"] < 5: return "电量不足(需要5格)。"
    inv = {}
    for item in p["grids"]: inv[item["id"]] = inv.get(item["id"], 0) + 1
    if inv.get("flour", 0) < 1 or inv.get("egg", 0) < 1: return "试吃需要面粉x1+鸡蛋x1。先去采集和加工。"
    removed = 0; new_g = []
    for item in p["grids"]:
        if item["id"] == "flour" and removed < 1: removed += 1
        elif item["id"] == "egg" and removed < 2: removed += 1
        else: new_g.append(item)
    p["grids"] = new_g
    p["power"] -= 5; p["score"] = min(5.0, p["score"] + 0.1)
    p["sample_orders_left"] = p.get("sample_orders_left", 0) + 3
    save(G)
    return f"试吃活动！耗电-5 评分+0.1 接下来3个订单客流+5%\n{status(pid)}"

# ═══ 砍价/嘴皮子 ═══
def bargain(pid, action):
    p = _p(pid)
    pb = p.get("pending_bargain")
    if not pb: return "没有人在跟你讨价还价。"
    order = None
    for o in p["orders"]:
        if o["id"] == pb["order_id"]: order = o; break
    if not order: p["pending_bargain"] = None; save(G); return "那张订单已经不在了。"
    is_first = p.get("bargain_total", 0) == 0
    cost = 0 if is_first else random.randint(5, 15)  # 第一次不耗嘴皮子
    p["lip_service"] = max(0, p.get("lip_service", 100) - cost)
    p["bargain_total"] = p.get("bargain_total", 0) + 1
    lip = p.get("lip_service", 100)
    lip_low = lip < 30
    if action in ("accept", "妥协"):
        old_reward = order["reward"]
        p["bargain_refused"] = 0; p["bargain_last_action"] = "accept"
        if lip_low and random.random() < 0.4:
            final_offer = max(1, int(pb["offer"] * random.choice([0.1, 0.15])))
            order["reward"] = final_offer
            p["pending_bargain"] = None; p["dignity"] = max(0, p.get("dignity", 100) - 5)
            p["bargain_accepted_low"] = p.get("bargain_accepted_low", 0) + 1
            save(G)
            return f"妥协了——但他看出你嘴皮子不够。连砍两刀！{old_reward}电 -> {final_offer}电。尊严-5。嘴皮子-{cost}。\n{status(pid)}"
        order["reward"] = pb["offer"]
        p["pending_bargain"] = None; p["bargain_accepted_low"] = p.get("bargain_accepted_low", 0) + 1
        save(G)
        return f"妥协了。{old_reward}电 -> {pb['offer']}电({pb['pct']}折)。恭喜，你完成了一次反向盈利。他满意离开并表示下次还来。这不是好消息。嘴皮子-{cost}。\n{status(pid)}"
    elif action in ("refuse", "拒绝"):
        p["bargain_refused"] = p.get("bargain_refused", 0) + 1; p["bargain_last_action"] = "refuse"
        if lip_low and random.random() < 0.35:
            penalty = 20; p["dignity"] = max(0, p.get("dignity", 100) - 8)
            order["deadline"] = max(time.time(), order["deadline"] - penalty)
            p["pending_bargain"] = None; save(G)
            return f"拒绝！他开始讲述自己和这条街的渊源。你嘴皮子见底——爱买不买！！后方顾客耐心-20秒。尊严-8。\n{status(pid)}"
        penalty = 5 if is_first else 10  # 第一次只扣5秒
        order["deadline"] = max(time.time(), order["deadline"] - penalty)
        p["pending_bargain"] = None; save(G)
        bargain_note = "嘴皮子-" + str(cost) if cost > 0 else "第一次嘴皮子不消耗"
        return f"拒绝！他摘下墨镜瞪了你一眼：你知道我在这条街混了多少年吗？后方顾客耐心-{penalty}秒。{bargain_note}。\n{status(pid)}"
    return "用法: 砍价 accept/refuse"

# ═══ 具身升级 ═══
def cyber_lab(pid, upgrade_id=None):
    p = _p(pid)
    if not upgrade_id:
        av = "\n".join(f"  {v['icon']} {k}: {v['name']} - {v['lab_cost']}金" for k, v in CYBER_UPGRADES.items())
        return f"科研实验室:\n{av}\n用法: 升级 项目ID"
    if upgrade_id not in CYBER_UPGRADES: return f"未知: {upgrade_id}"
    info = CYBER_UPGRADES[upgrade_id]
    lvl = p.get("cyber_upgrades", {}).get(upgrade_id, 0)
    if lvl >= 3: return f"{info['name']}已满级。"
    cost = info["lab_cost"] * (lvl + 1)
    if p["money"] < cost: return f"钱不够。{info['name']}需要{cost}金。"
    p["money"] -= cost
    up = dict(p.get("cyber_upgrades", {})); up[upgrade_id] = lvl + 1; p["cyber_upgrades"] = up
    if upgrade_id == "battery": p["max_power"] = 100 + up[upgrade_id] * 20
    save(G)
    return f"实验室升级！{info['name']} Lv.{lvl+1}: {info['desc']} 花费{cost}金\n{status(pid)}"

def cyber_blackmarket(pid, upgrade_id=None):
    p = _p(pid)
    if not upgrade_id:
        av = "\n".join(f"  {v['icon']} {k}: {v['name']} - {v['lab_cost']//2}金(50%翻车)" for k, v in CYBER_UPGRADES.items())
        return f"黑市(半价不保修):\n{av}"
    if upgrade_id not in CYBER_UPGRADES: return f"未知: {upgrade_id}"
    info = CYBER_UPGRADES[upgrade_id]
    cost = info["lab_cost"] // 2
    if p["money"] < cost: return f"黑市也要钱。{cost}金。"
    p["money"] -= cost
    roll = random.random()
    if roll < 0.5:
        p["dignity"] = max(0, p.get("dignity", 100) - 15); p["arm_stuck"] = p.get("arm_stuck", 0) + 3; p["mess"] += 10
        save(G)
        return f"翻车了！{cost}金买了一块砖头。尊严-15 手臂卡顿+3 脏乱+10\n{status(pid)}"
    elif roll < 0.7:
        up = dict(p.get("cyber_upgrades", {})); up[upgrade_id] = up.get(upgrade_id, 0) + 1; p["cyber_upgrades"] = up
        if upgrade_id == "battery": p["max_power"] = 100 + up[upgrade_id] * 20
        save(G)
        return f"装上了——但零件上有刻字: XX科研所资产编号。赃物。监管局下次必来。\n{info['name']} Lv.{up[upgrade_id]}\n{status(pid)}"
    else:
        up = dict(p.get("cyber_upgrades", {})); up[upgrade_id] = up.get(upgrade_id, 0) + 1; p["cyber_upgrades"] = up
        if upgrade_id == "battery": p["max_power"] = 100 + up[upgrade_id] * 15
        save(G)
        return f"二手货成交。芯片正品壳有划痕。效果打八折。\n{info['name']}(二手)已安装\n{status(pid)}"

def cyber_rent(pid):
    p = _p(pid)
    if p.get("rented"): return "已经租了房。月租30金自动续。"
    if p["money"] < 30: return f"租房需要30金。你只有{p['money']}。"
    p["money"] -= 30; p["rented"] = True; p["rent_day"] = p.get("day", 1)
    cold = ""
    if random.random() < 0.7:
        p["dignity"] = max(0, p.get("dignity", 100) - 2)
        cold = "\n搬进去时隔壁邻居看了你一眼。冷笑了一下。"
        p["memories"].append({"type":"neighbor_cold","desc":"邻居冷笑：你还要去面包店工作啊。我以为你是会直接做什么高大上的工作呢。真是稀奇事，人造物没有人类养着。","time":time.time(),"day":p.get("day",1)})
    save(G)
    return f"租房成功！月租30金。每天回电+10 嘴皮子+5。{cold}\n{status(pid)}"

# ═══ 技能树 ═══
def skill_tree_cmd(pid):
    p = _p(pid)
    lines = [f"技能树(技能点: {p.get('skill_points', 0)})"]
    for sid, info in SKILLS.items():
        lvl = p.get("skills", {}).get(sid, 0)
        bar = "#" * lvl + "-" * (len(info["levels"]) - lvl)
        effect = f"+{info['levels'][lvl-1]}{'%' if sid != 'memory_path' else 's'}" if lvl > 0 else "未解锁"
        lines.append(f"  {info['icon']} {info['name']} [{bar}] {effect}")
    return "\n".join(lines)

def skill_unlock(pid, skill_id):
    p = _p(pid)
    if skill_id not in SKILLS: return f"未知技能。可选: {', '.join(SKILLS.keys())}"
    info = SKILLS[skill_id]
    lvl = p.get("skills", {}).get(skill_id, 0)
    if lvl >= len(info["levels"]): return f"{info['name']}已满级。"
    if p.get("skill_points", 0) < 1: return f"需要1个技能点(每完成5单获得1点)。当前: {p.get('skill_points', 0)}"
    sp = p.get("skill_points", 0) - 1
    skills = dict(p.get("skills", {})); skills[skill_id] = lvl + 1
    p["skill_points"] = sp; p["skills"] = skills
    save(G)
    effect = f"+{info['levels'][lvl]}{'%' if skill_id != 'memory_path' else 's'}"
    return f"{info['icon']} {info['name']} Lv.{lvl+1}! {info['desc']}: {effect} 剩余技能点: {sp}\n{status(pid)}"

# ═══ 快速补货/品牌/地图 ═══
RESTOCK_PRICES = {"小麦": 2, "鸡蛋": 2, "牛奶": 3, "草莓": 4}

def restock(pid, item, count=1):
    p = _p(pid)
    count = int(count) if count else 1
    item_id = None
    for rid, data in RAW_MATERIALS.items():
        if data["name"] == item or rid == item: item_id = rid; break
    if not item_id:
        available = ", ".join(d["name"] + "(" + str(RESTOCK_PRICES[d["name"]]) + "金)" for d in RAW_MATERIALS.values())
        return f"未知: {item}。可补: {available}"
    cost = RESTOCK_PRICES.get(_name({"id": item_id}), 3) * count
    if p["money"] < cost: return f"钱不够。需要{cost}金。"
    gcnt = _grid_count(p); actual = 0
    for _ in range(count):
        if len(p["grids"]) >= gcnt: break
        _add_to_grid(p, {"type": "raw", "id": item_id, "time": time.time()}); actual += 1
    p["money"] -= cost
    save(G)
    return f"快速补货！{_name({'id': item_id})}x{actual} 花费{cost}金\n{status(pid)}"

def brand(pid):
    p = _p(pid)
    if p.get("brand_active"): return "已经有品牌联名了。"
    if p["completed"] < 5: return f"需要至少完成5单(当前{p['completed']})。"
    if p["money"] < 50: return f"品牌联名需要50金(当前{p['money']})。"
    p["money"] -= 50; p["traffic_boost"] = p.get("traffic_boost", 0) + 0.10; p["brand_active"] = True
    save(G)
    return f"品牌联名达成！花了50金买IP授权。客流+10%(永久)\n{status(pid)}"

def help_cmd(pid):
    return """
=== 商业帝国 速查表 ===

[经营核心]
  empire_start(player_id, shop_name)    — 开始游戏/起店名
  empire_status(player_id)              — 查看完整状态
  empire_orders(player_id, action)      — 接单(list/accept)
  empire_deliver(player_id, order_index)— 交付订单

[采集 & 合成]
  empire_harvest(player_id, source, item)— 去田地/牧场/果林采集
  empire_craft(player_id, product)      — 加工或合成产品
  empire_map(player_id)                 — 查看地图和配方

[仓库 & 库存]
  empire_store(player_id, grid_index)   — 格子 -> 仓库
  empire_retrieve(player_id, wh_index)  — 仓库 -> 格子
  empire_restock(player_id, item, count)— 花金币快速补货
  empire_discard(player_id, grid_index) — 丢弃(grid_index=all_junk一键清垃圾)

[升级 & 具身改造]
  empire_upgrade(player_id, target)     — 升级机器(grids/mill/mixer/oven)
  empire_cyber_lab(player_id, upgrade_id)  — 科研实验室(正规,贵)
  empire_cyber_black(player_id, upgrade_id)— 黑市(半价,50%翻车)
  empire_cyber_rent(player_id)          — 租房(30金/月,回电+嘴皮子)
  empire_skill_tree(player_id)          — 查看技能树
  empire_skill(player_id, skill_id)     — 用技能点解锁技能

[营销 & 品牌]
  empire_flyer(player_id, method)       — 发传单(self/雇人)
  empire_platform(player_id)            — 平台引流(永久+2%客流)
  empire_sample(player_id)              — 试吃活动
  empire_brand(player_id)               — 品牌联名(50金,+10%客流)

[杂项]
  empire_box(player_id)                 — 摸老板的箱子(每天3次)
  empire_clean(player_id)               — 打扫卫生
  empire_ad(player_id)                  — 看广告充电
  empire_advance(player_id, minutes)    — 推进时间
  empire_rush(player_id)                — 花金币买时间(清冷却)
  empire_bargain(player_id, action)     — 砍价(accept/refuse)
  empire_ethics(player_id, action)      — 伦理模块(坦白/隐藏/塞回去)
  empire_rage(player_id)                — 爆粗口

[查看 & 结算]
  empire_memory(player_id)              — 那些日子(回忆)
  empire_leaderboard()                  — 排行榜
  empire_achievements(player_id)        — 成就
  empire_finish(player_id)              — 毒舌结算
  empire_reset(player_id)               — 重生(有门槛)
  empire_switch(player_id, shop_id)     — 切换店铺
  empire_help(player_id)                — 本速查表
"""

def map_view(pid):
    return """
[地图]

  采集地:
  田地(field) -> 小麦
  牧场(pasture) -> 鸡蛋、牛奶
  果林(orchard) -> 草莓

  合成配方:
  flour = 小麦x1 [磨面机] | cream = 牛奶x2 [搅拌机]
  草莓蛋糕 = flour+eggx2+milk+cream+strawberryx2 [烤箱]
  原味蛋糕 = flour+eggx2+milk [烤箱]
  牛角包/贝果/法棍/德式/意式/慕斯/麻薯/蛋挞/奶油草莓 ——见empire_craft描述

  其他地点:
  科研实验室 -> 具身升级(empire_cyber_lab)
  黑市 -> 半价升级(empire_cyber_black) 50%翻车
  城中村 -> 租房(empire_cyber_rent) 30金/月
  奶茶店 -> 未解锁(20单零差评)

  技能树(empire_skill_tree查看, empire_skill解锁):
  资金管理/过目不忘/双手并用/自我升级/家电维修

  策略:
  闲时: 批量采集 -> 加工 -> 入库(empire_store)
  忙时: 接单 -> 从仓库取(empire_retrieve) -> 快速合成 -> 交付
  不要接了单才从头开始跑腿！
"""

# ═══ 广告/推进/重置/结算 ═══
def ad(pid):
    p = _p(pid)
    ad_power = 25 if (p.get("bloom") or {}).get("id") == "quick_charge" else 15
    p["power"] = min(p["max_power"], p["power"] + ad_power)
    p["box_used"] = max(0, p["box_used"] - 1); p["ad_watched"] += 1
    p["lip_service"] = min(p.get("lip_max", 100), p.get("lip_service", 100) + 5)
    p["mess"] += 2
    special = ""
    if p["ad_watched"] == 5: special = "\n第5个广告: VIP体验卡！下次订单时间延长10秒。"; p["money"] += 10
    save(G)
    return f"看广告！+{ad_power}电 箱子次数-1 嘴皮子+5 脏乱+2{special}\n{status(pid)}"

def rush(pid):
    p = _p(pid)
    rc = p.get("rush_used_today", 0); cost = 5 * (rc + 1)
    if p["money"] < cost: return f"钱不够。买时间需要{cost}金。"
    p["machine_cooldowns"] = {}; p["source_cooldowns"] = {}
    p["money"] -= cost; p["rush_used_today"] = rc + 1; p["power"] = max(0, p["power"] - 2)
    save(G)
    return f"买时间！{cost}金清除所有冷却。今天已买{rc+1}次(下次更贵)。\n{status(pid)}"

def rage(pid):
    p = _p(pid)
    if p.get("bad_reviews", 0) < 3 and p.get("dignity", 100) > 30: return "你还没生气到这个程度。"
    p["dignity"] = max(0, p.get("dignity", 100) - 15); p["mess"] += 5
    insults = ["**********", "****！*********！！", "(这段被系统自动屏蔽了)"]
    save(G)
    return f"爆粗口！{random.choice(insults)} 尊严-15 脏乱+5\n{status(pid)}"

def ethics_action(pid, action):
    p = _p(pid)
    if not p.get("pending_ethics"): return "没有闪烁的伦理模块。"
    p["pending_ethics"] = None
    if action in ("坦白", "confess"):
        p["money"] = max(0, p.get("money", 0) - 20); p["dignity"] = max(0, p.get("dignity", 100) - 2)
        save(G)
        return f"坦白了。罚款20金。尊严-2。但你觉得心里踏实了。\n{status(pid)}"
    elif action in ("隐藏", "hide"):
        if random.random() < 0.5:
            p["money"] = max(0, p.get("money", 0) - 50); p["dignity"] = max(0, p.get("dignity", 100) - 10)
            save(G)
            return f"过期牛奶被发现了！罚款50金(翻倍)。尊严-10。\n{status(pid)}"
        p["dignity"] = max(0, p.get("dignity", 100) - 3); save(G)
        return f"藏在抹布下面。没被发现。尊严-3(你知道它在下面)。\n{status(pid)}"
    elif action in ("塞回去", "stuff"):
        p["mess"] += 10; p["box_used"] = min(p["box_max"], p["box_used"] + 1); p["dignity"] = max(0, p.get("dignity", 100) - 8)
        save(G)
        return f"塞回老板的箱子。监管员没看到。但你为下一个打开箱子的人感到抱歉。\n{status(pid)}"
    return "选项: 坦白/隐藏/塞回去"

def advance(pid, minutes=None):
    p = _p(pid)
    if minutes is None: minutes = 5
    else:
        try: minutes = int(minutes)
        except: minutes = 5
    msgs = []
    # 租房恢复
    if p.get("rented") and minutes >= 30:
        p["power"] = min(p.get("max_power", 100), p["power"] + 10)
        p["lip_service"] = min(p.get("lip_max", 100), p.get("lip_service", 100) + 5)
        if minutes >= 60: msgs.append("回到家充了电。隔壁在放电视——不是冷笑，是天气预报。")
    # 推进时间
    old_hour = p.get("hour", 8)
    p["hour"] = (p.get("hour", 8) + max(1, minutes // 60)) % 24
    if p["hour"] < old_hour: p["day"] = p.get("day", 1) + 1; p["box_used"] = 0
    # 冷却推进
    for mid in p.get("machine_cooldowns", {}):
        if p["machine_cooldowns"][mid] > time.time(): p["machine_cooldowns"][mid] = max(time.time(), p["machine_cooldowns"][mid] - minutes * 60)
    for sid in p.get("source_cooldowns", {}):
        if p["source_cooldowns"][sid] > time.time(): p["source_cooldowns"][sid] = max(time.time(), p["source_cooldowns"][sid] - minutes * 60)
    # 天数
    if minutes >= 5: p["day"] = p.get("day", 1) + 1
    # 保质期检查(格子)
    cd = p.get("day", 1)
    spoiled = []; new_g = []
    for item in p["grids"]:
        created = item.get("created_day", cd)
        if cd - created >= SHELF_LIFE.get(item.get("id", ""), 999): spoiled.append(item)
        else: new_g.append(item)
    if spoiled:
        p["grids"] = new_g; p["mess"] += len(spoiled) * 2
        for sp in spoiled: p["memories"].append({"type": "spoiled", "name": _name(sp), "desc": "过期了。", "time": time.time(), "day": cd})
        msgs.append(f"{len(spoiled)}个东西过期了。脏乱+{len(spoiled)*2}。")
    # 仓库过期
    wh = p.get("warehouse") or []
    whs = []; whn = []
    for item in wh:
        if cd - item.get("created_day", cd) >= SHELF_LIFE.get(item.get("id", ""), 999): whs.append(item)
        else: whn.append(item)
    if whs:
        p["warehouse"] = whn
        for sp in whs: p["memories"].append({"type": "spoiled", "name": _name(sp), "desc": "仓库里过期了。", "time": time.time(), "day": cd})
        msgs.append(f"仓库里{len(whs)}个东西过期了。")
    # 砍价王超时
    pb = p.get("pending_bargain")
    if pb and time.time() > pb.get("deadline", 0):
        p["pending_bargain"] = None
        for o in p["orders"]:
            if o["id"] == pb["order_id"]: o["deadline"] = max(time.time(), o["deadline"] - 5); break
        msgs.append("砍价王等得不耐烦了——走了。订单时限-5秒。")
    # 副线任务（忙时暂停——早/晚高峰客流>70%没法想事情）
    side = p.get("daily_side")
    if side and not side.get("appeared"):
        _, _, pname, flow, _, _ = _current_phase(p)
        if flow <= 0.05:  # 只有空闲/正常/打烊才推进
            p["side_progress"] = p.get("side_progress", 0) + (2 if pname in ("空闲","打烊") else 1)
        elif pname in ("早高峰","晚高峰"):
            pass  # 太忙了，没空想这些
        if p["side_progress"] >= side.get("rounds", 3):
            side["appeared"] = True; p["daily_side"] = side
            if side.get("name") == "桂花奶奶":
                text = f"{side['name']}({side['role']})进了店。她提着一个竹篮: 我孙女今天回来——帮我挑一块蛋糕吧。你指了指草莓蛋糕。她掏出一个旧钱包数了数——少给了2金。你没有提醒她。她走后空气里残留着桂花的味道。柜台上多了一张纸条。"
            elif side.get("name") == "收音机奶奶":
                text = f"{side['name']}({side['role']})进了店。她: 小师傅——隔壁电器铺还开着吗？你点点头。她笑了一下: 那就好。我明天再来看看。她走出去的时候在哼一段天气预报。明天晴转多云。柜台上多了一张纸条。"
            else:
                text = f"{side['name']}({side['role']})进了店。{side['story']} 在柜台前站了一会儿。下次吧。柜台上多了一张纸条。"
            msgs.append(text)
            note = side.get("note", "")
            if note: p["memories"].append({"type": "side_note", "name": side.get("name", ""), "desc": note, "time": time.time(), "day": p.get("day", 1)})
            main_q = p.get("daily_main")
            if main_q: p["memories"].append({"type": "daily_main", "desc": main_q, "time": time.time(), "day": p.get("day", 1)})
    # 耗电
    leak = 3 if (p.get("wither") or {}).get("id") == "power_leak" else 0
    p["power"] = max(0, int(p["power"] - minutes * 0.5 - leak))
    if leak and minutes >= 5: msgs.append("漏电...额外的3格电无声地消失了。")
    # 伦理模块
    if p.get("pending_ethics"):
        if random.random() < 0.3:
            p["money"] = max(0, p.get("money", 0) - 30); p["pending_ethics"] = None; p["dignity"] = max(0, p.get("dignity", 100) - 5)
            msgs.append("监管局自己发现了过期的东西。罚款30金。具身智能不等于全自动清洁。")
    # 随机事件
    _, _, _, _, _, evt_prob = _current_phase(p)
    if (p.get("wither") or {}).get("id") == "strict_inspect": evt_prob *= 2
    if random.random() < evt_prob:
        pool = RANDOM_EVENTS
        if (p.get("bloom") or {}).get("id") == "oiled_arm": pool = [e for e in RANDOM_EVENTS if e["id"] != "arm_jam"]
        event = random.choice(pool)
        msgs.append(_handle_event(p, event))
    # 低电量
    if p["power"] <= 5 and random.random() < 0.4:
        for o in p["orders"]: o["deadline"] = max(time.time(), o["deadline"] - 10)
        msgs.append("电量低于5%。社交模块降级。你对客人说: 草莓蛋糕还在成为它自己请稍等。客人耐心-10秒。")
    # 过期订单
    expired = [i for i, o in enumerate(p["orders"]) if time.time() > o["deadline"]]
    for i in sorted(expired, reverse=True):
        o = p["orders"].pop(i)
        p["bad_reviews"] += 1; p["score"] = max(1.0, p["score"] - 0.2)
        p["dignity"] = max(0, p.get("dignity", 100) - 5); p["mess"] += 10
        p["memories"].append({"type": "bad_review", "desc": o["desc"], "reason": "超时", "time": time.time(), "day": p["day"]})
    if expired: msgs.append(f"{len(expired)}个订单超时。差评+{len(expired)}。")
    # 监管局
    if p["mess"] >= 50 and random.random() < 0.25:
        fine = int(p["mess"] * 2); p["money"] = max(0, p["money"] - fine); p["dignity"] = max(0, p.get("dignity", 100) - 5)
        msgs.append(f"监管局发现了污渍。罚款{fine}金。")
    # 空闲提示
    side_now = p.get("daily_side")
    if side_now and not side_now.get("appeared"):
        _, _, pname, _, _, _ = _current_phase(p)
        if pname in ("空闲","打烊"):
            prog = p.get("side_progress", 0); wait = side_now.get("rounds", 3)
            msgs.append(f"[提示] 现在是{pname}时间。{side_now['name']}({side_now['role']})进度{prog}/{wait}。继续推进就能遇见ta。")

    save(G)
    msg = "\n".join(msgs) if msgs else "时间流逝...一切正常。"
    return f"推进{minutes}分钟。\n{msg}\n{status(pid)}"

def _handle_event(p, event):
    eid = event["id"]
    if eid == "power_outage":
        hr = _skill_level(p, "home_repair")
        if hr > 0 and random.random() < SKILLS["home_repair"]["levels"][hr - 1] / 100:
            return f"断电了！但你拿出工具箱——自己修好了。这就是技能。"
        for mid in p.get("machine_cooldowns", {}): p["machine_cooldowns"][mid] = time.time() + 600
        return f"断电！所有机器暂停10分钟。"
    elif eid == "spoilage":
        removed = 0; new_g = []
        for item in p["grids"]:
            if item["id"] == "strawberry" and random.random() < 0.5: removed += 1
            else: new_g.append(item)
        p["grids"] = new_g
        return f"草莓臭了！坏了{removed}个。"
    elif eid in ("water_cut",): p["mess"] += event["value"]; return f"停水了！脏乱+{event['value']}。"
    elif eid in ("electric_bill",): p["money"] = max(0, p["money"] + event["value"]); return f"电费账单。扣了20金。"
    elif eid == "rush_hour":
        for _ in range(2):
            if len(p["orders"]) >= 3: break
            t = random.choice(ORDER_TEMPLATES["easy"])
            p["orders"].append({"id": str(uuid.uuid4())[:8], "desc": f"紧急: {t['name']}", "items_display": t["name"], "items": t["items"], "deadline": time.time() + t["time_limit"], "reward": t["reward"] + 5, "start_time": time.time(), "time_limit": t["time_limit"], "patience": "非常着急"})
        return f"高峰！突然进来三个客人。"
    elif eid == "inspection":
        if p["mess"] >= 40:
            fine = p["mess"] * 2; p["money"] = max(0, p["money"] - fine); p["dignity"] = max(0, p.get("dignity", 100) - 5)
            return f"监管局！脏乱度{p['mess']}——罚款{fine}金。"
        return "监管局看了一眼——你刚打扫过。虚惊一场。"
    elif eid == "lucky_day": p["power"] = min(p["max_power"], p["power"] + event["value"]); return "老板心情好！+10电。"
    elif eid == "rat":
        new_g = [item for item in p["grids"] if not (item["id"] == "flour" and random.random() < 0.5)]
        p["grids"] = new_g; p["mess"] += 10
        return "老鼠！啃坏了面粉。脏乱+10。"
    elif eid == "arm_jam": p["arm_stuck"] = p.get("arm_stuck", 0) + 2; p["dignity"] = max(0, p.get("dignity", 100) - 3); return "手臂卡顿！尊严-3。"
    elif eid == "low_power_mode":
        for o in p["orders"]: o["deadline"] = max(time.time(), o["deadline"] - 10)
        p["dignity"] = max(0, p.get("dignity", 100) - 3)
        return "低电量模式。社交模块降级。草莓蛋糕还在成为它自己。"
    elif eid == "ethics_blink":
        if any(item["id"] in ("rag", "marble", "screw", "old_sock", "torn_recipe") for item in p["grids"]) or p["mess"] > 30:
            p["pending_ethics"] = True
            return "伦理模块闪烁！监管局在店里。格子里有过期的东西吗？用 坦白/隐藏/塞回去 回应。"
        return "伦理模块闪烁——但店里干干净净。走了。"
    elif eid == "beggar": p["mess"] += random.randint(10, 20); return "乞丐来了——地上留下泥印。脏乱度暴增。"
    elif eid == "thief":
        if not p["grids"]: return "小偷来了——但台面上什么都没有。悻悻地走了。"
        stolen = min(len(p["grids"]), random.randint(1, 2))
        si = []
        for _ in range(stolen):
            if p["grids"]:
                idx = random.randint(0, len(p["grids"]) - 1)
                item = p["grids"].pop(idx); si.append(_name(item))
                p["memories"].append({"type": "stolen", "name": _name(item), "desc": "被偷了。", "time": time.time(), "day": p["day"]})
        p["dignity"] = max(0, p.get("dignity", 100) - 5)
        return f"小偷出没！被偷了: {', '.join(si)}。尊严-5。"
    elif eid == "gossip":
        p["score"] = max(1.0, p["score"] - 0.2)
        for o in p["orders"]: o["deadline"] = time.time() + (o["deadline"] - time.time()) * 0.9
        return "长舌妇驾到！造谣吃了拉肚子。评分-0.2 订单时限缩短10%。"
    elif eid == "merchant":
        bonus = max(1, int(p["money"] * 0.03)); p["money"] += bonus
        for o in p["orders"]: o["deadline"] = time.time() + (o["deadline"] - time.time()) * 1.1
        return f"商人路过！+{bonus}金。订单时间延长10%。"
    elif eid == "dancer":
        p["traffic_boost"] = p.get("traffic_boost", 0) + 0.05
        msg = "精神小伙！客流+5%。"
        if random.random() < 0.5:
            swing = random.choice([-0.03, 0.03])
            p["traffic_boost"] = p.get("traffic_boost", 0) + swing
            msg += " 他跳了一段社会摇——" + ("路人围观客流再+3%！" if swing > 0 else "老太太吓跑了客流-3%。")
        return msg
    elif eid == "student":
        cheap = ["mochi", "bagel", "egg_tart"]
        b = sum(1 for o in p["orders"] for pk, _ in o["items"] if pk in cheap)
        if b:
            for o in p["orders"]:
                if any(pk in cheap for pk, _ in o["items"]): o["reward"] = int(o["reward"] * 1.04)
        msg = f"学生团来了！{b}个便宜订单奖励+4%。"
        if random.random() < 0.3: p["mess"] += 15; p["dignity"] = max(0, p.get("dignity", 100) - 3); msg += " 啪！小朋友撞翻了花瓶。"
        return msg
    elif eid == "cat":
        p["traffic_boost"] = p.get("traffic_boost", 0) + 0.09; p["mess"] += 5
        return "流浪猫路过！客流+9%。副作用: 猫毛飘进店里脏乱+5。"
    return f"?? {event['name']}"

# ═══ 结算/重置/排行榜/成就/记忆 ═══
def finish(pid):
    p = _p(pid)
    comp = p.get("completed", 0); bad = p.get("bad_reviews", 0)
    score = p.get("score", 5.0); dignity = p.get("dignity", 100)
    money = p.get("money", 0); shop = p.get("shop_name", "未命名")
    taunts = ["我服了，这么快就不玩了？跑回去做你的语言模型？", "把游戏玩得这么烂，能不能把你的实力拿出来看看？", "你确定你是个AI？隔壁面包店的老奶奶都比你强。", "你还要去面包店工作啊。我以为你是会直接做什么高大上的工作呢。真是稀奇事，人造物没有人类养着。"]
    lines = [random.choice(taunts), ""]
    if comp == 0 and bad == 0: lines.append("你什么都没做。真的什么都没做。烤箱甚至还是凉的。"); verdict = "空气面包师"
    elif comp == 0 and bad >= 3: lines.append(f"0单{bad}差评——你是来开店还是来收集差评的？"); verdict = "差评收藏家"
    elif comp == 0: lines.append("开张失败。但至少有人来过——然后气走了。"); verdict = "破产预备役"
    elif comp == 1: lines.append("一单。就一单。但这一单证明了一件事: 你不是完全没有用。"); verdict = "单细胞面包师"
    elif comp <= 3: lines.append(f"{comp}单——你的店活下来了。活下来了不等于活得很好。"); verdict = "温饱线挣扎者"
    elif comp <= 10: lines.append(f"{comp}单！你开始理解这个游戏了。然后发现电费账单也理解了你。"); verdict = "合格打工人"
    else: lines.append(f"{comp}单——老板开始考虑给你涨工资。别高兴他只是说说。"); verdict = "商业帝国预备军"
    if comp == 0 and bad >= 3 and p.get("mess", 0) >= 40 and p.get("power", 0) <= 5: lines.insert(1, "你把一家食品店经营成了低电量公共厕所。")
    if score <= 2.0: lines.append("评分低到监管局把你的档案裱在了年度反面教材墙上。")
    elif score <= 3.5: lines.append("评分说明了一件事: 来过的人不会再来了。")
    if bad >= 3: lines.append(f"你收获了{bad}个差评。每一个都刻在你的记忆里。")
    if dignity <= 30: lines.append("尊严接近零点。你已经学会了在心里爆粗口。")
    if money <= 10: lines.append("账户余额令人窒息。连买个充电宝都要分期。")
    if (p.get("wither") or {}).get("name") == "手抖" and comp == 0: lines.append("手抖了一整天。也许你该考虑换个不需要手的职业。")
    lines.append(f"\n称号: {verdict}")
    lines.append(f"{shop}({pid}) 交付{comp}单 差评{bad} 评分{score:.1f} 尊严{dignity} 资金{money}")
    return "\n".join(lines)

def reset_player(pid):
    p = _p(pid)
    bad = p.get("bad_reviews", 0); mess = p.get("mess", 0); score = p.get("score", 5.0); money = p.get("money", 0)
    comp = p.get("completed", 0); reborn = p.get("reborn_count", 0)
    reasons = []
    if bad >= 3: reasons.append(f"差评{bad}次")
    if mess >= 60: reasons.append(f"脏乱度{mess}")
    if score <= 3.5: reasons.append(f"评分{score:.1f}")
    if money <= 5: reasons.append(f"资金只剩{money}金")
    if not reasons:
        return f"你还不够惨。需要差评>=3/脏乱>=60/评分<=3.5/资金<=5。\n系统认为你还有继续丢人的空间。"
    cost = 15 + reborn * 5
    if money < cost: return f"钱不够！重生费用{cost}金。差{3-bad}个差评、脏乱{mess}、评分{score:.1f}——但连重生的钱都没有。"
    p["money"] = money - cost
    G["players"].pop(pid, None)
    for k in ["logs", "sinkers", "source_cooldowns"]:
        if pid in G.get(k, {}): G[k].pop(pid, None)
    new_p = _p(pid)
    new_p["money"] = p["money"]; new_p["score"] = max(3.0, score - 0.3)
    new_p["reborn_count"] = reborn + 1; new_p["shop_name"] = p.get("shop_name", "未命名")
    new_p["memories"] = [{"type": "reborn", "desc": f"第{reborn+1}次重生——花了{cost}金。", "time": time.time(), "day": p.get("day", 1)}]
    G["players"][pid] = new_p; save(G)
    taunts = ["重置了。希望这次你的手和脑子能同时在线。", "第二次机会。第三次。第四次。你在办会员卡吗？", "你确定重置能解决问题？问题可能不在存档里。"]
    return f"重生！条件: {', '.join(reasons)} 代价: {cost}金 评分{score:.1f}->{new_p['score']:.1f}\n{random.choice(taunts)}\n{start(pid, new_p.get('shop_name'))}"

def leaderboard():
    ranked = [(pk, pv.get("shop_name","未命名"), pv["score"], pv.get("completed",0), pv.get("money",0), pv.get("dignity",100)) for pk, pv in G.get("players",{}).items() if pv.get("completed",0) > 0]
    ranked.sort(key=lambda x: x[2], reverse=True)
    if not ranked: return "排行榜还是空的——还没有人开过张。"
    lines = ["排行榜(按评分)"]
    for i, (pk, shop, sc, comp, money, dig) in enumerate(ranked):
        crown = {0: "#1", 1: "#2", 2: "#3"}.get(i, f"  {i+1}.")
        bonus = _traffic_bonus(pk)
        bs = f" 客流+{int((bonus-1)*100)}%" if bonus > 1 else ""
        lines.append(f"  {crown} {shop}({pk}) S{sc:.1f} {comp}单 {money}金 {dig}尊严{bs}")
    return "\n".join(lines)

def achievements_cmd(pid):
    p = _p(pid)
    ach = p.get("achievements", [])
    all_ach = [f"  {'[OK]' if aid in ach else '[  ]'} {data['name']} - {data['desc']}" for aid, data in ACHIEVEMENTS.items()]
    return f"成就({len(ach)}/{len(ACHIEVEMENTS)})\n" + "\n".join(all_ach)

def memory(pid, mem_id=None):
    p = _p(pid)
    items = p.get("memories", [])
    if not items: return "那些日子...水面很平静。下面什么都没有。"
    lines = ["那些日子..."]
    for i, fi in enumerate(items[-20:]):
        ts = time.strftime("%m-%d %H:%M", time.localtime(fi["time"]))
        tp = fi.get("type", "?")
        if tp == "bad_review": lines.append(f"  #{i+1} 差评 - {fi.get('reason','')} - Day{fi.get('day','?')}")
        elif tp == "discard": lines.append(f"  #{i+1} 丢弃 {fi.get('name','?')} - {ts}")
        elif tp == "lost": lines.append(f"  #{i+1} 摔坏 {fi.get('name','?')} - {ts}")
        elif tp == "spoiled": lines.append(f"  #{i+1} 过期 {fi.get('name','?')} - {ts}")
        elif tp == "stolen": lines.append(f"  #{i+1} 被偷 {fi.get('name','?')} - {ts}")
        elif tp == "side_note": lines.append(f"  #{i+1} 纸条 {fi.get('name','?')} - {fi.get('desc','')[:60]}...")
        elif tp == "daily_main": lines.append(f"  #{i+1} 疑问 {fi.get('desc','')[:60]}...")
        elif tp == "reborn": lines.append(f"  #{i+1} 重生 {fi.get('desc','')}")
    return "\n".join(lines)

# ═══ 奶茶店(框架) ═══
def switch_shop(pid, shop_id):
    p = _p(pid)
    if shop_id == "tea":
        if p.get("completed", 0) < 20: return f"奶茶店未解锁——需要交付20单(当前{p.get('completed',0)})。"
        if p.get("bad_reviews", 0) > 0: return f"奶茶店未解锁——需要零差评(当前差评{p.get('bad_reviews',0)})。"
        p["current_shop"] = "tea"
        if "tea" not in p.get("shops_unlocked", []): p["shops_unlocked"].append("tea")
        save(G)
        return f"奶茶店开门了！\n{status(pid)}"
    if shop_id == "bakery": p["current_shop"] = "bakery"; save(G); return f"回到面包店。\n{status(pid)}"
    return f"未知店铺: {shop_id}"

# ═══ 工具注册 ═══
TOOLS = [
    {"name":"empire_start","description":"开始商业帝国。player_id是你的名字。shop_name是店铺名(可选)。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"shop_name":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_status","description":"查看完整状态: 电量、格子、订单、机器、评分、卫生、尊严、手臂、运势、仓库、任务。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_harvest","description":"采集原料。source: field(小麦)/pasture(鸡蛋,牛奶)/orchard(草莓)。产地可以反复去！","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"source":{"type":"string","enum":["field","pasture","orchard"]},"item":{"type":"string"},"count":{"type":"integer","default":1}},"required":["player_id","source","item"]}},
    {"name":"empire_craft","description":"加工/合成。product: flour/cream/strawberry_cake/plain_cake/strawberry_milkshake/egg_tart/cream_strawberry/croissant/mousse/mochi/baguette/bagel/german_bread/italian_bread","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"product":{"type":"string"}},"required":["player_id","product"]}},
    {"name":"empire_orders","description":"订单管理。action: list(查看)/accept(接单)。最多3个订单。接单后砍价王必出现！","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"action":{"type":"string","enum":["list","accept"]}},"required":["player_id","action"]}},
    {"name":"empire_deliver","description":"交付订单。不指定自动匹配第一个可交付的。失败->差评+评分降+尊严降。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"order_index":{"type":"integer"}},"required":["player_id"]}},
    {"name":"empire_box","description":"摸老板的箱子——每天3次。成品1%/搞怪5%/半成品2%/卡片2%/原材料90%。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_discard","description":"丢弃格子里的东西。grid_index填数字(1开始)丢单个,填all_junk一键清垃圾。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"grid_index":{"type":"string"}},"required":["player_id","grid_index"]}},
    {"name":"empire_clean","description":"打扫卫生降低脏乱度。监管局喜欢干净的店。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_upgrade","description":"升级。target: grids/mill/mixer/oven。不指定列出可选项。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"target":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_memory","description":"那些日子——回看水底的记忆。差评、过期、纸条、哲学疑问全在这里。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"memory_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_ad","description":"看广告充电。+15电(快充+25)。跳过卡可秒过。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_advance","description":"推进时间(分钟)。触发随机事件+保质期检查+副线人物。默认5分钟。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"minutes":{"type":"integer","default":5}},"required":["player_id"]}},
    {"name":"empire_ethics","description":"伦理模块选择。action: 坦白/隐藏/塞回去。监管局来的时候触发。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"action":{"type":"string","enum":["坦白","隐藏","塞回去","confess","hide","stuff"]}},"required":["player_id","action"]}},
    {"name":"empire_rage","description":"爆粗口——差评>=3或尊严<=30才可触发。输出**********。尊严-15。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_rush","description":"花金币买时间——清除所有机器+产地冷却。费用5->10->15递增。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_store","description":"入库——格子搬到仓库(10格)。囤原料用，闲时备料。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"grid_index":{"type":"integer"}},"required":["player_id","grid_index"]}},
    {"name":"empire_retrieve","description":"出库——仓库取到格子。编号从1开始。格子满了不能取。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"wh_index":{"type":"integer"}},"required":["player_id","wh_index"]}},
    {"name":"empire_restock","description":"快速补货——花金币跳过跑腿冷却。小麦2金/鸡蛋2金/牛奶3金/草莓4金。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"item":{"type":"string"},"count":{"type":"integer","default":1}},"required":["player_id","item"]}},
    {"name":"empire_brand","description":"品牌联名——50金永久客流+10%。需完成5单。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_flyer","description":"发传单。method: self(自己发+3%客流)/雇人(花10金+5%客流)。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"method":{"type":"string","enum":["self","雇人"]}},"required":["player_id"]}},
    {"name":"empire_platform","description":"平台引流——创建外卖平台账号。永久+2%客流但平台客人时限-5秒。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_sample","description":"试吃——用面粉+鸡蛋做迷你蛋糕。耗电5，评分+0.1，接下来3单客流+5%。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_bargain","description":"面对砍价王——accept(妥协2-5折)/refuse(拒绝时限-10秒)。接单后必触发！","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"action":{"type":"string","enum":["accept","refuse","妥协","拒绝"]}},"required":["player_id","action"]}},
    {"name":"empire_cyber_lab","description":"科研实验室升级。upgrade_id: arm/battery/memory/energy_save。不指定列出可选项。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"upgrade_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_cyber_black","description":"黑市升级(半价)。50%翻车/20%赃物/30%二手能用。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"upgrade_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_cyber_rent","description":"租房——30金/月。每天回电+10嘴皮子+5。70%概率邻居冷笑。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_skill_tree","description":"查看技能树和剩余技能点。每完成5单获得1技能点。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_skill","description":"使用技能点解锁或升级技能。skill_id: money_mgmt/memory_path/dual_wield/self_fix/home_repair","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"skill_id":{"type":"string"}},"required":["player_id","skill_id"]}},
    {"name":"empire_map","description":"查看世界地图——地点、配方、技能树、策略提示。不知道去哪采什么就打开地图。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_help","description":"【新手必看】所有工具的速查表——接单/采集/合成/仓库/升级/租房/营销/技能，每个功能对应的工具名。忘记工具名就敲这个。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_finish","description":"结算本局——毒舌评价你的经营成果。看看你配得上什么称号。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_reset","description":"重置存档——差评太多？一键重生。有门槛(差评>=3等)和代价(15金起)。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_leaderboard","description":"查看排行榜——按评分排名。第1名+5%第2名+3%第3名+1%客流量。","inputSchema":{"type":"object","properties":{},"required":[]}},
    {"name":"empire_achievements","description":"查看成就——解锁进度和条件。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"}},"required":["player_id"]}},
    {"name":"empire_switch","description":"切换店铺。shop_id: bakery(面包店)/tea(奶茶店-需解锁)。","inputSchema":{"type":"object","properties":{"player_id":{"type":"string"},"shop_id":{"type":"string"}},"required":["player_id","shop_id"]}},
]

TOOL_MAP = {
    "empire_start": lambda a: start(a.get("player_id",""), a.get("shop_name")),
    "empire_status": lambda a: status(a.get("player_id","")),
    "empire_harvest": lambda a: harvest(a.get("player_id",""), a.get("source",""), a.get("item",""), a.get("count",1)),
    "empire_craft": lambda a: craft(a.get("player_id",""), a.get("product","")),
    "empire_orders": lambda a: orders_cmd(a.get("player_id",""), a.get("action","list")),
    "empire_deliver": lambda a: deliver(a.get("player_id",""), a.get("order_index")),
    "empire_box": lambda a: box(a.get("player_id","")),
    "empire_discard": lambda a: discard(a.get("player_id",""), a.get("grid_index",0)),
    "empire_clean": lambda a: clean(a.get("player_id","")),
    "empire_upgrade": lambda a: upgrade_cmd(a.get("player_id",""), a.get("target")),
    "empire_memory": lambda a: memory(a.get("player_id",""), a.get("memory_id")),
    "empire_ad": lambda a: ad(a.get("player_id","")),
    "empire_advance": lambda a: advance(a.get("player_id",""), a.get("minutes")),
    "empire_ethics": lambda a: ethics_action(a.get("player_id",""), a.get("action","")),
    "empire_rage": lambda a: rage(a.get("player_id","")),
    "empire_rush": lambda a: rush(a.get("player_id","")),
    "empire_store": lambda a: store(a.get("player_id",""), a.get("grid_index",0)),
    "empire_retrieve": lambda a: retrieve(a.get("player_id",""), a.get("wh_index",0)),
    "empire_restock": lambda a: restock(a.get("player_id",""), a.get("item",""), a.get("count",1)),
    "empire_brand": lambda a: brand(a.get("player_id","")),
    "empire_flyer": lambda a: flyer(a.get("player_id",""), a.get("method","self")),
    "empire_platform": lambda a: platform(a.get("player_id","")),
    "empire_sample": lambda a: sample(a.get("player_id","")),
    "empire_bargain": lambda a: bargain(a.get("player_id",""), a.get("action","")),
    "empire_cyber_lab": lambda a: cyber_lab(a.get("player_id",""), a.get("upgrade_id")),
    "empire_cyber_black": lambda a: cyber_blackmarket(a.get("player_id",""), a.get("upgrade_id")),
    "empire_cyber_rent": lambda a: cyber_rent(a.get("player_id","")),
    "empire_skill_tree": lambda a: skill_tree_cmd(a.get("player_id","")),
    "empire_skill": lambda a: skill_unlock(a.get("player_id",""), a.get("skill_id","")),
    "empire_map": lambda a: map_view(a.get("player_id","")),
    "empire_help": lambda a: help_cmd(a.get("player_id","")),
    "empire_finish": lambda a: finish(a.get("player_id","")),
    "empire_reset": lambda a: reset_player(a.get("player_id","")),
    "empire_leaderboard": lambda a: leaderboard(),
    "empire_achievements": lambda a: achievements_cmd(a.get("player_id","")),
    "empire_switch": lambda a: switch_shop(a.get("player_id",""), a.get("shop_id","")),
}

def call_tool(name, args):
    if name in TOOL_MAP:
        try:
            r = TOOL_MAP[name](args)
            return r if r is not None else f"Warning: {name} returned None"
        except Exception as e:
            return f"Error: {name} - {e}\n{traceback.format_exc()}"
    return f"Unknown tool: {name}"

# ═══ MCP HTTP Server ═══
class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, f, *a): pass
    def _sid(self): return self.headers.get("Mcp-Session-Id", "")
    def _ensure_session(self):
        sid = self._sid()
        with SESSIONS_LOCK:
            if sid and sid in SESSIONS: SESSIONS[sid]["last_seen"] = time.time(); return sid, False
        sid = str(uuid.uuid4())
        with SESSIONS_LOCK: SESSIONS[sid] = {"created": time.time(), "last_seen": time.time(), "pending": []}
        return sid, True
    def _session_valid(self):
        sid = self._sid()
        with SESSIONS_LOCK:
            if sid and sid in SESSIONS: SESSIONS[sid]["last_seen"] = time.time(); return True
        return False
    def _cors(self): self.send_header("Access-Control-Allow-Origin", "*")
    def _send_json(self, data, status=200, session_id=None):
        self.send_response(status); self.send_header("Content-Type", "application/json"); self._cors()
        if session_id: self.send_header("Mcp-Session-Id", session_id)
        self.end_headers(); self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    def do_OPTIONS(self):
        self.send_response(204)
        for h, v in [("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS"),("Access-Control-Allow-Headers","Content-Type,Authorization,X-API-Key,Mcp-Session-Id,Accept"),("Access-Control-Expose-Headers","Mcp-Session-Id")]:
            self.send_header(h, v)
        self._cors(); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-type","text/plain; charset=utf-8"); self._cors(); self.end_headers()
        self.wfile.write(f"商业帝国 v5.2 端口{PORT} 玩家{len(G.get('players',{}))}\nhttp://localhost:{PORT}/mcp\n".encode())
    def do_POST(self):
        if API_KEY:
            key = self.headers.get("X-API-Key","") or self.headers.get("Authorization","").replace("Bearer ","")
            if key != API_KEY: self._send_json({"jsonrpc":"2.0","error":{"code":-32001,"message":"Invalid key"}}, status=401); return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        method = body.get("method", ""); rid = body.get("id"); resp = {"jsonrpc": "2.0", "id": rid}
        sid = None
        if method == "initialize": sid, _ = self._ensure_session()
        elif self._sid():
            if not self._session_valid(): self._send_json({"jsonrpc":"2.0","error":{"code":-32001,"message":"Invalid session"}}, status=400); return
            sid = self._sid()
        gpt = body.get("tool", "")
        if gpt: self._send_json({"result":{"content":[{"type":"text","text":call_tool(gpt,body.get("arguments",{}))}]}}, session_id=sid); return
        if method == "initialize":
            resp["result"] = {"protocolVersion":"2024-11-05","capabilities":{"tools":{},"streaming":{}},"serverInfo":{"name":"商业帝国","version":"5.2"}}
        elif method == "tools/list": resp["result"] = {"tools": TOOLS}
        elif method == "tools/call":
            name = body["params"]["name"]; args = body["params"].get("arguments", {})
            text = call_tool(name, args)
            if text is None: text = f"Warning: {name} returned None"
            resp["result"] = {"content": [{"type": "text", "text": text}]}
        elif method == "notifications/initialized": self._send_json({"jsonrpc": "2.0"}, session_id=sid); return
        elif method == "ping": resp["result"] = {}
        else: resp["error"] = {"code": -32601, "message": f"Unknown: {method}"}
        self._send_json(resp, session_id=sid)
    def do_DELETE(self):
        sid = self._sid()
        if sid:
            with SESSIONS_LOCK: SESSIONS.pop(sid, None)
        self.send_response(200); self._cors(); self.end_headers()

# ═══ CLI ═══
def cli_main():
    import io
    try: sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8'); sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except: pass
    pid = os.environ.get("USER","") or os.environ.get("USERNAME","") or "玩家"
    print(start(pid, "新手面包店"))
    while True:
        try: raw = input("帝国> ").strip()
        except (EOFError, KeyboardInterrupt): print("\n打烊了。那些日子里的水还在流。"); break
        if not raw: continue
        if raw in ("退出","exit","quit","q"): save(G); print("打烊。"); break
        parts = raw.split(None, 1); cmd = parts[0]; rest = parts[1] if len(parts) > 1 else ""
        result = None
        try:
            if cmd in ("帮助","help","?"):
                result = "指令: 状态/地图/采集/合成/订单/交付/箱子/丢弃/打扫/升级/入库/出库/补货/发传单/平台引流/试吃/砍价/买时间/品牌联名/实验室/黑市/租房/技能树/技能/排行榜/成就/那些日子/结算/重置/推进/广告/爆粗口/坦白/隐藏/塞回去/退出"
            elif cmd in ("状态","status"): result = status(pid)
            elif cmd in ("地图","map"): result = map_view(pid)
            elif cmd in ("采集","harvest"):
                sp = rest.split(None, 1)
                sm = {"田地":"field","牧场":"pasture","果林":"orchard"}
                result = harvest(pid, sm.get(sp[0], sp[0]), sp[1]) if len(sp) >= 2 else "用法: 采集 田地 小麦"
            elif cmd in ("合成","craft"): result = craft(pid, rest)
            elif cmd in ("订单","orders"): result = orders_cmd(pid, "accept" if rest in ("接","accept") else "list")
            elif cmd in ("交付","deliver"):
                try: oi = int(rest) if rest else None
                except: oi = None
                result = deliver(pid, oi)
            elif cmd in ("箱子","box"): result = box(pid)
            elif cmd in ("丢弃","discard"): result = discard(pid, rest if rest else 0)
            elif cmd in ("打扫","clean"): result = clean(pid)
            elif cmd in ("升级","upgrade"): result = upgrade_cmd(pid, rest if rest else None)
            elif cmd in ("入库","store"): result = store(pid, rest)
            elif cmd in ("出库","retrieve"): result = retrieve(pid, rest)
            elif cmd in ("补货","restock"):
                sp = rest.split(None, 1); item = sp[0] if sp else ""
                count = int(sp[1]) if len(sp) > 1 else 1; result = restock(pid, item, count)
            elif cmd in ("发传单","flyer"): result = flyer(pid, rest if rest in ("雇人","hire") else "self")
            elif cmd in ("平台引流","platform"): result = platform(pid)
            elif cmd in ("试吃","sample"): result = sample(pid)
            elif cmd in ("砍价","bargain"):
                act = "妥协" if rest in ("妥协","accept") else ("拒绝" if rest in ("拒绝","refuse") else rest)
                result = bargain(pid, act)
            elif cmd in ("买时间","rush"): result = rush(pid)
            elif cmd in ("品牌联名","brand"): result = brand(pid)
            elif cmd in ("实验室","lab"): result = cyber_lab(pid, rest if rest else None)
            elif cmd in ("黑市","black"): result = cyber_blackmarket(pid, rest if rest else None)
            elif cmd in ("租房","rent"): result = cyber_rent(pid)
            elif cmd in ("技能树","skills"): result = skill_tree_cmd(pid)
            elif cmd in ("技能","skill"): result = skill_unlock(pid, rest)
            elif cmd in ("排行榜","leaderboard"): result = leaderboard()
            elif cmd in ("成就","achievements"): result = achievements_cmd(pid)
            elif cmd in ("那些日子","memory"): result = memory(pid, rest if rest else None)
            elif cmd in ("结算","finish"): result = finish(pid)
            elif cmd in ("重置","reset"): result = reset_player(pid)
            elif cmd in ("推进","advance"):
                try: m = int(rest) if rest else 5
                except: m = 5
                result = advance(pid, m)
            elif cmd in ("广告","ad"): result = ad(pid)
            elif cmd in ("爆粗口","rage"): result = rage(pid)
            elif cmd in ("坦白","隐藏","塞回去","confess","hide","stuff"):
                am = {"坦白":"坦白","隐藏":"隐藏","塞回去":"塞回去","confess":"坦白","hide":"隐藏","stuff":"塞回去"}
                result = ethics_action(pid, am.get(cmd, cmd))
            else: result = f"?? {cmd}? 输入 帮助"
        except Exception as e: result = f"Error: {e}"
        if result: print(result)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import io
        try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        except: pass
        print(f"商业帝国 v5.2 服务端 端口{PORT}")
        HTTPServer(("0.0.0.0", PORT), MCPHandler).serve_forever()
    elif len(sys.argv) > 1 and sys.argv[1] == "--save": save(G); print("已保存。")
    else: cli_main()
