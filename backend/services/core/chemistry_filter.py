import re

from services.models.paper import Paper


# ==========================================================
# Chemistry-Related Subjects (from OpenAlex concepts)
# ==========================================================

CHEMISTRY_SUBJECTS = {
    "catalysis", "catalyst", "catalytic",
    "chemistry", "chemical", "chemical engineering",
    "organic chemistry", "inorganic chemistry",
    "physical chemistry", "analytical chemistry",
    "biochemistry", "polymer chemistry",
    "materials science", "nanotechnology",
    "electrochemistry", "electrocatalysis",
    "photocatalysis", "photocatalytic",
    "biocatalysis", "biocatalyst",
    "organometallic", "coordination chemistry",
    "green chemistry", "environmental chemistry",
    "medicinal chemistry", "pharmaceutical chemistry",
    "computational chemistry", "theoretical chemistry",
    "surface science", "surface chemistry",
    "crystal engineering", "solid state chemistry",
    "polymer science", "polymer",
    "nanomaterial", "nanoparticle",
    "chemical kinetics", "thermodynamics",
    "spectroscopy", "chromatography",
    "electrochemical", "electrolysis",
    "fuel cell", "battery", "supercapacitor",
    "corrosion", "oxidation",
    "reduction", "hydrogen evolution",
    "oxygen evolution", "co2 reduction",
    "nitrogen reduction", "ammonia synthesis",
    "petrochemistry", "petrochemical",
    "photochemistry", "radiochemistry",
    "metallurgy", "metallurgical",
    "ceramic", "composite material",
    "adsorption", "absorption",
    "heterogeneous catalysis", "homogeneous catalysis",
    "enzymatic", "enzyme",
    "zeolite", "mof", "metal-organic framework",
    "covalent organic framework",
    "chemical biology", "chemical physics",
}

NON_CHEMISTRY_SUBJECTS = {
    "feminist studies", "women's studies", "gender studies",
    "sociology", "political science", "political sociology",
    "psychology", "clinical psychology", "social psychology",
    "economics", "business", "management", "marketing",
    "history", "philosophy", "literature", "linguistics",
    "art", "music", "theater",
    "law", "legal", "education", "anthropology",
    "archaeology", "geography",
    "communication", "journalism", "media studies",
    "library and information sciences",
    "nursing", "public health", "health policy",
    "social work", "criminology", "demography",
    "cultural studies", "ethnic studies",
    "theology", "religious studies",
    "international relations", "public administration",
    "urban studies", "development studies",
    "sports science", "family studies",
    "counseling", "social policy",
}


# ==========================================================
# Chemistry-Related Terms (for title/abstract matching)
# ==========================================================

CHEMISTRY_TERMS = {
    "catalyst", "catalysis", "catalytic", "catalyze", "catalyzed",
    "chemical", "chemistry",
    "synthesis", "synthetic", "synthesize", "synthesized",
    "reaction", "reactant", "reagent",
    "metal", "metallic", "metal-organic",
    "organic", "inorganic", "organometallic",
    "electrochemical", "electrocatalyst", "electrocatalysis",
    "polymer", "polymeric", "polymerization",
    "nanoparticle", "nanomaterial", "nanostructure", "nanoscale",
    "molecular", "atomic",
    "compound", "complex", "ligand", "chelate",
    "oxidation", "reduction", "redox",
    "hydrogen", "oxygen", "carbon", "nitrogen",
    "sulfur", "phosphorus", "silicon", "boron",
    "acid", "base", "alkali", "alkaline", "pH",
    "battery", "fuel cell", "electrolysis", "electrolyte",
    "photocatalyst", "photocatalytic", "photocatalysis",
    "biocatalyst", "biocatalysis", "enzymatic", "enzyme",
    "zeolite", "mof", "mofs",
    "spectroscopy", "chromatography", "diffraction",
    "molecule", "atom", "ion", "electron", "proton",
    "alloy", "bimetallic", "monometallic",
    "oxide", "sulfide", "nitride", "carbide",
    "adsorption", "desorption", "absorption",
    "thermodynamic", "thermodynamics", "kinetic", "kinetics",
    "mechanism", "pathway",
    "palladium", "platinum", "nickel", "cobalt",
    "iron", "copper", "ruthenium", "rhodium",
    "gold", "silver", "titanium", "zinc",
    "aluminum", "magnesium", "calcium", "lithium",
    "sodium", "potassium", "manganese", "chromium",
    "molybdenum", "tungsten", "vanadium", "iridium",
    "cerium", "lanthanum", "neodymium",
    "perovskite", "graphene", "carbon nanotube",
    "derivatization", "substitution", "addition",
    "condensation", "esterification", "hydrolysis",
    "precipitation", "crystallization",
    "electrode", "anode", "cathode",
    "copolymer", "monomer", "oligomer",
    "surfactant", "emulsion", "colloid",
    "titration", "calorimetry", "electrophoresis",
    "stoichiometry", "valence", "bonding",
    "orbital", "molecular dynamics",
    "density functional theory", "dft",
    "solvent", "solution", "aqueous",
    "concentration", "molar", "molality",
    "distillation", "extraction", "purification",
    "crystallography", "x-ray",
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def _count_chemistry_terms(
    text_normalized: str, query_words: set
) -> int:
    text_words = set(text_normalized.split())
    count = 0
    for term in CHEMISTRY_TERMS:
        term_normalized = _normalize(term)
        if term_normalized in query_words:
            continue
        if " " in term_normalized:
            if term_normalized in text_normalized:
                count += 1
        else:
            if term_normalized in text_words:
                count += 1
    return count


def is_chemistry_related(paper: Paper, query: str = "") -> bool:
    if paper.subjects:
        subject_lower = {s.lower().strip() for s in paper.subjects}
        has_chem = bool(subject_lower & CHEMISTRY_SUBJECTS)
        has_non_chem = bool(subject_lower & NON_CHEMISTRY_SUBJECTS)

        if has_non_chem and not has_chem:
            return False

        if has_chem and not has_non_chem:
            return True

        if has_chem and has_non_chem:
            return _check_content(paper, query)

    return _check_content(paper, query)


def _check_content(paper: Paper, query: str) -> bool:
    if not paper.title:
        return False

    query_words = set(_normalize(query).split())

    title_normalized = _normalize(paper.title)
    title_count = _count_chemistry_terms(title_normalized, query_words)
    if title_count >= 1:
        return True

    if not paper.abstract:
        return False

    abstract_normalized = _normalize(paper.abstract)
    abstract_count = _count_chemistry_terms(
        abstract_normalized, query_words
    )
    if abstract_count >= 2:
        return True

    return False