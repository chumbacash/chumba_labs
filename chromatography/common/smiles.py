from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors

RDLogger.DisableLog("rdApp.*")


def mol_from_smiles(smiles: str):
    s = smiles.strip()
    if not s or len(s) > 512:
        return None
    return Chem.MolFromSmiles(s)


def validate_smiles(smiles: str) -> bool:
    return mol_from_smiles(smiles) is not None


def analyte_descriptors(smiles: str) -> dict[str, float]:
    mol = mol_from_smiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles}")
    return {
        "logp": float(Descriptors.MolLogP(mol)),
        "tpsa": float(Descriptors.TPSA(mol)),
        "mw": float(Descriptors.MolWt(mol)),
        "hbd": float(Descriptors.NumHDonors(mol)),
        "hba": float(Descriptors.NumHAcceptors(mol)),
        "aromatic_rings": float(Descriptors.NumAromaticRings(mol)),
    }
