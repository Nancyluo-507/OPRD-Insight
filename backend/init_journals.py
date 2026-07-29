"""
导入全部期刊到数据库（从 RSS 源列表 + xlsx 数据）
保留原有的 subscription.json 配置兼容
"""
from database.database import SessionLocal, init_db
from database.models import Journal


JOURNALS = [
    # === ACS (15 journals) ===
    ("Organic Process Research & Development", "OPRD", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=oprdfk"),
    ("Journal of the American Chemical Society", "JACS", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jacsat"),
    ("Organic Letters", "OL", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=orlef7"),
    ("The Journal of Organic Chemistry", "JOC", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=joceah"),
    ("Analytical Chemistry", "AnalChem", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=ancham"),
    ("ACS Central Science", "ACSCentSci", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acscii"),
    ("Journal of Chemical Information and Modeling", "JCIM", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jcisd8"),
    ("Chemistry of Materials", "ChemMater", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=cmatex"),
    ("ACS Chemical Biology", "ACSChemBio", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acbcct"),
    ("ACS Omega", "ACSOmega", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=acsodf"),
    ("ACS Sustainable Chemistry & Engineering", "ACSSusChem", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=ascecg"),
    ("ACS Synthetic Biology", "ACSSynBio", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=asbcd6"),
    ("Biochemistry", "Biochem", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=bichaw"),
    ("Journal of Agriculture and Food Chemistry", "JAFC", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jafcau"),
    ("ACS Catalysis", "ACSCatal", "ACS", "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=accacs"),

    # === RSC (11 journals) ===
    ("Green Chemistry", "GreenChem", "RSC", "https://feeds.rsc.org/rss/gc"),
    ("Chemical Communications", "ChemCommun", "RSC", "https://feeds.rsc.org/rss/cc"),
    ("Chemical Science", "ChemSci", "RSC", "https://feeds.rsc.org/rss/sc"),
    ("Chemical Society Reviews", "ChemSocRev", "RSC", "https://feeds.rsc.org/rss/cs"),
    ("Organic & Biomolecular Chemistry", "OBC", "RSC", "https://feeds.rsc.org/rss/ob"),
    ("New Journal of Chemistry", "NJC", "RSC", "https://feeds.rsc.org/rss/nj"),
    ("Catalysis Science & Technology", "CatalSciTech", "RSC", "https://feeds.rsc.org/rss/cy"),
    ("Organic Chemistry Frontiers", "OrgChemFront", "RSC", "https://feeds.rsc.org/rss/qo"),
    ("RSC Advances", "RSCAdv", "RSC", "https://feeds.rsc.org/rss/ra"),
    ("RSC Chemical Biology", "RSCChemBio", "RSC", "https://feeds.rsc.org/rss/cb"),
    ("Dalton Transactions", "Dalton", "RSC", "https://feeds.rsc.org/rss/dt"),

    # === Nature (7 journals) ===
    ("Nature", "Nature", "Nature", "https://www.nature.com/nature.rss"),
    ("Nature Catalysis", "NatCatal", "Nature", "https://www.nature.com/natcatal.rss"),
    ("Nature Communications", "NatCommun", "Nature", "https://www.nature.com/ncomms.rss"),
    ("Nature Chemistry", "NatChem", "Nature", "https://www.nature.com/nchem.rss"),
    ("Nature Biotechnology", "NatBiotech", "Nature", "https://www.nature.com/nbt.rss"),
    ("Nature Cell Biology", "NatCellBio", "Nature", "https://www.nature.com/ncb.rss"),
    ("Nature Chemical Biology", "NatChemBio", "Nature", "https://www.nature.com/nchembio.rss"),

    # === AAAS / Science (6 journals) ===
    ("Science", "Science", "AAAS", "https://science.org/action/showFeed?type=axatoc&feed=rss&jc=science"),
    ("Science Advances", "SciAdv", "AAAS", "https://science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv"),
    ("Science Robotics", "SciRobot", "AAAS", "https://science.org/action/showFeed?type=etoc&feed=rss&jc=scirobotics"),
    ("Science Immunology", "SciImmunol", "AAAS", "https://science.org/action/showFeed?type=etoc&feed=rss&jc=sciimmunol"),
    ("Science Translational Medicine", "SciTranslMed", "AAAS", "https://science.org/action/showFeed?type=etoc&feed=rss&jc=stm"),
    ("Science Signaling", "SciSignal", "AAAS", "https://science.org/action/showFeed?type=etoc&feed=rss&jc=signaling"),

    # === Wiley (9 journals) ===
    ("Angewandte Chemie International Edition", "AngewChem", "Wiley", "https://onlinelibrary.wiley.com/feed/15213773/most-recent"),
    ("Advanced Synthesis & Catalysis", "AdvSynthCatal", "Wiley", "https://advanced.onlinelibrary.wiley.com/feed/16154169/most-recent"),
    ("Chemistry - A European Journal", "ChemEurJ", "Wiley", "https://chemistry-europe.onlinelibrary.wiley.com/feed/15213765/most-recent"),
    ("Chemistry - An Asian Journal", "ChemAsianJ", "Wiley", "https://aces.onlinelibrary.wiley.com/feed/1861471x/most-recent"),
    ("European Journal of Organic Chemistry", "EurJOC", "Wiley", "https://chemistry-europe.onlinelibrary.wiley.com/feed/10990690/most-recent"),
    ("Chirality", "Chirality", "Wiley", "https://onlinelibrary.wiley.com/feed/1520636x/most-recent"),
    ("ChemCatChem", "ChemCatChem", "Wiley", "https://chemistry-europe.onlinelibrary.wiley.com/feed/18673899/most-recent"),
    ("ChemBioChem", "ChemBioChem", "Wiley", "https://chemistry-europe.onlinelibrary.wiley.com/feed/14397633/most-recent"),
    ("Journal of Chemical Technology & Biotechnology", "JChemTechBiotech", "Wiley", "https://scijournals.onlinelibrary.wiley.com/feed/10974660/most-recent"),

    # === Elsevier / ScienceDirect (10 journals) ===
    ("Journal of Chromatography A", "JCA", "Elsevier", "https://rss.sciencedirect.com/publication/science/00219673"),
    ("Current Research in Green and Sustainable Chemistry", "CRGSC", "Elsevier", "https://rss.sciencedirect.com/publication/science/26660865"),
    ("Current Opinion in Chemical Biology", "COChemBio", "Elsevier", "https://rss.sciencedirect.com/publication/science/13675931"),
    ("Green Synthesis and Catalysis", "GreenSynthCatal", "Elsevier", "https://rss.sciencedirect.com/publication/science/26665549"),
    ("Bioorganic & Medicinal Chemistry", "BMC", "Elsevier", "https://rss.sciencedirect.com/publication/science/09680896"),
    ("Enzyme and Microbial Technology", "EnzMicrobTech", "Elsevier", "https://rss.sciencedirect.com/publication/science/01410229"),
    ("Trends in Biotechnology", "TrendsBiotech", "Elsevier", "https://rss.sciencedirect.com/publication/science/01677799"),
    ("Analytical Biochemistry", "AnalBiochem", "Elsevier", "https://rss.sciencedirect.com/publication/science/00032697"),
    ("Biocatalysis and Agricultural Biotechnology", "BiocatAgriBiotech", "Elsevier", "https://rss.sciencedirect.com/publication/science/18788181"),
    ("Journal of Biological Chemistry", "JBC", "Elsevier", "https://rss.sciencedirect.com/publication/science/00219258"),

    # === Springer ===
    ("Applied Microbiology and Biotechnology", "ApplMicrobBiotech", "Springer",
     "https://link.springer.com/search.rss?query=&search-within=Journal&facet-journal-id=253"),

    # === arXiv (via export.arxiv.org API, Atom XML) ===
    ("arXiv cs.CL - Computation and Language", "cs.CL", "arXiv", "https://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=50"),
    ("arXiv cs.CV - Computer Vision", "cs.CV", "arXiv", "https://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results=50"),
    ("arXiv cs.LG - Machine Learning", "cs.LG", "arXiv", "https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=50"),
    ("arXiv cs.NE - Neural and Evolutionary Computing", "cs.NE", "arXiv", "https://export.arxiv.org/api/query?search_query=cat:cs.NE&sortBy=submittedDate&sortOrder=descending&max_results=50"),
    ("arXiv stat.ML - Machine Learning", "stat.ML", "arXiv", "https://export.arxiv.org/api/query?search_query=cat:stat.ML&sortBy=submittedDate&sortOrder=descending&max_results=50"),
]


def import_journals():
    db = SessionLocal()
    try:
        existing = {j.title: j for j in db.query(Journal).all()}
        added = 0
        for title, short, publisher, rss_url in JOURNALS:
            if title in existing:
                continue
            journal = Journal(
                title=title,
                short_name=short,
                publisher=publisher,
                rss_url=rss_url,
                rss_type=publisher,
                is_active=True,
            )
            db.add(journal)
            added += 1
        db.commit()
        print(f"新增 {added} 本期刊，共 {db.query(Journal).count()} 本")
    finally:
        db.close()


def list_journals():
    db = SessionLocal()
    try:
        journals = db.query(Journal).order_by(Journal.publisher, Journal.title).all()
        print(f"\n共 {len(journals)} 本期刊：")
        print("=" * 80)
        for j in journals:
            print(f"[{j.publisher}] {j.title} ({j.short_name})")
            if j.rss_url:
                print(f"  RSS: {j.rss_url}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    import_journals()
    list_journals()
