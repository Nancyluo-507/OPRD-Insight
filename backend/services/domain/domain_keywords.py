DOMAIN_KEYWORDS = {
    "有机合成/方法学": "organic synthesis methodology cyclization annulation coupling C-H activation functionalization asymmetric enantioselective stereoselective radical 有机合成 全合成 环化 偶联 不对称 手性 碳氢活化",
    "工艺化学/放大/连续流": "process development scale-up scalable manufacturing kilogram pilot-scale route continuous flow intermediate impurity yield crystallization 工艺开发 放大 中试 公斤级 连续流 路线 中间体 杂质 收率",
    "催化": "catalysis catalytic catalyst homogeneous heterogeneous hydrogenation oxidation reduction palladium photoredox photocatalysis electrocatalysis organocatalysis ligand 催化 催化剂 均相 多相 氢化 氧化 光催化 电催化 配体",
    "生物催化/酶工程": "biocatalysis biocatalytic enzyme enzymatic directed evolution mutant transaminase hydrolase lipase protein engineering biotransformation 生物催化 酶 酶工程 定向进化 突变 转氨酶 水解酶 蛋白质工程 生物转化",
    "分析化学/色谱质谱": "analytical chemistry detection determination chromatography HPLC LC-MS GC-MS mass spectrometry method validation extraction impurity profiling sensing 分析化学 检测 色谱 液相色谱 质谱 方法验证 萃取 杂质分析",
    "药物化学/医药": "medicinal chemistry drug discovery drug design inhibitor scaffold ligand targeting potent structure-activity SAR lead optimization 药物化学 药物发现 药物设计 抑制剂 骨架 配体 靶向 构效关系 先导化合物",
    "绿色化学/可持续": "green chemistry sustainable waste valorization ionic liquid biomass lignin renewable atom economy solvent-free aqueous recycling 绿色化学 可持续 废物 生物质 木质素 可再生 无溶剂 水相 回收",
    "材料/无机化学": "materials inorganic coordination complex metal-organic framework MOF crystal structure magnetic electronic semiconductor nanoparticle porous 材料 无机 配位 配合物 金属有机框架 晶体 磁性 半导体 纳米 多孔",
    "计算化学/AI/化学信息": "computational machine learning deep learning artificial intelligence prediction model neural network graph simulation molecular dynamics DFT cheminformatics retrosynthesis docking screening 计算化学 机器学习 深度学习 人工智能 预测 模型 化学信息学 逆合成 虚拟筛选",
    "电化学/能源": "electrochemistry electrochemical electrocatalysis electrode electrolyte battery lithium sodium energy storage CO2 reduction water splitting fuel cell electrosynthesis 电化学 电催化 电极 电解质 电池 储能 二氧化碳还原 水分解 燃料电池 电合成",
    "食品/农业化学": "food chemistry agricultural pesticide residue nutrition flavor antioxidant contaminant food safety 食品化学 农业 农药 残留 营养 抗氧化 污染物 食品安全",
}

JOURNAL_TO_DOMAIN = {
    "organic process": "工艺化学/放大/连续流",
    "organic letters": "有机合成/方法学",
    "journal of organic chemistry": "有机合成/方法学",
    "european journal of organic": "有机合成/方法学",
    "organic chemistry frontiers": "有机合成/方法学",
    "synthesis": "有机合成/方法学",
    "advanced synthesis": "催化",
    "acs catalysis": "催化",
    "chemcatchem": "催化",
    "catalysis science": "催化",
    "nature catalysis": "催化",
    "green synthesis and catalysis": "催化",
    "enzyme and microbial": "生物催化/酶工程",
    "biocatalysis": "生物催化/酶工程",
    "chembiochem": "生物催化/酶工程",
    "chemical biology": "生物催化/酶工程",
    "biotechnology": "生物催化/酶工程",
    "microbiology": "生物催化/酶工程",
    "biological chemistry": "生物催化/酶工程",
    "biochemistry": "生物催化/酶工程",
    "analytical chemistry": "分析化学/色谱质谱",
    "chromatography": "分析化学/色谱质谱",
    "analytical biochemistry": "分析化学/色谱质谱",
    "medicinal chemistry": "药物化学/医药",
    "green chemistry": "绿色化学/可持续",
    "sustainable": "绿色化学/可持续",
    "current research in green": "绿色化学/可持续",
    "materials": "材料/无机化学",
    "dalton": "材料/无机化学",
    "chemical information": "计算化学/AI/化学信息",
    "synthetic biology": "计算化学/AI/化学信息",
    "agricultural and food": "食品/农业化学",
}


def get_domain_list():
    return list(DOMAIN_KEYWORDS.keys())


def journal_to_domain(journal):
    j = (journal or "").lower()
    for key, dom in JOURNAL_TO_DOMAIN.items():
        if key in j:
            return dom
    return "综合"


def guess_domain_by_text(text):
    t = (text or "").lower()
    best, best_hit = "综合", 0
    for dom, words in DOMAIN_KEYWORDS.items():
        hit = sum(1 for w in words.split() if w and w.lower() in t)
        if hit > best_hit:
            best, best_hit = dom, hit
    return best


def get_paper_domain(journal, text=""):
    dom = journal_to_domain(journal)
    if dom == "综合" and text:
        dom = guess_domain_by_text(text)
    return dom


def domain_matches(paper_domain, wanted_domains):
    if not wanted_domains:
        return True
    for w in wanted_domains:
        wl = w.strip().lower()
        if wl and (wl in paper_domain.lower() or paper_domain.lower() in wl):
            return True
    return False
