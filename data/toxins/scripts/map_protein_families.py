import pandas as pd
import numpy as np
import re

def create_protein_family_mapping():
    """
    Creates a dictionary mapping specific protein families to categories,
    with combined three-finger toxins, conotoxins, and neurotoxins.
    """
    return {
        # Combined conotoxin groups
        'conotoxin': [
            r'conotoxin.*superfamily',
            r'conotoxin.*family',
            r'cono.*peptide'
        ],

        # Scorpion toxin groups
        'scorpion_ktx': [
            r'.*ktx.*subfamily',
            r'.*potassium channel inhibitor.*subfamily'
        ],
        'scorpion_long_toxin': [
            r'long.*scorpion toxin.*subfamily',
            r'long \([34] c-c\) scorpion toxin'
        ],
        'scorpion_short_toxin': [
            r'short.*scorpion toxin',
        ],

        # Combined three-finger toxin group
        'three_finger_toxin': [
            r'snake three-finger toxin.*subfamily'
        ],

        # Combined neurotoxin group
        'neurotoxin': [
            r'neurotoxin.*family',
            r'.*toxin.*subfamily'
        ],

        # Enzyme groups
        'phospholipase_a2': [
            r'phospholipase a2.*family'
        ],
        'phospholipase_other': [
            r'phospholipase [^a2].*family'
        ],
        'metalloproteinase': [
            r'.*metalloproteinase.*family'
        ],
        'peptidase': [
            r'peptidase.*family'
        ],

        # Peptide groups
        'antimicrobial_peptide': [
            r'.*antimicrobial peptide.*family',
            r'.*defensin.*family'
        ],
        'cationic_peptide': [
            r'cationic peptide.*family'
        ],
        'bradykinin_related': [
            r'bradykinin.*family'
        ],

        # Specialized toxin groups
        'scoloptoxin': [
            r'scoloptoxin.*family'
        ],
        'hainantoxin': [
            r'hainantoxin.*family'
        ],
        'teretoxin': [
            r'teretoxin.*superfamily'
        ],

        # Venom protein groups
        'venom_kunitz': [
            r'venom kunitz.*family'
        ],
        'venom_protein_other': [
            r'venom protein.*family'
        ],

        # Growth factors and hormones
        'growth_factors': [
            r'.*growth factor.*family',
            r'.*\b(egf|ngf|vegf)\b.*family'
        ],
        'hormone_related': [
            r'.*hormone.*family',
            r'insulin family',
            r'glucagon family'
        ],

        # Other specific groups
        'lectin_related': [
            r'.*lectin.*family',
            r'snaclec family'
        ],
        'crisp_related': [
            r'crisp family',
            r'crisp.*subfamily'
        ],
        'disintegrin': [
            r'disintegrin.*family'
        ],
        'mcd_related': [
            r'mcd family',
            r'mcd.*subfamily'
        ]
    }

def classify_protein_family(family_name, categories):
    """
    Classifies a protein family name into categories based on regex patterns.
    Returns np.nan instead of 'unknown' for unmatched cases.

    Parameters:
    family_name (str): Original protein family name
    categories (dict): Dictionary of category patterns

    Returns:
    str or np.nan: Category name or np.nan if no match found
    """
    if pd.isna(family_name):
        return pd.NA

    family_name = str(family_name).lower()

    for category, patterns in categories.items():
        if any(re.search(pattern.lower(), family_name) for pattern in patterns):
            return category

    return pd.NA

def map_protein_families(df, family_column):
    """
    Maps protein families in a DataFrame to categories.

    Parameters:
    df (pandas.DataFrame): DataFrame containing protein family information
    family_column (str): Name of the column containing protein family names

    Returns:
    pandas.DataFrame: Original DataFrame with new 'protein_category' column
    """
    # Create the mapping categories
    categories = create_protein_family_mapping()

    # Create new column with mapped categories
    df['protein_category'] = df[family_column].apply(
        lambda x: classify_protein_family(x, categories)
    )

    return df

# Example usage:
# df = pd.DataFrame({'protein_family': protein_families})
# df = map_protein_families(df, 'protein_family')