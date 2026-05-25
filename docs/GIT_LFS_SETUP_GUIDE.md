# Git LFS Setup Guide

This guide explains when Git LFS is useful for ChessInsightAI and how the repository already hints at large-file handling.

## Relevant repository references

| File or folder | Status | Role |
| --- | --- | --- |
| [`../configure_git_lfs.sh`](../configure_git_lfs.sh) | Existing | Shell helper for Git LFS setup |
| [`../detect_large_files.sh`](../detect_large_files.sh) | Existing | Identifies files that may need different storage handling |
| [`../datasets/`](../datasets/) | Existing | Potential source of large raw inputs |
| [`../mlartifacts/`](../mlartifacts/) | Existing | Likely location for large generated artifacts |
| [`../notebooks/`](../notebooks/) | Existing | Can accumulate outputs worth excluding or externalizing |

## Theory

Git LFS is appropriate when files are too large or too binary-heavy for normal Git history, especially model artifacts, exported datasets, and large archives. It keeps repository history lighter while preserving version pointers.

## Practical guidance for this project

- Keep source code, configuration, and lightweight docs in normal Git.
- Evaluate large datasets, checkpoints, and generated artifacts for Git LFS or external storage.
- Use detection scripts before committing bulk data.

## Future plan

- Publish a formal list of tracked file extensions.
- Align volume strategy, artifact storage, and Git LFS usage.
- Document which large outputs should never be committed at all.
