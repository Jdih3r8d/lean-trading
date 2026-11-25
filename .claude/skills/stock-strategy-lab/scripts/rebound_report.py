"""Modo rebote: convierte el journal de un workflow (rebound_deep.js) en un informe Markdown legible y permanente.

usage: python3 rebound_report.py <journal.jsonl> <salida.md> [--title "Detalle de los agentes (25-nov-2026)"]

El journal está en ~/.claude/projects/<proyecto>/<sesión>/subagents/workflows/wf_*/journal.jsonl (el más reciente:
ls -td ~/.claude/projects/*/*/subagents/workflows/wf_* | head -1). Ordena las secciones así: mercado, tasas base,
analista y escéptico de cada acción, y juez. Si un agente se reanudó y aparece dos veces, se queda con el último
resultado. Las carpetas temporales que citen los agentes (scratchpad) desaparecen al cerrar la sesión: el informe es
lo que queda.
"""
import argparse
import json


def label_of(key):
    return key.replace('_', ' ').capitalize()


def render(value, depth=0):
    """Devuelve Markdown para un valor JSON: textos como párrafos, listas como viñetas y listas de objetos planos
    como tablas."""
    if value is None:
        return '—'
    if isinstance(value, bool):
        return 'sí' if value else 'no'
    if isinstance(value, float):
        return f'{value:.1%}' if -1 <= value <= 1 else f'{value:.4g}'   # probabilidades y rentabilidades en %
    if isinstance(value, (int, str)):
        return str(value)
    if isinstance(value, list):
        if not value:
            return '—'
        if all(isinstance(x, dict) and all(not isinstance(v, (dict, list)) for v in x.values()) for x in value):
            cols = list(dict.fromkeys(k for x in value for k in x))
            head = '| ' + ' | '.join(label_of(c) for c in cols) + ' |\n|' + '---|' * len(cols)
            rows = ['| ' + ' | '.join(render(x.get(c)).replace('\n', ' ').replace('|', '/') for c in cols) + ' |'
                    for x in value]
            return head + '\n' + '\n'.join(rows)
        return '\n'.join('- ' + render(x, depth + 1).replace('\n', '\n  ') for x in value)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            body = render(v, depth + 1)
            if '\n' in body or len(body) > 120:
                parts.append(f'**{label_of(k)}**\n\n{body}')
            else:
                parts.append(f'**{label_of(k)}:** {body}')
        return '\n\n'.join(parts)
    return str(value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('journal')
    ap.add_argument('out')
    ap.add_argument('--title', default='Detalle de los agentes')
    a = ap.parse_args()
    labels, results = {}, {}
    for line in open(a.journal, encoding='utf-8'):
        j = json.loads(line)
        if j.get('type') == 'started':
            labels[j['key']] = j.get('label') or j['key']
        elif j.get('type') == 'result':
            results[labels.get(j['key'], j['key'])] = j.get('result')   # el último gana (reanudaciones)
    order = ['mercado', 'tasas-base']
    tickers = list(dict.fromkeys(lab.split(':', 1)[1] for lab in results if lab.startswith('analista:')))
    for t in tickers:
        order += [f'analista:{t}', f'esceptico:{t}']
    order += ['juez']
    order += [lab for lab in results if lab not in order]
    titles = {'mercado': 'Contexto de mercado', 'tasas-base': 'Tasas base históricas', 'juez': 'Decisión del juez'}
    out = [f'# {a.title}', '',
           'Informe generado automáticamente con lo que devolvió cada agente, sin editar. Las probabilidades se '
           'muestran en %. Las rutas a carpetas temporales que citan los agentes ya no existen.', '']
    for lab in order:
        if lab not in results:
            if lab.startswith(('analista:', 'esceptico:')) or lab == 'juez':
                out += [f'## {lab}', '', '_Este agente no terminó._', '']
            continue
        if lab.startswith('analista:'):
            title = f'{lab.split(":", 1)[1]} · analista'
        elif lab.startswith('esceptico:'):
            title = f'{lab.split(":", 1)[1]} · escéptico'
        else:
            title = titles.get(lab, lab)
        out += [f'## {title}', '', render(results[lab]), '']
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'{a.out}: {len(results)} agentes')


if __name__ == '__main__':
    main()
