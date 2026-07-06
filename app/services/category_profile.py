from __future__ import annotations

from dataclasses import dataclass


MAIN_CATEGORY_LABELS = {
    "food": "食品饮品",
    "beauty": "美妆护肤",
    "home": "家居日用",
    "pet": "宠物用品",
    "other": "其他好物",
}

MAIN_CATEGORY_ALIASES = {
    "食品": "food",
    "饮品": "food",
    "零食": "food",
    "美妆": "beauty",
    "护肤": "beauty",
    "家居": "home",
    "日用": "home",
    "收纳": "home",
    "清洁": "home",
    "宠物": "pet",
}

GENERAL_SUBCATEGORY = {
    "food": "food_general",
    "beauty": "beauty_general",
    "home": "home_general",
    "pet": "pet_general",
    "other": "general",
}

SUBCATEGORY_ORDER = {
    "food": ["bakery", "drink", "snack", "light_meal"],
    "beauty": ["hand_body_care", "portable_care", "makeup", "skincare"],
    "home": ["cup_bottle", "storage", "cleaning", "desktop_commute"],
    "pet": ["pet_general"],
    "other": ["general"],
}

SUBCATEGORY_KEYWORDS = {
    "bakery": ["蛋糕", "面包", "吐司", "贝果", "曲奇", "饼干", "蛋挞", "泡芙", "糕点", "甜品", "欧包", "瑞士卷", "牛角包", "蛋黄酥", "麻薯"],
    "drink": ["咖啡", "茶", "奶茶", "果汁", "冲泡", "饮料", "豆浆", "牛奶", "燕麦奶", "椰乳", "气泡水", "茶包", "挂耳", "冷萃"],
    "snack": ["零食", "薯片", "坚果", "肉干", "果干", "糖果", "巧克力", "海苔", "辣条", "膨化", "梅子", "鸭脖", "卤味"],
    "light_meal": ["代餐", "轻食", "麦片", "燕麦", "能量棒", "蛋白棒", "沙拉", "即食鸡胸", "低脂", "控卡", "全麦", "谷物"],
    "skincare": ["面霜", "精华", "水乳", "爽肤水", "乳液", "面膜", "洁面", "洗面奶", "防晒", "修护", "补水", "保湿", "屏障"],
    "makeup": ["口红", "唇釉", "粉底", "气垫", "眼影", "腮红", "睫毛膏", "眉笔", "遮瑕", "散粉", "高光", "修容", "妆前乳"],
    "hand_body_care": ["护手霜", "身体乳", "润肤乳", "护手", "手霜", "香氛护手", "唇膏", "润唇膏", "身体护理"],
    "portable_care": ["防晒棒", "喷雾", "小样", "便携", "随身", "补涂"],
    "cup_bottle": ["保温杯", "保温瓶", "水杯", "杯子", "杯", "随行杯", "马克杯", "咖啡杯", "儿童杯", "吸管杯", "运动水壶"],
    "storage": ["收纳盒", "收纳箱", "置物架", "抽屉盒", "整理箱", "衣物收纳", "桌面收纳", "化妆品收纳", "挂钩", "收纳袋"],
    "cleaning": ["清洁剂", "洗洁精", "湿巾", "抹布", "拖把", "扫把", "除菌", "去污", "刷子", "清洁膏", "洁厕", "厨房清洁", "浴室清洁"],
    "desktop_commute": ["笔记本", "文具", "笔袋", "电脑支架", "鼠标垫", "数据线", "充电器", "手机支架", "通勤包", "钥匙包", "卡包"],
    "pet_general": ["猫", "狗", "宠物", "猫粮", "狗粮", "毛孩子", "猫砂", "逗猫", "宠物零食"],
}

