"""
:File: cut_video.py
:Description: Fonction utilitaire pour découper un extrait d'une vidéo.
:Inputs: 
    - input_path (str) : chemin de la vidéo source
    - output_path (str) : chemin de sortie pour la vidéo extraite
    - start_time (str) : temps de début au format "HH:MM:SS" ou en secondes ("3.5")
    - end_time (str) : temps de fin au format "HH:MM:SS" ou en secondes
:Outputs:
    - fichier vidéo découpé (format selon l'extension du output_path)
"""

import subprocess

def cut_video(input_path: str, output_path: str, start_time: str, end_time: str):
    """
    Découpe un extrait vidéo entre start_time et end_time.

    Args:
        input_path (str): chemin de la vidéo source.
        output_path (str): chemin où sauvegarder la vidéo extraite.
        start_time (str): temps de début ("3" ou "00:00:03").
        end_time (str): temps de fin ("8" ou "00:00:08").
    """

    command = [
        "ffmpeg",
        "-i", input_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",  # copie sans ré-encoder (rapide, pas de perte)
        output_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ Extrait sauvegardé dans {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la découpe: {e}")