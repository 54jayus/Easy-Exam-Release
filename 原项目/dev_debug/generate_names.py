import random
import pandas as pd
import os

def generate_chinese_names(count=817):
    # 常用姓氏
    family_names = (
        "李王张刘陈杨黄赵周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文"
    )
    # 常用名字字符
    given_names = (
        "伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘"
        "秀娟英华慧巧婷玉珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖露瑶怡婵雁蓓纨仪荷丹蓉眉君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希宁欣飘育滢馥筠柔竹霭凝晓欢霄枫芸菲寒伊亚宜可姬舒影荔枝思丽"
    )
    
    names = set()
    # 为了避免死循环（虽然概率极低），加个计数器
    attempts = 0
    while len(names) < count and attempts < count * 10:
        family = random.choice(family_names)
        # 名字可以是1个字或2个字
        # 考虑到现代人双字名较多，设定较高概率
        if random.random() < 0.9: 
            given = random.choice(given_names) + random.choice(given_names)
        else:
            given = random.choice(given_names)
        
        names.add(family + given)
        attempts += 1
    
    return list(names)

if __name__ == "__main__":
    count = 817
    names = generate_chinese_names(count)
    
    # 导出为 Excel
    df = pd.DataFrame(names, columns=["姓名"])
    
    # 也可以顺便生成一些模拟数据，方便用户直接测试考务系统
    # 比如加上班级、学号
    # 但用户只要求姓名，为了保持简单，只输出姓名，或者在另一列加个序号
    
    output_file = "817个中文姓名.xlsx"
    # 获取绝对路径
    output_path = os.path.join(os.getcwd(), output_file)
    
    try:
        df.to_excel(output_path, index=False)
        print(f"成功生成文件: {output_path}")
        print(f"共包含 {len(names)} 个不重复姓名")
    except Exception as e:
        print(f"生成Excel失败: {e}")
        # 备选：生成txt
        txt_path = output_path.replace(".xlsx", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            for name in names:
                f.write(name + "\n")
        print(f"已生成文本文件: {txt_path}")