SUBCATEGORY_COPY = {
    "bakery": {
        "main_category": "food",
        "tone_tags": ["下午茶", "口感松软", "家里囤"],
        "title_patterns": [
            "{name}，下午茶吃刚刚好",
            "早餐和下午茶都能安排的{name}",
            "想偷懒备点甜口小点心，可以看看{name}",
            "{name}这种松软口感，真的很适合家里囤一点",
            "配咖啡和牛奶都顺口的{name}",
        ],
        "selling_points": ["下午茶更合适", "口感松软", "配咖啡牛奶都顺", "家里囤一点", "解馋刚刚好"],
        "hashtags": ["#下午茶", "#小蛋糕", "#早餐分享", "#甜品推荐", "#家里囤货", "#烘焙点心"],
        "suitable_for": "喜欢早餐和下午茶分享的人",
        "recommend_reason": "口感松软，配咖啡或牛奶都顺，家里囤一点会很方便",
        "comments": ["你更想拿它配咖啡还是牛奶？", "这类小蛋糕你会放家里常备吗？", "还想看哪些下午茶点心分享？"],
        "body_patterns": [
            "最近这种{name}真的很适合下午茶，口感松软一点，配咖啡或者牛奶都挺顺。家里囤一点，嘴馋的时候拿出来也方便。{detail}",
            "{name}这种小点心我会更想放在早餐和下午茶场景里，口感不硬，吃起来比较轻松。要是平时就喜欢在家里备点甜口小东西，这类会更自然。{detail}",
            "如果你最近想找一款不夸张、但很适合配茶配咖啡的小点心，{name}这类烘焙糕点会更稳一点。口感和场景都比较好写，做种草内容也不费劲。{detail}",
        ],
        "summary_sentence": "{name}很适合早餐和下午茶场景。",
        "point_details": ["下午茶拿出来刚刚好", "口感松软更容易写出感觉", "配咖啡配牛奶都自然"],
        "summary_labels": ["适合场景", "口感亮点", "分享理由"],
    },
    "drink": {
        "main_category": "food",
        "tone_tags": ["早八友好", "办公室", "冷冷热热都行"],
        "title_patterns": [
            "{name}，早八真的能派上用场",
            "办公室备着更顺手的{name}",
            "想找一款入口顺一点的饮品，可以看看{name}",
            "{name}这种冷热点都能喝的，日常会更方便",
            "早餐和下午都能安排的{name}",
        ],
        "selling_points": ["早八更省心", "办公室备着方便", "入口更顺", "冷冷热热都适合", "搭早餐也自然"],
        "hashtags": ["#饮品分享", "#办公室好物", "#早八", "#咖啡茶饮", "#早餐搭子", "#日常囤货"],
        "suitable_for": "适合早八和办公室常备的人",
        "recommend_reason": "入口顺一点，冷冷热热都能喝，日常备着会更省心",
        "comments": ["你更喜欢热饮还是冷饮？", "这类饮品你会放办公室常备吗？", "还想看哪些早餐搭子分享？"],
        "body_patterns": [
            "{name}这种饮品我会更想放在早八和办公室场景里，入口顺一点，搭早餐也自然。要是平时就想备点随手能喝的，这类会很省心。{detail}",
            "最近会反复喝到{name}，冷的热的都能安排，放办公室或者家里都不别扭。下午想提提神，或者早餐想搭点喝的，这类都挺合适。{detail}",
            "如果你平时会在办公室备点饮品，{name}这种方向会比单纯图新鲜更稳一点。顺口、好搭早餐、日常也比较容易坚持。{detail}",
        ],
        "summary_sentence": "{name}适合早八和办公室日常场景。",
        "point_details": ["早八搭早餐会更顺", "入口感受更容易描述", "办公室或家里都能备着"],
        "summary_labels": ["适合时段", "入口感受", "分享理由"],
    },
    "snack": {
        "main_category": "food",
        "tone_tags": ["解馋", "追剧", "分享装"],
        "title_patterns": [
            "{name}，追剧的时候真的很容易吃掉",
            "办公室备一点更合适的{name}",
            "想找解馋小零食，可以看看{name}",
            "{name}这种小包装，分享起来也方便",
            "嘴馋的时候会想拿出来的{name}",
        ],
        "selling_points": ["解馋更直接", "追剧更配", "办公室备一点", "分享装更方便", "口感层次更丰富"],
        "hashtags": ["#零食分享", "#追剧零食", "#办公室囤货", "#小包装", "#解馋推荐", "#下午茶零食"],
        "suitable_for": "喜欢追剧和办公室囤零食的人",
        "recommend_reason": "解馋直接，分享方便，放办公室或家里都合适",
        "comments": ["你更喜欢咸口还是甜口零食？", "这类小包装你会囤一点吗？", "还想看哪些追剧零食分享？"],
        "body_patterns": [
            "{name}这种零食我会更想放在追剧和下午茶场景里，嘴馋的时候拿出来很直接。小包装或者分享装也更方便，不会一下子吃得太重。{detail}",
            "如果平时就喜欢在办公室备一点解馋小东西，{name}这种方向会比较稳。口感层次更明显，也更容易写出真实体验。{detail}",
            "最近会反复拿出来吃的就是{name}这类零食，不一定多特别，但在家里囤一点或者办公室放一点都很自然。{detail}",
        ],
        "summary_sentence": "{name}更适合追剧和解馋场景。",
        "point_details": ["追剧拿出来更合适", "小包装分享更方便", "办公室和家里都能备一点"],
        "summary_labels": ["解馋场景", "口感层次", "囤货理由"],
    },
    "light_meal": {
        "main_category": "food",
        "tone_tags": ["早餐省心", "轻负担", "办公室"],
        "title_patterns": [
            "{name}，忙的时候当早餐会更省心",
            "想找轻食方向，可以先看看{name}",
            "{name}这种日常准备起来更方便",
            "办公室备着更合适的{name}",
            "不想太麻烦的时候，会想到{name}",
        ],
        "selling_points": ["早餐更省心", "轻负担一点", "准备方便", "办公室也合适", "日常饮食更好安排"],
        "hashtags": ["#轻食分享", "#早餐省心", "#办公室常备", "#日常饮食", "#代餐参考", "#谷物轻食"],
        "suitable_for": "适合工作日早餐和轻食场景的人",
        "recommend_reason": "准备方便，轻负担一点，更适合忙的时候安排日常饮食",
        "comments": ["你更会把它放在早餐还是加餐？", "这类轻食你会放办公室吗？", "还想看哪些省心早餐分享？"],
        "body_patterns": [
            "{name}这种我会更想放在工作日早餐或者加餐场景里，准备起来省心一点，也不会显得太重。忙的时候能顺手安排上，这一点就很加分。{detail}",
            "如果你平时会关注轻食或代餐方向，{name}这种更适合写成日常饮食里的省心选择，而不是夸张功能型表达。办公室备着或者早餐搭着都自然。{detail}",
            "最近会留意{name}这类轻食，主要是因为准备方便，工作日也比较容易坚持。想把饮食安排得简单一点时，这类方向会更稳。{detail}",
        ],
        "summary_sentence": "{name}适合工作日早餐和轻食场景。",
        "point_details": ["忙的时候准备更省心", "轻负担一点更自然", "办公室也容易安排"],
        "summary_labels": ["适合时段", "轻负担", "准备方便"],
    },
    "skincare": {
        "main_category": "beauty",
        "tone_tags": ["补水", "不厚重", "肤感舒服"],
        "title_patterns": [
            "{name}，最近换季会更想用它",
            "日常护理里会留下的{name}",
            "想找不厚重一点的护肤品，可以看看{name}",
            "{name}这种肤感，更适合日常慢慢用",
            "妆前或晚间护理都能安排的{name}",
        ],
        "selling_points": ["补水更稳一点", "肤感舒服", "不厚重更日常", "换季更容易用上", "妆前也好安排"],
        "hashtags": ["#护肤分享", "#补水保湿", "#换季护理", "#日常护理", "#肤感分享", "#妆前护肤"],
        "suitable_for": "适合关注肤感和日常护理的人",
        "recommend_reason": "补水和肤感都更稳一点，日常护理更容易坚持",
        "comments": ["你更在意补水还是吸收感？", "换季时你会更关注哪一步护理？", "还想看哪些日常护肤分享？"],
        "body_patterns": [
            "{name}这类护肤品我会更看重肤感和日常使用感，不想太厚重，但也希望补水和保湿都稳一点。妆前或者晚上护理里安排它都比较自然。{detail}",
            "最近换季的时候会更在意{name}这种产品，主要还是看吸收感和用完之后皮肤会不会觉得闷。要是你也偏好轻一点的护理感受，这类方向会更适合参考。{detail}",
            "如果你平时做护肤分享不想写得太像广告，{name}这种更适合从肤感、补水和使用场景去写，读起来会更像真实体验。{detail}",
        ],
        "summary_sentence": "{name}适合日常护肤和换季护理场景。",
        "point_details": ["补水和肤感更容易说明白", "妆前或晚间护理都能带到", "不厚重更适合日常坚持"],
        "summary_labels": ["肤感重点", "护理场景", "换季参考"],
    },
    "makeup": {
        "main_category": "beauty",
        "tone_tags": ["显色", "持妆", "通勤妆"],
        "title_patterns": [
            "{name}，日常通勤妆很容易用上",
            "想找自然一点的妆感，可以看看{name}",
            "{name}这种上脸效果更适合日常妆",
            "通勤化妆包里会留下的{name}",
            "{name}，提气色这件事它还挺稳",
        ],
        "selling_points": ["显色更自然", "通勤妆更顺手", "妆感不突兀", "上脸更服帖", "日常提气色"],
        "hashtags": ["#彩妆分享", "#通勤妆", "#日常妆容", "#显色自然", "#持妆表现", "#化妆包常备"],
        "suitable_for": "适合日常通勤妆和提气色需求的人",
        "recommend_reason": "显色自然，通勤妆更顺手，上脸也比较服帖",
        "comments": ["你更喜欢自然妆感还是存在感强一点？", "这类彩妆你会放通勤化妆包吗？", "还想看哪些日常妆容分享？"],
        "body_patterns": [
            "{name}这种彩妆我会更看重上脸是不是自然，通勤妆能不能顺手用上。显色有一点，但不会太跳，日常提气色就够了。{detail}",
            "如果你平时更常画日常妆，{name}这种方向会更好写真实体验。比如显色、服帖感、通勤时会不会拿出来补一下，这些都比夸张效果更重要。{detail}",
            "最近会留下{name}这种彩妆，主要还是因为通勤妆里好安排。妆感自然一点、上脸顺一点，反而更容易长期用下去。{detail}",
        ],
        "summary_sentence": "{name}适合日常通勤妆和提气色场景。",
        "point_details": ["显色和妆感更容易写清楚", "通勤妆里更容易安排", "上脸服帖会更加分"],
        "summary_labels": ["妆感重点", "通勤妆面", "上脸表现"],
    },
    "hand_body_care": {
        "main_category": "beauty",
        "tone_tags": ["随身带", "滋润", "不黏腻"],
        "title_patterns": [
            "包里常备的{name}",
            "洗完手顺手涂一点的{name}",
            "{name}这种更适合秋冬常备",
            "想找不黏腻一点的手部护理，可以看看{name}",
            "{name}，属于随身带着更安心那类",
        ],
        "selling_points": ["随身带更方便", "滋润但不黏", "秋冬更容易用上", "手部护理更顺手", "包里常备更安心"],
        "hashtags": ["#护手霜", "#手部护理", "#随身好物", "#秋冬护理", "#不黏腻", "#身体护理"],
        "suitable_for": "适合秋冬和日常手部护理场景的人",
        "recommend_reason": "随身带方便，滋润感够用，又不会太黏腻",
        "comments": ["你更在意滋润感还是不黏手？", "护手霜你会放包里还是桌上？", "还想看哪些秋冬护理分享？"],
        "body_patterns": [
            "{name}这种我会更想放在包里常备，洗完手或者手有点干的时候顺手涂一下刚好。滋润感够，但不会太黏，日常用起来会更安心。{detail}",
            "最近会留下{name}这种手部或身体护理，主要还是看它是不是够细腻、会不会一涂就觉得厚。秋冬或者空调房里更容易想到它。{detail}",
            "如果你也想找一款随身带着方便、日常不会懒得用的护理产品，{name}这种方向会更适合写真实使用感。{detail}",
        ],
        "summary_sentence": "{name}适合秋冬和随身护理场景。",
        "point_details": ["洗完手顺手涂更方便", "滋润感和细腻度更关键", "包里常备会更安心"],
        "summary_labels": ["使用场景", "滋润感", "随身常备"],
    },
    "portable_care": {
        "main_category": "beauty",
        "tone_tags": ["随身带", "补涂方便", "通勤出门"],
        "title_patterns": [
            "{name}，出门前后都很容易用上",
            "想找便携护理好物，可以看看{name}",
            "{name}这种放包里就很安心",
            "午后补一补更方便的{name}",
            "通勤包里会想留下的{name}",
        ],
        "selling_points": ["随身带更轻松", "补涂更方便", "包里不占地方", "通勤也好带", "出门前后都能安排"],
        "hashtags": ["#便携护理", "#随身补涂", "#通勤好物", "#包里常备", "#午后补涂", "#防晒补涂"],
        "suitable_for": "适合出门前后和午后补涂场景的人",
        "recommend_reason": "便携、补涂方便、通勤放包里也不占地方",
        "comments": ["你会更在意便携还是补涂感受？", "这类产品你会放通勤包吗？", "还想看哪些随身护理分享？"],
        "body_patterns": [
            "{name}这种更适合放在通勤包里，出门前或者午后想补一下的时候会很方便。体积不大、拿出来顺手，才更容易真的用起来。{detail}",
            "如果你平时会在外面补涂或补用，{name}这种方向会更好写真实体验。重点不是夸张功效，而是它是不是够方便、会不会放包里不占地方。{detail}",
            "最近会偏爱{name}这类便携护理，主要还是因为出门场景里它真的更容易派上用场。通勤、旅行或者午后补一下都自然。{detail}",
        ],
        "summary_sentence": "{name}适合通勤和午后补涂场景。",
        "point_details": ["出门前后更容易安排", "午后补一下会更方便", "包里常备不会太占地方"],
        "summary_labels": ["补涂场景", "随身方便", "出门前后"],
    },
    "cup_bottle": {
        "main_category": "home",
        "tone_tags": ["通勤带", "容量刚好", "日常补水"],
        "title_patterns": [
            "通勤水杯真的很有必要，{name}这类就够用",
            "上班上学都能带的{name}",
            "想多喝水，可以先换个顺手的{name}",
            "{name}这种放包里也更省心",
            "车里办公室书包都能放的{name}",
        ],
        "selling_points": ["通勤带着方便", "容量刚好", "日常补水更顺手", "冷热饮都适合", "放包里也省心"],
        "hashtags": ["#保温杯", "#通勤好物", "#日常补水", "#上班族好物", "#水杯推荐", "#外出方便"],
        "suitable_for": "适合通勤、上学和日常补水的人",
        "recommend_reason": "通勤带着方便，容量刚好，冷热饮都适合",
        "comments": ["你更在意容量还是便携感？", "水杯你会放车里还是书包里？", "还想看哪些通勤补水好物？"],
        "body_patterns": [
            "通勤带水杯真的会方便很多，{name}这类容量刚好，放车里、办公室或者书包里都顺手。平时想多喝点水的时候，有个顺手的杯子会更容易坚持。{detail}",
            "{name}这种杯壶类我会更在意是不是好带、会不会放包里省心。冷热饮都能用，日常补水场景也更完整，反而更容易长期留下来。{detail}",
            "如果你最近正想换个更适合通勤的水杯，{name}这种方向会比较稳。不是花哨路线，但在办公室、上学路上或者外出时都很实用。{detail}",
        ],
        "summary_sentence": "{name}适合通勤和日常补水场景。",
        "point_details": ["通勤带着方便", "放包里也省心", "车里办公室书包都适合"],
        "summary_labels": ["适合场景", "推荐理由", "日常补水"],
    },
    "storage": {
        "main_category": "home",
        "tone_tags": ["桌面整洁", "分类清楚", "拿取方便"],
        "title_patterns": [
            "{name}，让桌面看起来清爽很多",
            "小空间更适合用上的{name}",
            "想把东西分类得更清楚，可以看看{name}",
            "{name}这种日常整理起来会省心很多",
            "柜子里和桌面都更顺手的{name}",
        ],
        "selling_points": ["桌面更整洁", "分类更清楚", "小空间也友好", "拿取更方便", "日常整理更省心"],
        "hashtags": ["#收纳整理", "#桌面收纳", "#小空间友好", "#整理好物", "#日常整理", "#收纳分享"],
        "suitable_for": "适合桌面和柜内整理场景的人",
        "recommend_reason": "分类更清楚，拿取方便，小空间用起来也友好",
        "comments": ["你更想整理桌面还是柜子？", "这类收纳你会更在意容量还是分类？", "还想看哪些整理好物？"],
        "body_patterns": [
            "{name}这种更适合放在桌面或柜子整理场景里，分类清楚之后，拿东西会顺手很多。小空间里尤其会觉得它的存在感刚刚好。{detail}",
            "如果你平时就想把常用物品收得更整齐一点，{name}这种方向会更稳。重点不在夸张收纳术，而是日常拿取会不会真的更方便。{detail}",
            "最近会留下{name}这类整理好物，主要还是因为桌面或抽屉一旦分好类，生活感会立刻清楚很多。{detail}",
        ],
        "summary_sentence": "{name}适合桌面和柜内整理场景。",
        "point_details": ["分类更清楚会更省心", "小空间也能更整洁", "拿取顺手这一点最加分"],
        "summary_labels": ["适合空间", "整理感受", "拿取方便"],
    },
    "cleaning": {
        "main_category": "home",
        "tone_tags": ["清洁省心", "厨房浴室", "日常常备"],
        "title_patterns": [
            "{name}，日常清洁里真的会常用到",
            "厨房浴室都更省心的{name}",
            "想找顺手一点的清洁用品，可以看看{name}",
            "{name}这种家务时会更容易派上用场",
            "家里常备会更安心的{name}",
        ],
        "selling_points": ["清洁更省心", "厨房浴室都能用上", "去污更直接", "家务效率更高", "日常常备更安心"],
        "hashtags": ["#清洁好物", "#厨房清洁", "#浴室清洁", "#家务省心", "#去污分享", "#日常清洁"],
        "suitable_for": "适合厨房、浴室和日常家务场景的人",
        "recommend_reason": "日常清洁更省心，厨房浴室都容易派上用场",
        "comments": ["你家里更常用在厨房还是浴室？", "这类清洁用品你更在意去污还是顺手？", "还想看哪些家务省心好物？"],
        "body_patterns": [
            "{name}这种会更适合放在厨房、浴室或者日常家务场景里，顺手和省心比花哨更重要。真正能把清洁这件事做得轻松一点，才更值得留下。{detail}",
            "如果你平时就想找一款日常常备的清洁用品，{name}这种方向会更适合从去污感受和使用场景去写。家务效率高一点，体验就已经很不一样了。{detail}",
            "最近会觉得{name}这类清洁用品很实在，尤其是厨房和浴室这些高频区域，用起来顺不顺手差别很明显。{detail}",
        ],
        "summary_sentence": "{name}适合厨房、浴室和日常清洁场景。",
        "point_details": ["厨房浴室更容易派上用场", "清洁效率更值得提", "日常常备会更安心"],
        "summary_labels": ["清洁场景", "省心程度", "日常常备"],
    },
    "desktop_commute": {
        "main_category": "home",
        "tone_tags": ["通勤", "桌面整洁", "包里常备"],
        "title_patterns": [
            "{name}，通勤和桌面都会用到",
            "包里常备会更安心的{name}",
            "想让办公桌更顺手，可以看看{name}",
            "{name}这种日常真的很容易派上用场",
            "轻便一点更适合留下的{name}",
        ],
        "selling_points": ["通勤更顺手", "桌面更整洁", "包里常备方便", "日常使用频率高", "轻便更容易带着走"],
        "hashtags": ["#通勤好物", "#桌面整理", "#办公顺手", "#包里常备", "#效率感", "#日常使用"],
        "suitable_for": "适合办公桌面和通勤场景的人",
        "recommend_reason": "通勤和办公都顺手，轻便一点更容易长期用",
        "comments": ["你更会把它放桌上还是包里？", "这类通勤好物你最在意哪一点？", "还想看哪些桌面顺手小物？"],
        "body_patterns": [
            "{name}这种我会更想放在桌面或者通勤场景里，日常会反复用到，顺手就很重要。包里常备或者办公桌上随手拿到，都会更方便。{detail}",
            "如果你平时很在意桌面是不是清爽、通勤是不是轻便，{name}这种方向会比较稳。不是特别张扬，但使用频率高才是真的加分点。{detail}",
            "最近会留下{name}这类小东西，主要还是因为它很容易进入日常。办公、通勤、包里常备这些场景都能接得住。{detail}",
        ],
        "summary_sentence": "{name}适合桌面办公和通勤场景。",
        "point_details": ["桌面用起来会更顺手", "包里常备更方便", "轻便一点更适合高频日常"],
        "summary_labels": ["通勤场景", "桌面顺手", "包里常备"],
    },
    "food_general": {
        "main_category": "food",
        "tone_tags": ["早餐友好", "下午茶", "口感舒服"],
        "title_patterns": [
            "{name}，最近早餐经常吃",
            "{name}，下午茶也很合适",
            "想找日常吃的，可以看看{name}",
            "{name}，很适合家里囤一点",
            "办公室也能备着的{name}",
        ],
        "selling_points": ["早餐下午茶都能搭", "口感更轻松", "家里办公室都能备一点", "配咖啡也合适", "解馋不会太有负担"],
        "hashtags": ["#食品分享", "#早餐推荐", "#下午茶", "#好物分享", "#家里囤一点", "#办公室备一点"],
        "suitable_for": "喜欢早餐和下午茶分享的人",
        "recommend_reason": "口感轻松，早餐下午茶都能搭，适合家里囤一点",
        "comments": ["你平时更喜欢早餐还是下午茶？", "这类食品你会囤吗？", "还想看哪些食品分享？"],
        "body_patterns": [
            "最近会吃到{name}，这种日常食品更适合放在早餐或下午茶场景里。搭咖啡、牛奶或者茶都比较自然，也适合家里和办公室备一点。{detail}",
            "{name}这种方向我会更想写成日常场景里的真实分享，不是夸张功能型，而是口感、搭配和囤货方便这些点更清楚。{detail}",
        ],
        "summary_sentence": "{name}适合早餐和下午茶场景。",
        "point_details": ["早餐或下午茶都合适", "口感和场景更容易写清楚", "家里或办公室都能备一点"],
        "summary_labels": ["适合场景", "推荐理由", "日常分享"],
    },
    "beauty_general": {
        "main_category": "beauty",
        "tone_tags": ["清爽感", "不厚重", "日常护理"],
        "title_patterns": [
            "{name}，最近通勤会带着",
            "{name}，肤感比想象中轻松",
            "日常护理里会留下{name}",
            "{name}，不厚重更适合日常",
            "{name}，属于会继续回购的类型",
        ],
        "selling_points": ["质地轻一点", "肤感更舒服", "随身带着没负担", "日常护理更顺手", "不厚重更日常"],
        "hashtags": ["#护肤分享", "#美妆好物", "#通勤好物", "#日常护理", "#真实测评", "#护肤日常"],
        "suitable_for": "喜欢日常护理和通勤好物的人",
        "recommend_reason": "质地舒服、肤感清爽、日常护理顺手",
        "comments": ["你更在意质地还是肤感？", "这类美妆护肤好物你会试吗？", "还想看哪些通勤护肤分享？"],
        "body_patterns": [
            "最近出门和通勤时会带着{name}，它更像日常护理里不太有负担的那一类。质地和肤感都会更重要一点，不想写得太像广告说明。{detail}",
            "如果你也想找一款更适合日常护理、又能随身带着的产品，这类思路会更稳。重点还是放在肤感、使用场景和会不会真的常拿出来用。{detail}",
        ],
        "summary_sentence": "{name}更适合日常护理场景。",
        "point_details": ["质地和肤感更容易说明白", "妆前补水或日常护理都能带到", "随身补用也不会太有负担"],
        "summary_labels": ["适合肤感", "推荐理由", "日常分享"],
    },
    "home_general": {
        "main_category": "home",
        "tone_tags": ["顺手用", "桌面整洁", "日常使用"],
        "title_patterns": [
            "{name}，比想象中更实用",
            "{name}，日常用着很顺手",
            "家里会反复用到的{name}",
            "{name}，放进日常更轻松",
            "{name}，适合实用派参考",
        ],
        "selling_points": ["顺手用更轻松", "桌面更整洁", "日常使用频率高", "收纳友好", "家里用着更省心"],
        "hashtags": ["#家居好物", "#生活好物", "#日用分享", "#桌面整洁", "#实用好物", "#真实分享"],
        "suitable_for": "喜欢实用家居和日用分享的人",
        "recommend_reason": "顺手、省心、能让日常更轻松一点",
        "comments": ["你更喜欢哪类日用好物？", "这类实用分享你会继续看吗？", "你家里最近缺什么顺手小物？"],
        "body_patterns": [
            "最近日常里会用到{name}，它属于那种不夸张，但真的会提高使用频率的小东西。更适合放进桌面、通勤或居家这些高频场景里去写。{detail}",
            "如果你也偏向实用派，这类不花哨但很稳定的家居日用更值得参考。重点还是看它解决了什么小麻烦，而不是空泛地说提升体验。{detail}",
        ],
        "summary_sentence": "{name}适合高频日常场景。",
        "point_details": ["日常使用频率会更高", "顺手一点会更省心", "更适合高频日常场景"],
        "summary_labels": ["适合空间", "推荐理由", "日常使用"],
    },
    "pet_general": {
        "main_category": "pet",
        "tone_tags": ["养宠日常", "常备", "省心"],
        "title_patterns": [
            "{name}，养宠日常会用到",
            "{name}，更适合日常常备",
            "{name}，属于省心型宠物用品",
            "家里有毛孩子可以看看{name}",
            "{name}，最近会继续备着",
        ],
        "selling_points": ["养宠日常更省心", "常备更自然", "拿取更顺手", "照顾场景更稳定", "适合日常囤一点"],
        "hashtags": ["#宠物用品", "#养宠分享", "#猫狗日常", "#真实分享", "#养宠好物", "#宠物日常"],
        "suitable_for": "关注宠物日常照顾的人",
        "recommend_reason": "省心、常备方便、适合日常照顾场景",
        "comments": ["你家毛孩子最近更需要哪类用品？", "这类养宠分享你会继续看吗？", "还想看哪些宠物日常好物？"],
        "body_patterns": [
            "最近养宠日常里会用到{name}，我更在意它是不是能稳定融入每天的照顾节奏。省心和常备方便，比花哨说法更重要。{detail}",
            "如果你也想找适合家里毛孩子的常备款，可以先从日常频率最高的场景看起。{detail}",
        ],
        "summary_sentence": "{name}适合养宠日常常备。",
        "point_details": ["日常照顾更省心", "常备起来会更自然", "更适合养宠高频场景"],
        "summary_labels": ["适合场景", "推荐理由", "日常常备"],
    },
    "general": {
        "main_category": "other",
        "tone_tags": ["真实分享", "日常好物", "轻松种草"],
        "title_patterns": [
            "{name}，最近经常会用到",
            "{name}，比想象中更顺手",
            "{name}，很适合日常分享",
            "{name}，属于轻松种草那类",
            "{name}，想认真分享一下",
        ],
        "selling_points": ["日常好用", "不挑使用场景", "适合轻分享", "顺手一点更自然", "用起来更轻松"],
        "hashtags": ["#好物分享", "#日常好物", "#真实体验", "#轻松种草", "#生活好物", "#种草笔记"],
        "suitable_for": "喜欢日常好物分享的人",
        "recommend_reason": "好用、顺手、能自然放进日常",
        "comments": ["你最在意哪一点？", "这类好物你会试试吗？", "还想看哪些日常分享？"],
        "body_patterns": [
            "最近会反复用到{name}，它不是特别复杂的东西，但确实很容易放进日常。比起空泛夸它，不如直接写清楚使用场景和顺手程度。{detail}",
            "如果你也在找更轻松、更自然的日常好物，这类方向会更稳。{detail}",
        ],
        "summary_sentence": "{name}适合轻松放进日常。",
        "point_details": ["更适合放进日常场景", "顺手一点更容易留下来", "适合直接做真实分享"],
        "summary_labels": ["适合场景", "推荐理由", "一眼看懂"],
    },
}


