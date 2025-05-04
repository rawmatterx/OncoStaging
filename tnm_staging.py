# tnm_staging.py

def determine_tnm_stage(cancer_type: str, features: dict) -> dict:
    cancer_type = cancer_type.lower()

    if cancer_type == "gallbladder":
        return stage_gallbladder_cancer(features)
    elif cancer_type == "esophageal":
        return stage_esophageal_cancer(features)
    elif cancer_type == "breast":
        return stage_breast_cancer(features)
    elif cancer_type == "lung":
        return stage_lung_cancer(features)
    elif cancer_type == "colorectal":
        return stage_colorectal_cancer(features)
    elif cancer_type in ["head and neck", "oral cavity", "oropharynx"]:
        return stage_head_neck_cancer(features)
    else:
        return {"T": "Unknown", "N": "Unknown", "M": "Unknown", "Stage": "Not available"}


def stage_gallbladder_cancer(features):
    t_size = features.get("tumor_size_cm", 0)
    liver_invasion = features.get("liver_invasion", False)
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    if liver_invasion:
        T = "T3"
    elif t_size > 2:
        T = "T2"
    elif t_size > 0:
        T = "T1"
    else:
        T = "Tx"

    if nodes == 0:
        N = "N0"
    elif 1 <= nodes <= 3:
        N = "N1"
    else:
        N = "N2"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IVB"
    elif T == "T3" and N != "N0":
        Stage = "Stage IVA"
    elif T == "T3":
        Stage = "Stage IIIB"
    elif T == "T2" and N == "N0":
        Stage = "Stage II"
    elif T in ["T1", "T2"] and N != "N0":
        Stage = "Stage IIIA"
    elif T == "T1" and N == "N0":
        Stage = "Stage I"
    else:
        Stage = "Stage Unknown"

    return {"T": T, "N": N, "M": M, "Stage": Stage}


def stage_esophageal_cancer(features):
    t_depth = features.get("tumor_depth", "")
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    T = {
        "mucosa": "T1",
        "submucosa": "T1b",
        "muscularis": "T2",
        "adventitia": "T3",
        "adjacent structures": "T4"
    }.get(t_depth.lower(), "Tx")

    if nodes == 0:
        N = "N0"
    elif 1 <= nodes <= 2:
        N = "N1"
    elif 3 <= nodes <= 6:
        N = "N2"
    else:
        N = "N3"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IVB"
    elif T == "T4" or N == "N3":
        Stage = "Stage IVA"
    elif T in ["T2", "T3"] and N in ["N0", "N1"]:
        Stage = "Stage II"
    elif T == "T1" and N == "N0":
        Stage = "Stage I"
    else:
        Stage = "Stage III"

    return {"T": T, "N": N, "M": M, "Stage": Stage}


def stage_breast_cancer(features):
    size = features.get("tumor_size_cm", 0)
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    if size <= 2:
        T = "T1"
    elif size <= 5:
        T = "T2"
    else:
        T = "T3"

    if nodes == 0:
        N = "N0"
    elif nodes <= 3:
        N = "N1"
    elif nodes <= 9:
        N = "N2"
    else:
        N = "N3"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IV"
    elif T == "T1" and N == "N0":
        Stage = "Stage I"
    elif T in ["T1", "T2"] and N == "N1":
        Stage = "Stage II"
    elif T == "T3" or N in ["N2", "N3"]:
        Stage = "Stage III"
    else:
        Stage = "Stage Unknown"

    return {"T": T, "N": N, "M": M, "Stage": Stage}


def stage_lung_cancer(features):
    size = features.get("tumor_size_cm", 0)
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    if size <= 3:
        T = "T1"
    elif size <= 5:
        T = "T2"
    elif size <= 7:
        T = "T3"
    else:
        T = "T4"

    if nodes == 0:
        N = "N0"
    elif nodes <= 3:
        N = "N1"
    else:
        N = "N2"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IV"
    elif T == "T1" and N == "N0":
        Stage = "Stage I"
    elif T in ["T2", "T3"] and N in ["N0", "N1"]:
        Stage = "Stage II"
    elif T in ["T3", "T4"] or N == "N2":
        Stage = "Stage III"
    else:
        Stage = "Stage Unknown"

    return {"T": T, "N": N, "M": M, "Stage": Stage}


def stage_colorectal_cancer(features):
    depth = features.get("tumor_depth", "")
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    T = {
        "submucosa": "T1",
        "muscularis propria": "T2",
        "subserosa": "T3",
        "peritoneum/invasion": "T4"
    }.get(depth.lower(), "Tx")

    if nodes == 0:
        N = "N0"
    elif nodes <= 3:
        N = "N1"
    else:
        N = "N2"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IV"
    elif T in ["T1", "T2"] and N == "N0":
        Stage = "Stage I"
    elif T == "T3" and N == "N0":
        Stage = "Stage II"
    elif N in ["N1", "N2"]:
        Stage = "Stage III"
    else:
        Stage = "Stage Unknown"

    return {"T": T, "N": N, "M": M, "Stage": Stage}


def stage_head_neck_cancer(features):
    size = features.get("tumor_size_cm", 0)
    nodes = features.get("lymph_nodes_involved", 0)
    distant_mets = features.get("distant_metastasis", False)

    if size <= 2:
        T = "T1"
    elif size <= 4:
        T = "T2"
    else:
        T = "T3"

    if nodes == 0:
        N = "N0"
    elif nodes == 1:
        N = "N1"
    elif 2 <= nodes <= 3:
        N = "N2"
    else:
        N = "N3"

    M = "M1" if distant_mets else "M0"

    if M == "M1":
        Stage = "Stage IVC"
    elif T == "T1" and N == "N0":
        Stage = "Stage I"
    elif T in ["T1", "T2"] and N in ["N1", "N2"]:
        Stage = "Stage II–III"
    elif T == "T3" or N == "N3":
        Stage = "Stage IV"
    else:
        Stage = "Stage Unknown"

    return {"T": T, "N": N, "M": M, "Stage": Stage}
