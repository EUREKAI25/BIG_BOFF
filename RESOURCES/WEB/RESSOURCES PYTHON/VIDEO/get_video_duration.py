"""
:File: get_video_duration.py
:Description: Fonction utilitaire pour obtenir la durée d'une vidéo.
:Inputs:
    - input_path (str) : chemin de la vidéo
:Outputs:
    - float : durée en secondes
"""

import subprocess
import json

def get_video_duration(input_path: str) -> float:
    """
    Retourne la durée d'une vidéo (en secondes).

    Args:
        input_path (str): chemin de la vidéo

    Returns:
        float: durée en secondes
    """
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        input_path
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la durée: {e}")
        return -1.0