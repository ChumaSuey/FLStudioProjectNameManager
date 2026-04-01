"""
FL Studio Project Name Manager
Core scanner module — scans directories for FL Studio projects (.flp)
and checks for rendered audio / MIDI files (mp3, wav, mid, ogg, flac…).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# Audio / MIDI extensions that indicate a project has been exported / finished
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aiff", ".aif", ".mid", ".midi"}
FL_PROJECT_EXT = ".flp"


@dataclass
class FLProject:
    """Represents a single FL Studio project folder."""
    folder_name: str
    folder_path: str
    flp_files: List[str] = field(default_factory=list)
    audio_files: List[str] = field(default_factory=list)

    @property
    def has_audio(self) -> bool:
        """True if the project folder contains rendered audio or MIDI files."""
        return len(self.audio_files) > 0

    @property
    def project_count(self) -> int:
        return len(self.flp_files)

    @property
    def status(self) -> str:
        if not self.flp_files:
            return "Empty"
        return "Named ✓" if self.has_audio else "Unnamed"

    @property
    def export_names(self) -> list:
        """Return the stem names of all exported audio/MIDI files."""
        return [Path(f).stem for f in self.audio_files]

    @property
    def primary_name(self) -> str:
        """Return the 'best' project name (first .flp without extension)."""
        if self.flp_files:
            return Path(self.flp_files[0]).stem
        return self.folder_name


def scan_directory(root_path: str, depth: int = 1) -> List[FLProject]:
    """
    Scan *root_path* for FL Studio project folders.

    Parameters
    ----------
    root_path : str
        The top-level directory to scan.
    depth : int
        How many directory levels deep to search (1 = immediate children only).

    Returns
    -------
    list[FLProject]
        A list of discovered project descriptors, sorted by folder name.
    """
    projects: List[FLProject] = []
    root = Path(root_path)

    if not root.is_dir():
        return projects

    if depth == 0:
        # Scan the root itself as a project
        project = _scan_single_folder(root)
        if project.flp_files:
            projects.append(project)
        return projects

    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            # Check this directory
            project = _scan_single_folder(entry)
            if project.flp_files:
                projects.append(project)
            # Recurse if depth allows
            elif depth > 1:
                projects.extend(scan_directory(str(entry), depth - 1))

    return projects


def scan_directory_recursive(root_path: str, max_depth: int = 5) -> List[FLProject]:
    """
    Recursively scan for FL Studio projects up to *max_depth* levels.
    Every folder containing at least one .flp file is reported.
    """
    projects: List[FLProject] = []
    root = Path(root_path)

    if not root.is_dir():
        return projects

    def _walk(current: Path, current_depth: int):
        if current_depth > max_depth:
            return
        project = _scan_single_folder(current)
        if project.flp_files:
            projects.append(project)
        try:
            for child in sorted(current.iterdir()):
                if child.is_dir():
                    _walk(child, current_depth + 1)
        except PermissionError:
            pass

    _walk(root, 0)
    return projects


def _scan_single_folder(folder: Path) -> FLProject:
    """Scan a single folder and collect .flp and audio files."""
    flp_files: List[str] = []
    audio_files: List[str] = []

    try:
        for item in folder.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                if ext == FL_PROJECT_EXT:
                    flp_files.append(item.name)
                elif ext in AUDIO_EXTENSIONS:
                    audio_files.append(item.name)
    except PermissionError:
        pass

    return FLProject(
        folder_name=folder.name,
        folder_path=str(folder),
        flp_files=sorted(flp_files),
        audio_files=sorted(audio_files),
    )