@dataclass(frozen=True)
class ProductProfile:
    main_category: str
    sub_category: str
    category_label: str
    keywords: tuple[str, ...]
    tone_tags: tuple[str, ...]


def _combined_text(product_name: str, category: str, description: str) -> str:
    return " ".join(part.strip() for part in [category, product_name, description] if part and part.strip())


def _detect_main_category(category: str, text: str) -> str:
    category_text = (category or "").strip()
    for main_category, label in MAIN_CATEGORY_LABELS.items():
        if category_text == label and main_category != "other":
            return main_category
    for alias, main_category in MAIN_CATEGORY_ALIASES.items():
        if alias in category_text:
            return main_category

    for sub_category, keywords in SUBCATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return SUBCATEGORY_COPY[sub_category]["main_category"]
    return "other"


def _detect_sub_category(main_category: str, text: str) -> tuple[str, tuple[str, ...]]:
    for sub_category in SUBCATEGORY_ORDER.get(main_category, []):
        matched = tuple(keyword for keyword in SUBCATEGORY_KEYWORDS.get(sub_category, []) if keyword in text)
        if matched:
            return sub_category, matched
    return GENERAL_SUBCATEGORY.get(main_category, "general"), ()


def detect_product_profile(product_name: str, category: str, description: str) -> ProductProfile:
    text = _combined_text(product_name, category, description)
    main_category = _detect_main_category(category, text)
    sub_category, matched = _detect_sub_category(main_category, text)
    copy_config = SUBCATEGORY_COPY[sub_category]
    return ProductProfile(
        main_category=main_category,
        sub_category=sub_category,
        category_label=MAIN_CATEGORY_LABELS[main_category],
        keywords=matched,
        tone_tags=tuple(copy_config.get("tone_tags", [])),
    )


def get_profile_copy(profile: ProductProfile) -> dict:
    return SUBCATEGORY_COPY[profile.sub_category]
