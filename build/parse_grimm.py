# -*- coding: utf-8 -*-
"""Parse 174 Grimm .docx -> data/stories.js (window.__GRIMM__)
Italian body paragraphs aligned to Chinese paragraphs by cumulative-length ratio.
"""
import zipfile, re, sys, os, json, glob
from xml.etree import ElementTree as ET

SRC = r"D:/BaiduNetdiskDownload/格林童话word档"
OUT = r"D:/workbuddy工作区/2026-08-23-21-28-02/grimm-fiabe"
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
CJK = re.compile(r'[\u3400-\u9fff]')


def docx_paras(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    out = []
    for pe in root.iter(W + 'p'):
        txt = ''.join(t.text or '' for t in pe.iter(W + 't'))
        if txt.strip():
            out.append(txt.strip())
    return out


def split_title(line):
    """Return (it_title, zh_title). First CJK char splits Latin / CJK."""
    m = None
    for i, ch in enumerate(line):
        if CJK.match(ch):
            m = i
            break
    if m is None:
        return line.strip(), ''
    it = line[:m].strip()
    zh = line[m:].strip()
    return it, zh


def is_zh(s):
    return bool(CJK.search(s))


def align(it_ps, zh_ps):
    """Map each IT paragraph to a contiguous chunk of ZH paragraphs by length ratio."""
    if not it_ps:
        return []
    if not zh_ps:
        return [{'it': x, 'zh': ''} for x in it_ps]
    it_lens = [len(x) for x in it_ps]
    zh_lens = [len(x) for x in zh_ps]
    total_it = sum(it_lens) or 1
    total_zh = sum(zh_lens) or 1
    zh_cum = []
    c = 0
    for l in zh_lens:
        c += l
        zh_cum.append(c)
    units = []
    zh_pos = 0
    it_cum = 0
    for i, il in enumerate(it_lens):
        it_cum += il
        target = it_cum * total_zh / total_it
        j = zh_pos
        while j < len(zh_lens) and zh_cum[j] < target:
            j += 1
        end = max(zh_pos, min(j, len(zh_lens) - 1))
        chunk = zh_ps[zh_pos:end + 1]
        units.append({'it': it_ps[i], 'zh': '\n'.join(chunk)})
        zh_pos = end + 1
    if zh_pos < len(zh_ps):
        tail = '\n'.join(zh_ps[zh_pos:])
        units[-1]['zh'] = (units[-1]['zh'] + '\n' + tail).strip()
    return units


# Stories whose docx has a Chinese-only title line -> supply literal Italian title.
TITLE_FIX = {
    '75': 'La volpe e il cavallo',
    '76': 'Il medico di tutto fare',
    '77': 'Il cibo di Dio',
    '78': 'Fratello Lustig',
    '79': 'Il re della Montagna d\'Oro',
    '80': 'I sette svevi',
    '81': 'I tre garzoni',
    '82': 'Il principe senza paura',
    '83': 'L\'erba magica',
    '84': 'La vecchia nel bosco',
    '85': 'La stufa di ferro',
    '107': 'La bella Catterina e Piff, Paff, Puff e Poltrino',
}


def main():
    files = sorted(glob.glob(os.path.join(SRC, '*.docx')))
    stories = []
    missing_it_title = []
    zero_it = []
    total_it_paras = 0
    for f in files:
        name = os.path.basename(f)
        m = re.match(r'^(\d+)\.', name)
        sid = m.group(1) if m else name
        ps = docx_paras(f)
        if not ps:
            print('SKIP empty:', name)
            continue
        it_title, zh_title = split_title(ps[0])
        if not it_title and sid in TITLE_FIX:
            it_title = TITLE_FIX[sid]
        body = ps[1:]
        it_body = [x for x in body if not is_zh(x)]
        zh_body = [x for x in body if is_zh(x)]
        if not it_body:
            zero_it.append(name)
        if not it_title:
            missing_it_title.append((sid, zh_title, name))
        units = align(it_body, zh_body)
        # assign para ids
        for idx, u in enumerate(units, 1):
            u['id'] = 'p%02d' % idx
            u['audio'] = 'audio/%s/p%02d.mp3' % (sid, idx)
        total_it_paras += len(units)
        stories.append({
            'id': sid,
            'title_it': it_title,
            'title_zh': zh_title,
            'paras': units,
        })

    meta = {
        'title_it': 'Fiabe di Grimm',
        'title_zh': '格林童话',
        'subtitle_it': 'Le fiabe dei fratelli Grimm',
        'subtitle_zh': '格林兄弟童话集 · 意中双语',
        'author': 'Fratelli Grimm',
        'lang': 'it-IT',
        'voice': 'it-IT-ElsaNeural',
        'story_count': len(stories),
        'para_count': total_it_paras,
    }
    data = {'meta': meta, 'stories': stories}
    out_path = os.path.join(OUT, 'data', 'stories.js')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('window.__GRIMM__ = ')
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write(';\n')
    print('STORIES:', len(stories))
    print('TOTAL IT PARAS (audio files):', total_it_paras)
    print('STORIES WITH ZH-ONLY TITLE:', len(missing_it_title))
    for sid, zh, fn in missing_it_title:
        print('   ', sid, '|', zh, '|', fn)
    print('STORIES WITH NO IT BODY:', len(zero_it))
    for fn in zero_it:
        print('   ', fn)
    # save a small manifest for audio jobs
    man = [{'id': s['id'], 'n': len(s['paras']),
            'paras': [{'pid': p['id'], 'text': p['it']} for p in s['paras']]}
           for s in stories]
    with open(os.path.join(OUT, 'build', 'audio_manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(man, fh, ensure_ascii=False)


if __name__ == '__main__':
    main()
