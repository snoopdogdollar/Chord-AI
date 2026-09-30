"""Checks without audio downloads, ML dependencies, or local training."""
import ast
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent


class NotebookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = json.loads((HERE / 'guitarset_kaggle_train.ipynb').read_text(encoding='utf-8'))
        tree = ast.parse((HERE / 'chord_cnn.py').read_text(encoding='utf-8'))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name in ('reduce_chord', 'group_id')]
        cls.namespace = {'re': re}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<pure helpers>', 'exec'), cls.namespace)

    def test_cells_compile_and_are_unexecuted(self):
        self.assertEqual(self.notebook['nbformat'], 4)
        ids = [c['id'] for c in self.notebook['cells']]
        self.assertEqual(len(ids), len(set(ids)))
        for i, cell in enumerate(self.notebook['cells']):
            if cell['cell_type'] == 'code':
                compile(''.join(cell['source']), f'<cell {i}>', 'exec')
                self.assertIsNone(cell['execution_count'])
                self.assertEqual(cell['outputs'], [])

    def test_exported_module_matches_local_inference(self):
        for cell in self.notebook['cells']:
            source = ''.join(cell['source'])
            if source.startswith('MODULE_SOURCE = '):
                embedded = ast.literal_eval(ast.parse(source).body[0].value)
                self.assertEqual(embedded, (HERE / 'chord_cnn.py').read_text(encoding='utf-8'))
                return
        self.fail('Missing inference module')

    def test_enharmonic_and_extension_policy(self):
        reduce = self.namespace['reduce_chord']
        self.assertEqual(reduce('Db:maj7'), reduce('C#:maj'))
        self.assertEqual(reduce('A:min7'), 21)
        self.assertEqual(reduce('C/3'), 0)
        self.assertEqual(reduce('B#:maj'), 0)
        self.assertEqual(reduce('G:7/b7'), 7)
        for label in ['N', 'X', 'C:dim', 'D:sus4', 'C:maj(*3)', 'bad', 'C:aug']:
            self.assertEqual(reduce(label), -1, label)

    def test_related_recordings_stay_in_same_group(self):
        group = self.namespace['group_id']
        related = ['00_BN1-129-Eb_comp', '00_BN1-129-Eb_solo', '05_BN1-170-C_comp']
        self.assertEqual({group(track) for track in related}, {'BN1'})
        self.assertNotEqual(group('00_BN2-129-Eb_comp'), 'BN1')
        with self.assertRaises(ValueError):
            group('unexpected.wav')


if __name__ == '__main__':
    unittest.main()
