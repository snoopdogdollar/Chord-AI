"""Create a Kaggle-safe copy without changing the original GuitarSet archives."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

SOURCES = {
    'annotation.zip': ('annotations', '.jams', 'b39b78e63d3446f2e54ddb7a54df9b10'),
    'audio_mono-mic.zip': ('audio', '.wav', '275966d6610ac34999b58426beb119c3'),
}


def build(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f'Will not overwrite {output}')
    mappings, ids = {}, {}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as result:
        for name, (folder, suffix, expected) in SOURCES.items():
            original = source / name
            with original.open('rb') as f:
                assert hashlib.file_digest(f, 'md5').hexdigest() == expected, f'Wrong source checksum: {name}'
            tracks = set()
            with zipfile.ZipFile(original) as archive:
                for info in archive.infolist():
                    path = Path(info.filename)
                    if info.is_dir() or '__MACOSX' in path.parts or path.name.startswith('._') or path.suffix != suffix:
                        continue
                    safe = path.name.replace('#', 'sharp')
                    track = Path(safe).stem.removesuffix('_mic')
                    assert track not in tracks, f'Duplicate track: {track}'
                    tracks.add(track)
                    destination = folder + '/' + safe
                    with archive.open(info) as src, result.open(destination, 'w', force_zip64=True) as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    mappings[destination] = {'original': info.filename, 'crc32': info.CRC, 'size': info.file_size}
            assert len(tracks) == 360, (name, len(tracks))
            ids[folder] = tracks
            print(f'{name}: copied {len(tracks)} files', flush=True)
        assert ids['annotations'] == ids['audio'], 'Audio and annotation IDs differ'
        result.writestr('filename_mapping.json', json.dumps(mappings, indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None, 'ZIP integrity failure'
        assert all('#' not in name for name in archive.namelist())
        for name, original in mappings.items():
            copied = archive.getinfo(name)
            assert (copied.CRC, copied.file_size) == (original['crc32'], original['size'])
    print(f'Verified 360 matching pairs; file contents unchanged. Output: {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
